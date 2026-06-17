## Reading data

Spark infers nothing for free — be explicit with CSV.

```python
# CSV with header + schema inference
df = spark.read.option("header", True).option("inferSchema", True).csv("data/people.csv")

# JSON (one object per line, or multiline)
df = spark.read.json("data/events.json")
df = spark.read.option("multiline", True).json("data/nested.json")

# Parquet (schema is embedded — fastest, preferred)
df = spark.read.parquet("data/events.parquet")

# Generic form
df = spark.read.format("csv").option("header", True).load("data/people.csv")
```

Scala is the same shape:

```scala
val df = spark.read.option("header", true).csv("data/people.csv")
```

---

## Inspecting

```python
df.show()              # first 20 rows, truncated
df.show(50, truncate=False)
df.printSchema()       # column names + types
df.columns             # ['id', 'name', ...]
df.dtypes              # [('id','int'), ...]
df.count()             # ACTION: number of rows
df.describe().show()   # summary stats
df.explain()           # physical plan (no execution)
df.explain(True)       # parsed/analyzed/optimized/physical plans
```

---

## Transformations (lazy)

```python
import pyspark.sql.functions as F

result = (
    df
    .select("id", "name", "age")            # project columns
    .filter(F.col("age") >= 18)             # or .where(...)
    .withColumn("decade", (F.col("age") / 10).cast("int") * 10)
    .withColumnRenamed("name", "full_name")
    .drop("temp_col")
    .dropDuplicates(["id"])
)
```

Filter syntax variants (all equivalent):

```python
df.filter(df.age > 18)
df.filter(F.col("age") > 18)
df.filter("age > 18")          # SQL string expression
```

---

## groupBy / agg

```python
import pyspark.sql.functions as F

(df.groupBy("country")
   .agg(
       F.count("*").alias("n"),
       F.avg("age").alias("avg_age"),
       F.max("age").alias("max_age"),
   )
   .orderBy(F.desc("n"))
   .show())
```

---

## Joins

```python
joined = orders.join(users, on="user_id", how="inner")     # inner, left, right, outer, semi, anti
joined = orders.join(users, orders.user_id == users.id, "left")

# Broadcast the small side to avoid a shuffle
from pyspark.sql.functions import broadcast
orders.join(broadcast(users), "user_id")
```

---

## Common functions (`functions as F`)

```python
import pyspark.sql.functions as F

df.select(
    F.upper("name"),
    F.length("name"),
    F.coalesce("nickname", "name"),
    F.when(F.col("age") < 18, "minor").otherwise("adult").alias("bucket"),
    F.to_date("created_at", "yyyy-MM-dd"),
    F.year("created_at"),
    F.lit("constant"),
)
```

Window functions:

```python
from pyspark.sql.window import Window
import pyspark.sql.functions as F

w = Window.partitionBy("country").orderBy(F.desc("score"))
df.withColumn("rank", F.row_number().over(w)).show()
```

---

## Caching

Cache when you reuse a DataFrame across multiple actions — otherwise Spark recomputes it each time.

```python
df.cache()             # lazy; materializes on next action (default MEMORY_AND_DISK)
df.count()             # triggers the cache
df.is_cached           # True
df.unpersist()         # free it
```

---

## Temp views + SQL

Mix DataFrame and SQL freely.

```python
df.createOrReplaceTempView("people")
adults = spark.sql("SELECT country, COUNT(*) n FROM people WHERE age >= 18 GROUP BY country")
adults.show()
```

See `references/spark-sql.md` for the catalog and table types.

---

## Writing out

```python
# Parquet, overwrite, partitioned
df.write.mode("overwrite").partitionBy("country").parquet("out/people")

# Single CSV file with header
df.coalesce(1).write.mode("overwrite").option("header", True).csv("out/people_csv")

# Modes: error (default), overwrite, append, ignore
df.write.mode("append").parquet("out/events")
```

---

## Lazy evaluation & actions

Transformations (`select`, `filter`, `join`, `withColumn`, `groupBy`) build a plan and run nothing. Work happens only on an **action**:

- `show()`, `count()`, `collect()`, `take(n)`, `first()`, `head()`
- `write....save()`, `toPandas()`, `foreach()`

`collect()` / `toPandas()` pull **all** rows to the driver — guard with `limit()` or you risk a driver OOM (see `references/troubleshooting.md`). Use `explain()` to see the plan before paying for an action.

---

## Docs
- DataFrame / SQL programming guide: https://spark.apache.org/docs/latest/sql-programming-guide.html
- PySpark DataFrame API: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html
- `functions` (column functions): https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html
- RDD/transformations vs actions: https://spark.apache.org/docs/latest/rdd-programming-guide.html#transformations
- Data sources (CSV/JSON/Parquet): https://spark.apache.org/docs/latest/sql-data-sources.html
