## Connecting — host, port, auth, TLS, db select

```bash
# Default localhost:6379
redis-cli

# Remote host + port + ACL user/password
redis-cli -h cache.example.com -p 6380 --user app --pass "$REDIS_PASSWORD"

# Legacy single-password (requirepass) auth
redis-cli -h cache.example.com -a "$REDIS_PASSWORD"   # add --no-auth-warning to silence the warning

# Connection URI (scheme, auth, db all in one)
redis-cli -u "redis://app:$REDIS_PASSWORD@cache.example.com:6380/2"

# TLS (rediss://) — common on managed Redis (ElastiCache in-transit, Redis Cloud)
redis-cli -h cache.example.com -p 6380 --tls \
  --cacert ca.pem --cert client.crt --key client.key

# Select a logical DB (0-15 by default); or use the /N suffix in a URI
redis-cli -n 3
```

Inside an interactive session: `SELECT 3` to switch DB, `AUTH user pass` to authenticate late, `PING` to test (`PONG`).

---

## Interactive vs one-shot

```bash
# One-shot: run a single command and exit (great for scripts/pipes)
redis-cli SET session:42 active EX 300
redis-cli GET session:42
redis-cli -n 1 DBSIZE

# Interactive REPL
redis-cli
127.0.0.1:6379> SET foo bar
OK
127.0.0.1:6379> GET foo
"bar"

# Pretty-print / raw output (raw strips quotes — good for binary/pipes)
redis-cli --no-raw GET foo    # show quotes/escapes
redis-cli --raw GET foo       # raw bytes
```

---

## SCAN vs KEYS — never block the server

`KEYS pattern` scans the entire keyspace in one blocking O(N) call — it can freeze a busy server. `SCAN` is cursor-based and incremental.

```text
# DON'T (production): KEYS user:*
# DO: iterate with a cursor (returns [cursor, [keys...]])
SCAN 0 MATCH user:* COUNT 100
SCAN 7136 MATCH user:* COUNT 100   # feed the returned cursor back until it returns 0

# Type-specific scans for collections
HSCAN user:42 0 MATCH addr:*
SSCAN tags:post:9 0
ZSCAN leaderboard 0
```

```bash
# redis-cli wraps SCAN in a flag that iterates for you
redis-cli --scan --pattern 'user:*'
redis-cli --scan --pattern 'cache:*' | head

# Bulk-delete matched keys safely (UNLINK is non-blocking; DEL is blocking)
redis-cli --scan --pattern 'tmp:*' | xargs -L 100 redis-cli UNLINK
```

---

## MONITOR — live command stream (debug only)

```bash
# Stream every command the server processes. High overhead — never leave running in prod.
redis-cli MONITOR

# Filter for a key pattern
redis-cli MONITOR | grep --line-buffered 'session:'
```

---

## INFO — server state at a glance

```bash
redis-cli INFO                 # everything
redis-cli INFO memory          # used_memory, maxmemory, fragmentation
redis-cli INFO stats           # ops/sec, hits/misses, evicted/expired keys
redis-cli INFO keyspace        # per-db key counts + keys with TTL
redis-cli INFO replication
redis-cli INFO clients         # connected_clients, blocked_clients

# Compute cache hit rate
redis-cli INFO stats | grep keyspace_
# keyspace_hits / (keyspace_hits + keyspace_misses)
```

---

## Pipelining — batch commands, one round trip

```bash
# Feed commands from a file or heredoc; --pipe uses the fast bulk protocol
redis-cli --pipe < commands.txt

cat <<'EOF' | redis-cli --pipe
SET a 1
SET b 2
INCR counter
EOF

# Ad-hoc batching without --pipe (still one connection)
printf 'SET x 1\nSET y 2\n' | redis-cli
```

Pipelining removes per-command round-trip latency — essential when loading thousands of keys.

---

## --eval — run Lua scripts atomically

Scripts run atomically on the single thread. Args before the comma-separated `,` are KEYS, after are ARGV.

```bash
# inline: KEYS[1]=lock, ARGV[1]=token, ARGV[2]=ttl
redis-cli --eval check_and_set.lua lock:job , token123 30

# Example check_and_set.lua (atomic compare-and-delete, the safe unlock pattern)
# if redis.call('GET', KEYS[1]) == ARGV[1] then
#   return redis.call('DEL', KEYS[1])
# else return 0 end
```

```text
# Or load once and call by SHA to save bandwidth
SCRIPT LOAD "return redis.call('INCR', KEYS[1])"
EVALSHA <sha> 1 counter
```

---

## CONFIG GET / SET — runtime tuning

```bash
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET maxmemory-policy
redis-cli CONFIG GET 'max*'              # glob match

# Set at runtime (does NOT persist across restart unless you rewrite the config)
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG REWRITE                 # persist running config to redis.conf
```

---

## Inspecting a key — type, TTL, encoding, size

```text
TYPE user:42                 # string | list | set | zset | hash | stream
TTL user:42                  # seconds left; -1 = no expiry, -2 = key missing
PTTL user:42                 # milliseconds
EXPIRE user:42 300           # set TTL; PERSIST removes it
OBJECT ENCODING user:42      # e.g. embstr, int, ziplist/listpack, hashtable, skiplist
OBJECT IDLETIME user:42      # seconds since last access (LRU debugging)
OBJECT FREQ user:42          # access frequency (only when maxmemory-policy is LFU)
MEMORY USAGE user:42         # approx bytes incl. overhead
DEBUG OBJECT user:42         # low-level details (serializedlength, etc.)
```

`OBJECT ENCODING` reveals whether small collections still use the compact `listpack`/`intset` representation vs a promoted `hashtable`/`skiplist` — useful for memory tuning.

---

## Docs
- redis-cli guide — https://redis.io/docs/latest/develop/tools/cli/
- SCAN — https://redis.io/commands/scan/
- INFO — https://redis.io/commands/info/
- EVAL / Lua scripting — https://redis.io/docs/latest/develop/interact/programmability/eval-intro/
- CONFIG SET — https://redis.io/commands/config-set/
- OBJECT ENCODING — https://redis.io/commands/object-encoding/
