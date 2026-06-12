# PostgreSQL — fundamentals

## Schema design
- Pick precise types: `bigint` ids, `text`/`varchar`, `numeric(p,s)` for money
  (never float for currency), `timestamptz` for time, `boolean`, `date`.
- Enforce integrity in the DB, not just the app:
  - `NOT NULL` and sensible `DEFAULT`s.
  - `FOREIGN KEY ... ON DELETE CASCADE/RESTRICT`.
  - `UNIQUE` and `CHECK` constraints for invariants.

## Indexing
- Index columns used in `WHERE`, `JOIN`, `ORDER BY`, and FKs (Rails doesn't index
  FKs automatically on raw SQL — `add_index` them).
- Composite indexes follow left-to-right usage; column order matters.
- Specialized indexes: **GIN** for `array`/`jsonb`/full-text, partial indexes for
  filtered subsets (`WHERE active`).
- `EXPLAIN ANALYZE` before adding indexes — measure, don't guess.

## Arrays & JSONB
- `text[]` for small tag-like lists; query with `@>` (contains) and a GIN index.
  ```sql
  WHERE tags @> ARRAY['vip']::varchar[]
  ```
- `jsonb` for flexible/nested data; index with GIN. Prefer real columns when the
  shape is known and queried often.

## Querying & safety
- Always use **parameterized queries** (Rails does via `where(col: val)` /
  bind params) — never string-interpolate user input.
- Use transactions for multi-statement invariants.
- Full-text search: `to_tsvector`/`to_tsquery`, or `ILIKE '%term%'` for simple
  substring matching (add a `pg_trgm` GIN index if it gets hot).

## Operations
- Migrations should be safe on live tables: add nullable columns or set defaults
  carefully on large tables; create indexes `CONCURRENTLY` in production.
- Back up with `pg_dump`; pin the major version in your image (`postgres:16`).
