## Memory: maxmemory, OOM, eviction

```bash
redis-cli INFO memory | grep -E 'used_memory:|used_memory_human|maxmemory_human|maxmemory_policy|mem_fragmentation_ratio'
```

- `OOM command not allowed when used memory > 'maxmemory'` means you hit the cap under `noeviction`. Either raise `maxmemory`, set an eviction policy, or add TTLs.
- `mem_fragmentation_ratio` well above 1 (e.g. > 1.5) = fragmentation; enable `activedefrag yes` or restart during a window.
- Check eviction is actually working:

```bash
redis-cli INFO stats | grep -E 'evicted_keys|expired_keys'
redis-cli CONFIG GET maxmemory-policy   # 'noeviction' is the silent killer for caches
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

See `references/caching.md` for the policy table.

---

## Latency: slowlog, latency monitor

```text
# Slowlog: commands exceeding slowlog-log-slower-than microseconds
CONFIG SET slowlog-log-slower-than 10000   # log commands > 10ms
SLOWLOG GET 10                             # last 10 slow entries (id, ts, micros, args)
SLOWLOG LEN
SLOWLOG RESET

# Latency monitor: tracks spikes by event (expire-cycle, fork, command, ...)
CONFIG SET latency-monitor-threshold 100   # ms
LATENCY LATEST
LATENCY HISTORY command
LATENCY RESET
LATENCY DOCTOR                             # human-readable analysis
```

```bash
# Measure round-trip latency continuously / sampled
redis-cli --latency
redis-cli --latency-history -i 5
redis-cli --intrinsic-latency 5            # measures the host's own scheduling latency
```

Common culprits: `KEYS`/large `SCAN COUNT`, big `SMEMBERS`/`HGETALL`/`LRANGE 0 -1`, synchronous `DEL` of huge keys (use `UNLINK`), and fork stalls during RDB/AOF rewrite.

---

## Big keys and hot keys

```bash
# Big keys: largest key per type (samples the keyspace, safe-ish)
redis-cli --bigkeys
redis-cli --memkeys                # by memory rather than element count

# Exact memory of one key
redis-cli MEMORY USAGE somekey

# Hot keys: requires maxmemory-policy to be an LFU policy
redis-cli CONFIG SET maxmemory-policy allkeys-lfu
redis-cli --hotkeys
```

Big collections turn O(N) commands into latency spikes. Split them (shard a giant hash into `obj:{id}:part:N`) or page reads (`HSCAN`, `XRANGE COUNT`). Hot keys overload one CPU/slot in Cluster — add local client-side caching or replicas for reads.

---

## Keyspace notifications

Redis can publish events when keys change/expire — useful for cache-invalidation fan-out and expiry-driven workflows.

```text
CONFIG SET notify-keyspace-events KEA       # K=keyspace, E=keyevent, A=all event classes
# e.g. Ex = expired-key events only
CONFIG SET notify-keyspace-events Ex
```

```bash
# Subscribe to expirations across db 0
redis-cli PSUBSCRIBE '__keyevent@0__:expired'
# Watch all events on a key pattern
redis-cli PSUBSCRIBE '__keyspace@0__:user:*'
```

Caveats: notifications are pub/sub (fire-and-forget — missed if no subscriber), and `expired` events fire when the key is *actually* removed (lazy or active expiry), not exactly at TTL.

---

## Persistence: RDB and AOF gotchas

```bash
redis-cli INFO persistence | grep -E 'rdb_last_bgsave_status|aof_enabled|aof_last_bgrewrite_status|aof_last_write_status|loading:'
redis-cli BGSAVE          # async snapshot
redis-cli BGREWRITEAOF    # compact the AOF
redis-cli LASTSAVE        # unix ts of last successful save
```

- **RDB** = point-in-time snapshots; fast restart, but you can lose everything since the last save on crash. The fork to write the snapshot can stall on large datasets / low memory (watch for `Cannot allocate memory` / overcommit).
- **AOF** = append every write; lower data loss (`appendfsync everysec` is the usual balance) but larger files and slower restart. A truncated AOF after an unclean shutdown may need `redis-check-aof --fix`.
- Set `stop-writes-on-bgsave-error yes` (default) means writes are rejected if a background save fails — alarming but intentional; fix the disk/permission and it recovers.
- For a pure cache you may legitimately disable persistence entirely (`save ""`, `appendonly no`).

---

## Connection limits and blocked clients

```bash
redis-cli INFO clients
# connected_clients, blocked_clients (in BLPOP/XREAD BLOCK/WAIT), maxclients
redis-cli CONFIG GET maxclients
redis-cli CLIENT LIST                       # per-connection age, idle, cmd, addr
redis-cli CLIENT LIST TYPE normal | wc -l
redis-cli CLIENT NO-EVICT on                # protect a connection
redis-cli CLIENT KILL ID 123                # drop a misbehaving client
```

- `ERR max number of clients reached`: raise `maxclients`, but first check the OS `ulimit -n` (file descriptors) — Redis caps `maxclients` to fd budget minus reserve.
- High `blocked_clients` is normal for stream/list consumers; a *growing* count with no throughput suggests stuck consumers — cross-check `XINFO GROUPS` / `XPENDING`.
- Connection storms usually mean a missing client-side connection pool, not a Redis bug.

---

## First-response triage checklist

```bash
redis-cli PING
redis-cli INFO server | grep -E 'redis_version|uptime_in_seconds'
redis-cli INFO stats | grep -E 'instantaneous_ops_per_sec|keyspace_hits|keyspace_misses|rejected_connections'
redis-cli INFO memory | grep -E 'used_memory_human|maxmemory_human|maxmemory_policy'
redis-cli SLOWLOG GET 5
redis-cli --latency
redis-cli --bigkeys
```

---

## Docs
- Memory optimization — https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/
- Latency troubleshooting — https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/
- SLOWLOG — https://redis.io/commands/slowlog-get/
- Keyspace notifications — https://redis.io/docs/latest/develop/use/keyspace-notifications/
- Persistence (RDB/AOF) — https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- Diagnosing latency issues — https://redis.io/docs/latest/develop/reference/clients/ (clients) and https://redis.io/commands/client-list/
