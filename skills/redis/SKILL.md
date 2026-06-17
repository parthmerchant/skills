---
name: redis
description: Redis fundamentals with emphasis on caching (SET/EX/NX, cache-aside, eviction, TTL, stampede) and Streams (XADD, consumer groups, XACK/XCLAIM, trimming), plus redis-cli and troubleshooting. Use when designing a cache, building an event stream or queue with Redis Streams, debugging memory/latency/eviction, or driving Redis from the terminal.
---

# Redis

App-agnostic fundamentals, biased toward caching and Streams. Read the reference that matches your task.

## References
- `references/cli.md` — redis-cli: connect/auth/TLS, one-shot vs interactive, SCAN vs KEYS, MONITOR, INFO, pipelining, `--eval` Lua, CONFIG, key inspection
- `references/caching.md` — SET EX/PX/NX, GETEX, cache-aside vs write-through, TTL, eviction policies, key naming, stampede protection, invalidation, INCR, hashes, locks
- `references/streams.md` — XADD, XRANGE, XREAD blocking, consumer groups, XACK/XPENDING/XCLAIM/XAUTOCLAIM, trimming, at-least-once, DLQ, vs pub/sub & lists
- `references/troubleshooting.md` — memory/OOM, eviction, slowlog, latency monitor, big/hot keys, keyspace notifications, RDB/AOF, connection limits, blocked clients

## TL;DR
- A cache value with **no TTL is a memory leak** — set `EX`/`PX` on writes, and pick a `maxmemory-policy` (usually `allkeys-lru`) so Redis evicts under pressure.
- `SET k v NX EX 30` is the atomic primitive for cache-aside fills and naive locks; `GETEX k EX 60` reads and refreshes TTL in one round trip.
- **Never run `KEYS *` in production** — it blocks the single thread; use `SCAN`/`--scan` with a cursor instead.
- Streams (`XADD` + consumer groups) give **at-least-once, replayable, acknowledged** delivery — unlike pub/sub (fire-and-forget) or lists (no acks, no fan-out).
- Trim streams aggressively: `XADD s MAXLEN ~ 100000 * ...` (the `~` makes trimming cheap) or by ID with `MINID`.
- Unacked stream messages sit in the **PEL** — monitor with `XPENDING`, recover crashed consumers with `XAUTOCLAIM`, and route poison messages (high delivery count) to a dead-letter stream.
- For correctness, prefer atomic single commands (`INCR`, `SET NX`) or Lua/`MULTI` over read-modify-write; for real distributed locks use **Redlock**, not a bare `SETNX`.
- Diagnose with `INFO`, `SLOWLOG GET`, `redis-cli --latency`, and `redis-cli --bigkeys` / `MEMORY USAGE key` before guessing.

## Docs
- Redis docs home — https://redis.io/docs/latest/
- Command reference — https://redis.io/commands/
- Caching at scale (key eviction) — https://redis.io/docs/latest/operate/oss_and_stack/management/config/
- Streams intro — https://redis.io/docs/latest/develop/data-types/streams/
