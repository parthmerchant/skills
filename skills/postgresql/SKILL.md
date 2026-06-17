---
name: postgresql
description: Interacting with PostgreSQL from the terminal via pgcli — connecting, everyday SQL, admin/introspection meta-commands, and troubleshooting. Use when running queries, connecting to a Postgres database with pgcli or psql, writing SELECT/INSERT/UPDATE/JOIN/JSONB/CTE/window SQL, inspecting schemas with \d/\dt/\l, tuning with EXPLAIN ANALYZE, granting roles, or debugging connection/lock/"too many connections" errors.
---

# PostgreSQL via pgcli

App-agnostic fundamentals for working with PostgreSQL from the command line. The primary client here is **pgcli** (https://www.pgcli.com/) — psql-compatible with autocompletion and syntax highlighting. Read the reference that matches your task.

## References
- `references/pgcli.md` — install, connect (DSN/URL/named connections), `~/.pgclirc`, autocomplete, `\?` special commands, `\timing`, output formats, `\copy`, running `.sql` files
- `references/sql.md` — SELECT/INSERT/UPDATE/DELETE, JOINs, upsert (`ON CONFLICT`), CTEs, window functions, JSONB, arrays, `RETURNING`, keyset pagination, transactions
- `references/admin.md` — meta-commands (`\l \dt \d \du \df \x`), roles/`GRANT`, create db/users, `EXPLAIN ANALYZE`, indexes, `VACUUM`/`ANALYZE`, `pg_stat_activity`, introspection
- `references/troubleshooting.md` — auth/`pg_hba`/SSL errors, "too many connections", slow queries, lock contention, serial/sequence issues, encoding, `pg_terminate_backend`

## TL;DR
- Connect with a URL: `pgcli postgres://user:pass@host:5432/dbname` — or save it as a named connection in `~/.pgclirc` and run `pgcli mydb`.
- pgcli accepts almost every psql backslash command (`\dt`, `\d table`, `\l`, `\du`); run `\?` for the full list. Use `\h SELECT` for SQL syntax help.
- `\x` toggles expanded (vertical) output — essential for wide rows. `\timing` shows query duration.
- Upsert = `INSERT ... ON CONFLICT (col) DO UPDATE SET ...`; add `RETURNING *` to any write to get the affected rows back.
- Wrap risky writes in `BEGIN; ... ROLLBACK;` first to preview, then `COMMIT;` when correct.
- `EXPLAIN ANALYZE <query>` runs the query and shows the real plan + timings; look for `Seq Scan` on big tables → add an index.
- Find and kill a runaway query: `SELECT pid, query FROM pg_stat_activity WHERE state='active';` then `SELECT pg_terminate_backend(<pid>);`.
- Use **GIN** indexes for JSONB/array/full-text columns, **btree** (the default) for everything else.

## Docs
- PostgreSQL manual — https://www.postgresql.org/docs/current/
- pgcli — https://www.pgcli.com/
- pgcli source & config — https://github.com/dbcli/pgcli
- psql reference — https://www.postgresql.org/docs/current/app-psql.html
