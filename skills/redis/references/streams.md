## What a Stream is

An append-only log of entries, each with an auto-generated ID `<ms>-<seq>` and a set of field/value pairs. Supports replay, blocking reads, and consumer groups with acknowledgements — the closest thing Redis has to Kafka.

---

## XADD — append entries

```text
# * = let Redis assign the ID (monotonically increasing)
XADD events * type signup user 42 plan pro
# => "1718600000000-0"

# Explicit ID (must be greater than the last) — rarely needed
XADD events 1718600000000-1 type login user 42

# Add WITH trimming in the same call (recommended for bounded streams)
XADD events MAXLEN ~ 100000 * type click url /home
```

---

## Length and inspection

```text
XLEN events                          # number of entries
XINFO STREAM events                  # length, first/last IDs, groups, etc.
XINFO STREAM events FULL             # entries + per-group/consumer detail
XINFO GROUPS events                  # consumer groups + their lag/pending
XINFO CONSUMERS events grp           # per-consumer pending + idle time
```

---

## XRANGE / XREVRANGE — read by ID range

```text
XRANGE events - +                    # all entries (oldest -> newest); - = min, + = max
XRANGE events - + COUNT 10           # first 10
XREVRANGE events + - COUNT 1         # the single newest entry
XRANGE events 1718600000000 +        # from a timestamp onward (IDs sort by time)

# Paginate: take last seen ID, use ( for exclusive start
XRANGE events (1718600000000-0 + COUNT 100
```

---

## XREAD — read new entries, optionally blocking

```text
# Read entries with ID greater than the given one
XREAD COUNT 10 STREAMS events 0           # 0 = from the very beginning
XREAD STREAMS events $                    # $ = only entries arriving AFTER this call

# Blocking consumer (tail -f style): wait up to 5000ms for new data; 0 = block forever
XREAD BLOCK 5000 STREAMS events $

# Multiple streams in one call
XREAD BLOCK 0 STREAMS orders payments $ $
```

`XREAD` is fan-out: every reader sees every message and there are no acks. For load-balanced, acknowledged work, use consumer groups.

---

## Consumer groups — load balancing + at-least-once

A group tracks a last-delivered ID and a **Pending Entries List (PEL)** of delivered-but-unacked messages. Each entry goes to exactly one consumer in the group, and stays pending until `XACK`.

```text
# Create the group. $ = start from new messages; 0 = replay all history.
# MKSTREAM creates the stream if it doesn't exist yet.
XGROUP CREATE events workers $ MKSTREAM

# Consumer "c1" claims new messages (> = never-delivered entries)
XREADGROUP GROUP workers c1 COUNT 10 BLOCK 5000 STREAMS events >

# ... process ... then acknowledge so it leaves the PEL
XACK events workers 1718600000000-0

# Re-read THIS consumer's own pending (unacked) backlog after a restart: use an ID, not >
XREADGROUP GROUP workers c1 COUNT 10 STREAMS events 0

XGROUP CREATECONSUMER events workers c2
XGROUP DELCONSUMER events workers c1     # returns count of pending it still owned
XGROUP SETID events workers 0            # rewind the group to replay
```

---

## XPENDING — inspect unacked work

```text
XPENDING events workers                                  # summary: count, min/max ID, per-consumer
XPENDING events workers - + 10                           # detail: up to 10 pending entries
XPENDING events workers IDLE 60000 - + 10 c1             # only entries idle > 60s for consumer c1
```

The summary's per-consumer counts tell you if one consumer is stuck holding messages it never acked (likely crashed).

---

## XCLAIM / XAUTOCLAIM — recover from dead consumers

If a consumer dies, its pending messages stay in the PEL forever. Another consumer must claim them.

```text
# Manually claim entries idle > 60000ms, reassigning ownership to c2
XCLAIM events workers c2 60000 1718600000000-0 1718600000000-3

# XAUTOCLAIM scans the PEL and claims eligible entries for you (preferred, since Redis 6.2)
# Returns [next-cursor, [claimed entries], [deleted ids]]; loop until cursor is 0-0.
XAUTOCLAIM events workers c2 60000 0
XAUTOCLAIM events workers c2 60000 0 COUNT 50
```

Each claim/delivery increments the entry's delivery counter — use it for dead-lettering (below).

---

## Trimming — keep streams bounded

Streams grow forever unless trimmed. Trim by count (`MAXLEN`) or by ID/age (`MINID`). The `~` (approximate) form lets Redis trim in efficient whole-node chunks and is much cheaper than exact `=`.

```text
XADD events MAXLEN ~ 100000 * field val   # cap length on every write (recommended)
XTRIM events MAXLEN ~ 100000              # trim out-of-band to ~100k entries
XTRIM events MAXLEN = 100000              # exact (more work)
XTRIM events MINID ~ 1718600000000        # drop entries older than a timestamp (time-based retention)
XDEL events 1718600000000-0               # delete a specific entry (leaves a tombstone gap)
```

Trimming a stream does NOT remove entries from a group's PEL — already-delivered, unacked messages can be trimmed away; handle the "claimed entry no longer exists" case in consumers.

---

## At-least-once delivery and dead-letter handling

Streams give **at-least-once**: a consumer may crash after processing but before `XACK`, so the message is redelivered. Therefore **make processing idempotent**.

Dead-letter a "poison" message that keeps failing (high delivery count):

```text
# 1. Find chronically-redelivered entries (4th field = delivery count)
XPENDING events workers - + 50
# 2. Claim it, copy to a DLQ stream, then ACK the original so it stops cycling
XCLAIM events workers dlq-handler 0 1718600000000-7
XADD events:dead * orig 1718600000000-7 reason max_retries
XACK events workers 1718600000000-7
```

There's no built-in DLQ — you implement it with a delivery-count threshold + a separate stream.

---

## Streams vs Pub/Sub vs Lists

| | Streams | Pub/Sub | Lists (LPUSH/BRPOP) |
|---|---|---|---|
| Persistence | Yes (stored, replayable) | No — dropped if no subscriber | Yes (until popped) |
| Acknowledgement | Yes (PEL + XACK) | No | No |
| Fan-out to N readers | Yes (groups + plain reads) | Yes | No (one popper per item) |
| Load-balance across workers | Yes (consumer groups) | No | Yes (competing BRPOP) |
| Redelivery / recovery | Yes (XCLAIM/XAUTOCLAIM) | No | No (lost on crash mid-process) |
| History / replay | Yes | No | No |

Use **Streams** for durable event logs and reliable work queues; **pub/sub** for ephemeral broadcast (presence, live notifications) where loss is acceptable; **lists** for simple FIFO queues where at-most-once and no replay is fine.

---

## Docs
- Streams data type & tutorial — https://redis.io/docs/latest/develop/data-types/streams/
- XADD — https://redis.io/commands/xadd/
- XREADGROUP — https://redis.io/commands/xreadgroup/
- XPENDING — https://redis.io/commands/xpending/
- XAUTOCLAIM — https://redis.io/commands/xautoclaim/
- XTRIM — https://redis.io/commands/xtrim/
- Pub/Sub (for comparison) — https://redis.io/docs/latest/develop/interact/pubsub/
