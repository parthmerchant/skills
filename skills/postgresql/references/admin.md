## Meta-commands (psql + pgcli)

Both clients support these backslash commands. Add `+` for more detail (sizes, descriptions), e.g. `\dt+`.

```sql
\l            -- list databases (\l+ adds size)
\dn           -- list schemas
\dt           -- list tables in current schema
\dt schema.*  -- tables in a specific schema
\dv           -- views      \dm  materialized views     \di  indexes
\ds           -- sequences
\d table      -- describe a table: columns, types, indexes, FKs, triggers
\d+ table     -- + storage, stats target, comments
\du           -- list roles/users and their attributes
\df           -- list functions      \df+ adds source
\df schema.*  -- functions in a schema
\dp / \z      -- table access privileges (GRANTs)
\x            -- toggle expanded output (vertical) — pair with wide \d output
\c dbname     -- connect to another database
\conninfo     -- show current connection details
\h CREATE INDEX  -- SQL syntax help
```

---

## Create databases, roles, users

```sql
-- Roles. A "user" is just a role WITH LOGIN.
CREATE ROLE app_owner LOGIN PASSWORD 'secret';
CREATE ROLE readonly NOLOGIN;             -- a group role to GRANT into

CREATE DATABASE app OWNER app_owner ENCODING 'UTF8' TEMPLATE template0;

-- Alter attributes later
ALTER ROLE app_owner WITH CREATEDB;
ALTER ROLE app_owner PASSWORD 'newsecret';
```

From the shell (libpq wrappers):

```bash
createuser --interactive --pwprompt app_owner
createdb -O app_owner app
```

See https://www.postgresql.org/docs/current/sql-createrole.html.

---

## Permissions (GRANT / REVOKE)

```sql
-- Database & schema access
GRANT CONNECT ON DATABASE app TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;

-- Read-only on all current tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Make it apply to FUTURE tables too (run as the table owner)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO readonly;

-- Read/write app role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_owner;

-- Put a user into a group role
GRANT readonly TO some_user;

REVOKE INSERT ON users FROM some_user;
```

Inspect grants with `\dp tablename`. Reference: https://www.postgresql.org/docs/current/sql-grant.html.

---

## EXPLAIN / EXPLAIN ANALYZE

`EXPLAIN` shows the plan; `EXPLAIN ANALYZE` actually **runs** the query and reports real row counts and timings (don't ANALYZE a destructive statement outside a transaction you'll roll back).

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 42;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 42 ORDER BY created_at DESC LIMIT 10;
```

Reading it:
- **Seq Scan** on a large table in a selective query → missing/unused index.
- **Rows estimated vs actual** far apart → stale stats; run `ANALYZE`.
- **Nested Loop** with huge inner row counts → consider a different index or a hash join.
- Paste plans into https://explain.dalibo.com/ for a visual breakdown.

Docs: https://www.postgresql.org/docs/current/using-explain.html.

---

## Indexes

```sql
-- btree (default) — equality & range, ORDER BY
CREATE INDEX idx_orders_user ON orders (user_id);
CREATE INDEX idx_orders_user_created ON orders (user_id, created_at DESC);

-- Unique
CREATE UNIQUE INDEX idx_users_email ON users (lower(email));

-- Partial — index only the rows you query
CREATE INDEX idx_orders_open ON orders (user_id) WHERE status = 'open';

-- GIN — JSONB, arrays, full-text
CREATE INDEX idx_users_data ON users USING gin (data);
CREATE INDEX idx_posts_tags ON posts USING gin (tags);

-- Build without locking writes (slower; runs outside a txn)
CREATE INDEX CONCURRENTLY idx_orders_total ON orders (total);

\di+              -- list indexes with sizes
DROP INDEX idx_old;
```

Rule of thumb: btree for scalars/ranges, GIN for containment (`@>`, `?`, `ANY`) and `tsvector`. https://www.postgresql.org/docs/current/indexes-types.html.

---

## VACUUM / ANALYZE

`VACUUM` reclaims space from dead rows; `ANALYZE` refreshes planner statistics. Autovacuum handles this automatically, but you can force it.

```sql
ANALYZE users;                 -- refresh stats only (fast)
VACUUM users;                  -- reclaim dead tuples
VACUUM (ANALYZE, VERBOSE) users;
VACUUM FULL users;             -- rewrites table, reclaims to OS — takes ACCESS EXCLUSIVE lock

-- Check bloat / last (auto)vacuum
SELECT relname, n_dead_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

Avoid `VACUUM FULL` on live tables — it locks the table. Docs: https://www.postgresql.org/docs/current/routine-vacuuming.html.

---

## Inspect activity & locks

```sql
-- Who's connected and what they're running
SELECT pid, usename, datname, state, wait_event_type,
       now() - query_start AS runtime, left(query, 80) AS query
FROM pg_stat_activity
WHERE state <> 'idle'
ORDER BY runtime DESC;

-- Blocked vs blocking sessions
SELECT blocked.pid AS blocked_pid, blocked.query AS blocked_query,
       blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));

-- Raw lock view
SELECT locktype, relation::regclass, mode, granted, pid FROM pg_locks;
```

`pg_stat_activity`: https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW.

---

## Schema introspection

```sql
-- Table & index sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS total
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;

-- Columns of a table (portable, via information_schema)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Foreign keys
SELECT conname, conrelid::regclass AS tbl, confrelid::regclass AS refs
FROM pg_constraint WHERE contype = 'f';

-- Current version & settings
SELECT version();
SHOW max_connections;
```

`information_schema` is the SQL-standard, portable route; `pg_catalog` exposes Postgres-specific detail. Docs: https://www.postgresql.org/docs/current/information-schema.html.

---

## Docs
- psql meta-commands — https://www.postgresql.org/docs/current/app-psql.html
- `GRANT` — https://www.postgresql.org/docs/current/sql-grant.html
- `CREATE ROLE` — https://www.postgresql.org/docs/current/sql-createrole.html
- Using EXPLAIN — https://www.postgresql.org/docs/current/using-explain.html
- Index types — https://www.postgresql.org/docs/current/indexes-types.html
- Routine vacuuming — https://www.postgresql.org/docs/current/routine-vacuuming.html
- Monitoring (pg_stat_activity) — https://www.postgresql.org/docs/current/monitoring-stats.html
