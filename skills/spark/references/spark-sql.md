## Two ways to run SQL

```bash
# 1) The spark-sql shell — pure SQL prompt
spark-sql --master 'local[*]'
```
```sql
spark-sql> SELECT 1 + 1;
spark-sql> SHOW TABLES;
```

```python
# 2) From pyspark / any session — spark.sql returns a DataFrame
df = spark.sql("SELECT country, COUNT(*) AS n FROM people GROUP BY country")
df.show()
```

`spark.sql(...)` is lazy and returns a DataFrame; in the `spark-sql` shell a statement runs immediately and prints results.

---

## Exploring the catalog

```sql
SHOW DATABASES;                 -- aka SHOW SCHEMAS
SHOW TABLES;                    -- in current database
SHOW TABLES IN mydb;
USE mydb;                       -- set current database

DESCRIBE TABLE people;          -- columns + types
DESCRIBE EXTENDED people;       -- + location, provider, table type
SHOW CREATE TABLE people;
SHOW COLUMNS FROM people;
SHOW FUNCTIONS;
```

From Python via the catalog API:

```python
spark.catalog.listDatabases()
spark.catalog.listTables()
spark.catalog.listColumns("people")
spark.catalog.currentDatabase()
spark.catalog.setCurrentDatabase("mydb")
```

---

## Temp views vs managed tables

| Kind | Lifetime | Stored where | Create |
|---|---|---|---|
| Temp view | this session only | nothing on disk | `df.createOrReplaceTempView("t")` |
| Global temp view | across sessions, same app | nothing on disk | `df.createGlobalTempView("t")` → query as `global_temp.t` |
| Managed table | persists in metastore | Spark-owned warehouse dir | `CREATE TABLE ... ` (no `LOCATION`) |
| External table | persists in metastore | your path; not deleted on DROP | `CREATE TABLE ... LOCATION '...'` |

```python
df.createOrReplaceTempView("people")
spark.sql("SELECT * FROM people LIMIT 5").show()
```

Dropping a **managed** table deletes its data; dropping an **external** table only removes the metadata.

---

## CREATE TABLE

```sql
-- Managed, Spark-native format
CREATE TABLE events (id BIGINT, ts TIMESTAMP, kind STRING) USING parquet;

-- Create from a query (CTAS)
CREATE TABLE adults USING parquet AS
SELECT * FROM people WHERE age >= 18;

-- External table over existing files
CREATE TABLE ext_events (id BIGINT, kind STRING)
USING parquet
LOCATION '/data/events';

INSERT INTO events VALUES (1, current_timestamp(), 'click');
INSERT OVERWRITE TABLE events SELECT * FROM staging;
```

---

## Query files directly — no table needed

Read a path as a table using `format`.\`path\` syntax:

```sql
SELECT * FROM parquet.`/data/events.parquet` LIMIT 5;
SELECT * FROM json.`/data/events.json`;
SELECT COUNT(*) FROM csv.`/data/people.csv`;
```

Great for ad-hoc exploration in the `spark-sql` shell against local files.

---

## Configuration via SET

```sql
SET spark.sql.shuffle.partitions=8;     -- default 200; lower for small local data
SET spark.sql.shuffle.partitions;       -- show current value
SET -v;                                 -- list all SQL config with descriptions
SET spark.sql.session.timeZone=UTC;
```

Equivalent from a session:

```python
spark.conf.set("spark.sql.shuffle.partitions", "8")
```

`EXPLAIN` works in SQL too:

```sql
EXPLAIN EXTENDED SELECT country, COUNT(*) FROM people GROUP BY country;
```

---

## Docs
- SQL reference: https://spark.apache.org/docs/latest/sql-ref.html
- SQL syntax (SHOW/DESCRIBE/CREATE): https://spark.apache.org/docs/latest/sql-ref-syntax.html
- CREATE TABLE: https://spark.apache.org/docs/latest/sql-ref-syntax-ddl-create-table.html
- Generic file source (query a path directly): https://spark.apache.org/docs/latest/sql-data-sources-generic-options.html
- Catalog API (PySpark): https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/catalog.html
- SQL config (SET): https://spark.apache.org/docs/latest/sql-ref-syntax-aux-conf-mgmt-set.html
