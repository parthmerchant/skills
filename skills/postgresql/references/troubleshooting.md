## Connection refused / can't reach server

```
psql: error: could not connect to server: Connection refused
  Is the server running on host "localhost" and accepting TCP/IP connections on port 5432?
```

- Is Postgres running? `pg_isready -h localhost -p 5432` (macOS/brew: `brew services list`; systemd: `sudo systemctl status postgresql`).
- Wrong host/port? Check with `\conninfo` or `echo $PGHOST $PGPORT`.
- Server only listening on the socket? Confirm `listen_addresses = '*'` (or the host) in `postgresql.conf`, then reload: `SELECT pg_reload_conf();`.

---

## Authentication failures (password / pg_hba)

```
FATAL: password authentication failed for user "app"
FATAL: no pg_hba.conf entry for host "10.0.0.5", user "app", database "app", no encryption
```

- The second error means **`pg_hba.conf` has no matching rule** — not a bad password. Locate it: `SHOW hba_file;`.
- Add a line (most specific first) and reload (`SELECT pg_reload_conf();` — no restart needed):

```
# TYPE  DATABASE  USER  ADDRESS         METHOD
host    app       app   10.0.0.0/24     scram-sha-256
```

- `scram-sha-256` is the modern method; `md5` is legacy; `trust` (no password) should never be used on a network.
- Store passwords in `~/.pgpass` (`chmod 600`) to stop retyping. Docs: https://www.postgresql.org/docs/current/auth-pg-hba-conf.html.

---

## SSL errors

```
FATAL: connection requires a valid client certificate
psql: error: SSL error: certificate verify failed
```

- Force or relax TLS via `sslmode` in the URL: `?sslmode=require` (encrypt, no cert check) … `verify-full` (encrypt + verify hostname).
- Self-signed server cert: `sslmode=require` connects without verifying the CA. For `verify-full`, point `sslrootcert=/path/to/ca.crt`.
- Cloud providers (RDS, Cloud SQL, Supabase) usually require `sslmode=require` or stricter. Docs: https://www.postgresql.org/docs/current/libpq-ssl.html.

---

## "Too many connections"

```
FATAL: sorry, too many clients already
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

```sql
-- How many, by state and source
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
SELECT count(*), usename, application_name FROM pg_stat_activity GROUP BY 2,3 ORDER BY 1 DESC;

SHOW max_connections;
```

- Usually the app is leaking connections or running without pooling. Put **PgBouncer** (or your framework's pool) in front; raise `max_connections` only as a stopgap.
- Kill idle leftovers (see kill section below); filter on `state = 'idle'` and old `state_change`.

---

## Slow queries

```sql
-- Currently long-running
SELECT pid, now() - query_start AS runtime, left(query, 100)
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 s'
ORDER BY runtime DESC;

-- See the plan
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

- Enable `pg_stat_statements` to find the worst aggregate offenders over time:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT left(query,60), calls, mean_exec_time, total_exec_time
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
```

- Log anything slow: set `log_min_duration_statement = 500` (ms) in `postgresql.conf`.
- `Seq Scan` on a big table → add an index; row estimates way off → `ANALYZE`.
Docs: https://www.postgresql.org/docs/current/pgstatstatements.html.

---

## Lock contention

```sql
-- Who is blocking whom
SELECT blocked.pid  AS blocked_pid,  left(blocked.query, 60)  AS blocked_query,
       blocking.pid AS blocking_pid, left(blocking.query, 60) AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

- Common cause: a transaction left open (`idle in transaction`) holding a row/table lock. Find them: `WHERE state = 'idle in transaction'`.
- Mitigate future cases with `SET lock_timeout = '5s'` and `idle_in_transaction_session_timeout`.
- Cancel the *blocking* session (see below) or fix the app to commit promptly.

---

## Sequence / serial / "duplicate key" after import

After a bulk load with explicit IDs, the sequence behind a `serial`/`identity` column falls behind, so the next insert collides:

```
ERROR: duplicate key value violates unique constraint "users_pkey"
```

```sql
-- Find the sequence and reset it past the current max
SELECT pg_get_serial_sequence('users', 'id');

SELECT setval(
  pg_get_serial_sequence('users','id'),
  (SELECT max(id) FROM users)
);
```

Prefer `GENERATED ALWAYS AS IDENTITY` over `serial` in new schemas. Docs: https://www.postgresql.org/docs/current/functions-sequence.html.

---

## Encoding / collation

```
ERROR: invalid byte sequence for encoding "UTF8"
ERROR: new encoding (UTF8) is incompatible with the encoding of the target database (SQL_ASCII)
```

```sql
SHOW server_encoding;
SHOW client_encoding;
\encoding UTF8            -- set client encoding for this session
```

- Importing latin1 data into a UTF8 db? Convert first: `iconv -f LATIN1 -t UTF-8 in.csv > out.csv`.
- A database's encoding is fixed at `CREATE DATABASE` time — to change it you must dump, recreate with the right `ENCODING`/`LC_COLLATE`, and reload.

---

## Find & kill queries

```sql
-- Cancel a single statement (gentle — lets the txn continue)
SELECT pg_cancel_backend(<pid>);

-- Terminate the whole backend/connection (forceful)
SELECT pg_terminate_backend(<pid>);

-- Kill all idle-in-transaction sessions older than 10 min
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '10 minutes'
  AND pid <> pg_backend_pid();         -- never kill yourself
```

Try `pg_cancel_backend` first; reach for `pg_terminate_backend` only when cancel doesn't free the lock. Docs: https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-SIGNAL.

---

## Docs
- Server admin manual — https://www.postgresql.org/docs/current/admin.html
- `pg_hba.conf` — https://www.postgresql.org/docs/current/auth-pg-hba-conf.html
- libpq SSL — https://www.postgresql.org/docs/current/libpq-ssl.html
- pg_stat_statements — https://www.postgresql.org/docs/current/pgstatstatements.html
- Admin/signal functions — https://www.postgresql.org/docs/current/functions-admin.html
- Sequence functions — https://www.postgresql.org/docs/current/functions-sequence.html
