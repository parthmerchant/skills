---
name: spark
description: Running interactive Apache Spark commands against a local Spark server — pyspark, spark-shell, spark-sql, and Spark Connect; DataFrame API, Spark SQL, sessions, configs, and debugging. Use when launching pyspark/spark-shell/spark-sql, connecting to a local standalone master (spark://localhost:7077) or local[*], using Spark Connect (sc://localhost:15002), exploring DataFrames/SQL interactively, or debugging a local Spark job/UI.
---

# Apache Spark — Interactive & Local

App-agnostic fundamentals for driving a local Spark server from the terminal. Read the reference that matches your task.

## References
- `references/interactive-shell.md` — launching pyspark/spark-shell/spark-sql, `--master`, Spark Connect `--remote`, `--conf`/`--packages`/`--jars`, memory, `spark`/`sc`, local standalone master, Spark UI
- `references/dataframes.md` — reading/writing, select/filter/withColumn/groupBy/agg/join, `functions as F`, show/printSchema/explain, caching, temp views, lazy vs actions
- `references/spark-sql.md` — `spark-sql` shell & `spark.sql(...)`, SHOW/DESCRIBE, temp vs managed tables, catalog, query files directly, `SET`
- `references/troubleshooting.md` — master/worker registration, "Initial job has not accepted resources", version/Java mismatch, Connect vs classic conflicts, OOM, reading the UI/DAG, Py4J errors, port 4040→4041

## TL;DR
- `--master local[*]` runs everything in-process; `--master spark://localhost:7077` targets a standalone server you started with `start-master.sh` + `start-worker.sh`.
- In `pyspark`/`spark-shell` the `spark` (SparkSession) and `sc` (SparkContext) objects are **already created** — don't make new ones.
- Transformations are **lazy**; nothing runs until an **action** (`show`, `count`, `collect`, `write`). `explain()` shows the plan without executing.
- Spark Connect uses `--remote sc://localhost:15002` (or `spark.remote`); it gives you a `spark` session but **no `sc`** and only DataFrame APIs — don't mix with a classic `--master`.
- Watch the live job UI at http://localhost:4040 (next free port 4041, 4042… if taken); standalone master UI is http://localhost:8080.
- Tune memory with `--driver-memory 4g` / `--executor-memory 4g`; collecting too much to the driver is the classic OOM.
- `import pyspark.sql.functions as F` for column expressions; register a DataFrame with `df.createOrReplaceTempView("t")` then query it via `spark.sql`.

## Docs
- Overview: https://spark.apache.org/docs/latest/
- Submitting/launching: https://spark.apache.org/docs/latest/submitting-applications.html
- Spark Connect: https://spark.apache.org/docs/latest/spark-connect-overview.html
- Standalone mode: https://spark.apache.org/docs/latest/spark-standalone.html
