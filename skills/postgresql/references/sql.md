## SELECT basics

```sql
SELECT id, email, created_at
FROM users
WHERE active = true AND created_at >= now() - interval '30 days'
ORDER BY created_at DESC
LIMIT 50;

-- Aggregation
SELECT country, count(*) AS n, avg(age)::numeric(5,1) AS avg_age
FROM users
GROUP BY country
HAVING count(*) > 10
ORDER BY n DESC;

-- DISTINCT ON: one row per group (first by ORDER BY)
SELECT DISTINCT ON (user_id) user_id, created_at, status
FROM orders
ORDER BY user_id, created_at DESC;
```

---

## INSERT / UPDATE / DELETE + RETURNING

`RETURNING` hands back the affected rows from any write — no second query needed.

```sql
INSERT INTO users (email, name)
VALUES ('a@x.com', 'Ada')
RETURNING id, created_at;

-- Bulk insert
INSERT INTO users (email, name)
VALUES ('a@x.com','Ada'), ('b@x.com','Bea');

UPDATE users
SET name = 'Ada L.', updated_at = now()
WHERE id = 42
RETURNING *;

DELETE FROM users
WHERE last_login < now() - interval '2 years'
RETURNING id, email;
```

Always include a `WHERE` on UPDATE/DELETE unless you truly mean every row.

---

## Upsert — ON CONFLICT

Requires a unique constraint / index on the conflict target. See https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT.

```sql
-- Insert, or update if the email already exists
INSERT INTO users (email, name, login_count)
VALUES ('a@x.com', 'Ada', 1)
ON CONFLICT (email)
DO UPDATE SET
  name = EXCLUDED.name,
  login_count = users.login_count + 1
RETURNING *;

-- Insert, or silently skip duplicates
INSERT INTO tags (name) VALUES ('sql')
ON CONFLICT (name) DO NOTHING;
```

`EXCLUDED` refers to the row that *would* have been inserted.

---

## JOINs

```sql
SELECT u.email, o.id AS order_id, o.total
FROM users u
JOIN orders o      ON o.user_id = u.id          -- INNER: matches only
LEFT JOIN refunds r ON r.order_id = o.id         -- keep orders w/o refunds
WHERE u.active
ORDER BY o.created_at DESC;

-- "Users with no orders" via LEFT JOIN + NULL filter
SELECT u.id, u.email
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;

-- Lateral join: top-3 orders per user
SELECT u.id, recent.total
FROM users u
CROSS JOIN LATERAL (
  SELECT total FROM orders o
  WHERE o.user_id = u.id
  ORDER BY created_at DESC LIMIT 3
) recent;
```

---

## CTEs (WITH)

```sql
WITH recent AS (
  SELECT * FROM orders WHERE created_at >= now() - interval '7 days'
), per_user AS (
  SELECT user_id, sum(total) AS spent FROM recent GROUP BY user_id
)
SELECT u.email, p.spent
FROM per_user p JOIN users u ON u.id = p.user_id
ORDER BY p.spent DESC;

-- Recursive CTE: walk a category tree
WITH RECURSIVE tree AS (
  SELECT id, parent_id, name FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.parent_id, c.name
  FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree;
```

Data-modifying CTEs are allowed: `WITH moved AS (DELETE FROM a WHERE ... RETURNING *) INSERT INTO b SELECT * FROM moved;`

---

## Window functions

Compute across a set of rows *without* collapsing them. See https://www.postgresql.org/docs/current/tutorial-window.html.

```sql
SELECT
  user_id,
  created_at,
  total,
  row_number() OVER w           AS seq,
  rank()       OVER w           AS rnk,
  sum(total)   OVER w           AS running_total,
  lag(total)   OVER w           AS prev_total
FROM orders
WINDOW w AS (PARTITION BY user_id ORDER BY created_at);

-- Latest order per user (rank then filter)
SELECT * FROM (
  SELECT *, row_number() OVER (PARTITION BY user_id ORDER BY created_at DESC) rn
  FROM orders
) t WHERE rn = 1;
```

---

## JSONB

`->` returns JSON, `->>` returns text. Use `@>` (containment) and a GIN index for fast lookups. See https://www.postgresql.org/docs/current/functions-json.html.

```sql
-- Extract
SELECT data->'address'->>'city' AS city
FROM users
WHERE data->>'plan' = 'pro';

-- Path extraction
SELECT data #>> '{address,zip}' FROM users;

-- Containment (uses GIN index)
SELECT * FROM users WHERE data @> '{"plan":"pro"}';

-- Key existence
SELECT * FROM users WHERE data ? 'address';

-- Update a key (merge) / remove a key
UPDATE users SET data = data || '{"verified":true}'      WHERE id = 1;
UPDATE users SET data = data - 'temp_flag'               WHERE id = 1;
UPDATE users SET data = jsonb_set(data, '{plan}', '"enterprise"') WHERE id = 1;

-- Expand array of objects into rows
SELECT e.value->>'sku' AS sku
FROM orders o, jsonb_array_elements(o.items) AS e;
```

---

## Arrays

See https://www.postgresql.org/docs/current/arrays.html.

```sql
CREATE TABLE posts (id serial PRIMARY KEY, tags text[]);
INSERT INTO posts (tags) VALUES (ARRAY['sql','postgres']);

SELECT * FROM posts WHERE 'sql' = ANY(tags);     -- membership
SELECT * FROM posts WHERE tags @> ARRAY['sql'];  -- contains (GIN-indexable)
UPDATE posts SET tags = array_append(tags, 'cli') WHERE id = 1;

-- Array <-> rows
SELECT id, unnest(tags) AS tag FROM posts;
SELECT array_agg(name ORDER BY name) FROM users;
```

---

## Pagination — LIMIT/OFFSET vs keyset

`OFFSET` scans and discards skipped rows, so deep pages get slow. **Keyset (seek)** pagination uses the last seen value and stays fast at any depth.

```sql
-- OFFSET: simple, fine for shallow pages
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 40;

-- Keyset: pass the last id from the previous page
SELECT * FROM orders
WHERE id > :last_seen_id
ORDER BY id
LIMIT 20;

-- Keyset on a non-unique sort key: tie-break with a unique column
SELECT * FROM orders
WHERE (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

---

## Transactions

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
-- inspect results, then:
COMMIT;     -- or ROLLBACK; to undo everything

-- Preview a destructive change safely
BEGIN;
DELETE FROM logs WHERE created_at < '2024-01-01';
-- check the row count, then ROLLBACK; if it looks wrong
ROLLBACK;

-- Savepoints for partial rollback
BEGIN;
  INSERT INTO a VALUES (1);
  SAVEPOINT sp1;
  INSERT INTO a VALUES (2);   -- oops
  ROLLBACK TO sp1;            -- undo just the second insert
COMMIT;
```

Lock a row to prevent concurrent edits: `SELECT ... FOR UPDATE` inside a transaction. Isolation levels at https://www.postgresql.org/docs/current/transaction-iso.html.

---

## Docs
- SQL command reference — https://www.postgresql.org/docs/current/sql-commands.html
- `INSERT ... ON CONFLICT` — https://www.postgresql.org/docs/current/sql-insert.html
- Window functions — https://www.postgresql.org/docs/current/tutorial-window.html
- JSON functions — https://www.postgresql.org/docs/current/functions-json.html
- Arrays — https://www.postgresql.org/docs/current/arrays.html
- Transaction isolation — https://www.postgresql.org/docs/current/transaction-iso.html
