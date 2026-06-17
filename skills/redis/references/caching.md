## SET with expiry and conditions

`SET` is the workhorse. Combine expiry and conditional flags so writes are atomic and always bounded.

```text
SET key val EX 300        # expire in 300 seconds
SET key val PX 500        # expire in 500 milliseconds
SET key val NX            # only set if key does NOT exist (insert / lock acquire)
SET key val XX            # only set if key already exists (update only)
SET key val NX EX 300     # atomic "create-with-TTL" — the cache-fill primitive
SET key val KEEPTTL       # overwrite value but keep existing TTL
SET key val GET           # set new value, return the old one (atomic swap)
```

Rule of thumb: **every cache key gets a TTL.** A value with no expiry and no eviction policy is an unbounded memory leak.

---

## GETEX — read and refresh TTL together

```text
GETEX key EX 600          # return value AND reset TTL to 600s (sliding expiration)
GETEX key PERSIST         # return value and remove its TTL
GETDEL key                # return value and delete it (one-shot tokens)
```

`GETEX … EX` implements a sliding-window cache (hot keys stay alive, cold keys expire) in a single round trip.

---

## Cache-aside (lazy loading) — the default pattern

App checks cache, falls back to the DB on a miss, then populates the cache.

```text
# pseudo-flow
val = GET user:42
if val == nil:
    val = db.query(42)
    SET user:42 <val> EX 300 NX   # NX avoids clobbering a concurrent fill
return val
```

- Simple, resilient (cache down ≠ data lost), only caches what's actually read.
- Downside: first read after expiry is always a miss; risk of stampede (see below).

---

## Write-through / write-behind

```text
# Write-through: update DB and cache in the same logical write
db.save(42, val)
SET user:42 <val> EX 300

# Write-behind (write-back): write cache now, flush to DB asynchronously (e.g. via a stream)
SET user:42 <val> EX 300
XADD writeback:users * id 42 payload <val>
```

Write-through keeps the cache warm and consistent on writes but adds write latency. Write-behind is fast but risks data loss if Redis dies before the flush — only for tolerant workloads.

---

## TTL / expiration semantics

```text
EXPIRE key 300            # set/replace TTL (seconds)
PEXPIRE key 300000        # milliseconds
EXPIREAT key 1893456000   # expire at absolute Unix time
TTL key                   # -1 = persistent, -2 = missing
PERSIST key               # remove TTL
```

Redis expires keys two ways: **lazily** (on access) and via a background **active** sampler. A key past its TTL may still occupy memory until one of those fires — don't assume instant reclamation.

---

## Eviction policies (maxmemory-policy)

When `maxmemory` is reached, Redis evicts per policy. Set both, or writes will start failing with OOM under `noeviction`.

```bash
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

| Policy | Evicts |
|---|---|
| `noeviction` | nothing — writes error with OOM (default; **wrong for a pure cache**) |
| `allkeys-lru` | least-recently-used across all keys (good general cache default) |
| `allkeys-lfu` | least-frequently-used (better when access skew is stable) |
| `allkeys-random` | random key |
| `volatile-lru` / `volatile-lfu` / `volatile-random` | same, but only among keys **with a TTL** |
| `volatile-ttl` | key with the shortest remaining TTL |

For a cache, use `allkeys-lru` or `allkeys-lfu`. Use `volatile-*` only when Redis also stores persistent, non-cache data that must never be evicted.

---

## Key naming conventions

```text
user:42:profile          # colon-delimited namespaces (entity:id:field)
cache:v3:product:99      # include a version segment so you can bump-invalidate everything
session:{token}          # {hashtag} forces same cluster slot for related keys (MGET, MULTI)
feed:user:42:page:0
```

- Use a consistent prefix per concern (`cache:`, `session:`, `lock:`) so `--scan` and eviction reasoning are easy.
- Embed a schema version; to invalidate all caches at once, bump the version in code rather than scanning/deleting.

---

## Atomic counters and object caching

```text
INCR pageviews:home          # atomic +1 (creates at 0); INCRBY for steps
DECR stock:sku:9
INCRBYFLOAT price:9 1.50
EXPIRE pageviews:home 86400  # bound counters too

# Hashes for object caching — update one field without re-serializing the whole object
HSET user:42 name Ada email ada@x.io plan pro
HGET user:42 plan
HGETALL user:42
HINCRBY user:42 logins 1
EXPIRE user:42 600           # NOTE: TTL is per-key, not per-field
```

Atomic ops (`INCR`, `HINCRBY`) avoid the classic read-modify-write race that plagues `GET`+`SET` from concurrent clients.

---

## Thundering herd / cache stampede

When a hot key expires, many requests miss simultaneously and all hammer the DB.

Mitigations:
- **Lock-on-miss:** `SET lock:user:42 token NX EX 5` — only the lock winner recomputes; others briefly back off and re-read.
- **Probabilistic early expiration:** refresh a key slightly *before* its TTL with random jitter so all keys don't expire at once.
- **Stale-while-revalidate:** store value + a logical "soft expiry"; serve stale and refresh in the background.
- **TTL jitter:** add randomness to TTLs (`EX 300 + rand(0..60)`) so bulk-loaded keys don't expire in lockstep.

```text
# Lock-on-miss sketch
if SET lock:user:42 $token NX EX 5 == OK:
    val = db.query(42); SET user:42 $val EX 300; <delete lock with the safe Lua unlock>
else:
    sleep(20ms); val = GET user:42   # retry the read
```

---

## Cache invalidation

```text
DEL user:42                  # blocking delete
UNLINK user:42               # non-blocking delete (reclaims memory in background) — prefer for big values
DEL user:42 user:43 user:44  # batch

# Pattern invalidation — SCAN, never KEYS, in prod
redis-cli --scan --pattern 'cache:v3:product:*' | xargs -L 100 redis-cli UNLINK
```

Prefer **versioned keys** (bump `cache:v3:` → `cache:v4:`) over scan-and-delete for mass invalidation — it's O(1) and avoids a server-wide scan.

---

## Locks — SETNX and why Redlock for distributed

```text
# Single-instance lock: acquire with NX + TTL (the TTL prevents a crashed holder from deadlocking)
SET lock:job:7 $unique_token NX EX 30

# Release MUST be atomic compare-and-delete (Lua) — never a bare DEL,
# or you may delete a lock another client acquired after yours expired:
#   if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end
```

A bare `SETNX` lock on a single node is only safe-ish for non-critical mutual exclusion. For correctness across failover/replication, use the **Redlock** algorithm (acquire a majority of N independent masters) — and even then, only with a fencing token if the protected resource can't tolerate double execution.

---

## Docs
- SET (EX/PX/NX/XX/KEEPTTL) — https://redis.io/commands/set/
- GETEX — https://redis.io/commands/getex/
- Key eviction & maxmemory-policy — https://redis.io/docs/latest/develop/reference/eviction/
- EXPIRE & key expiration — https://redis.io/commands/expire/
- INCR — https://redis.io/commands/incr/
- Distributed locks / Redlock — https://redis.io/docs/latest/develop/use/patterns/distributed-locks/
- Client-side caching patterns — https://redis.io/docs/latest/develop/use/patterns/
