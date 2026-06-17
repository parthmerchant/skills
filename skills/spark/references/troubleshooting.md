## Connecting to a local standalone server

```bash
# Did master + worker actually start?
jps                       # expect: Master, Worker (and your shell's SparkSubmit)

# Master UI lists registered workers + running apps
open http://localhost:8080
```

- **Wrong master URL** — must match exactly what the master logs print, e.g. `spark://localhost:7077` (RPC port **7077**, not the **8080** UI port). On some hosts use the machine hostname instead of `localhost`.
- **No worker registered** — `start-master.sh` alone is not enough; run `start-worker.sh spark://localhost:7077`. The worker must appear under "Workers" in the UI.

---

## "Initial job has not accepted any resources..."

```
WARN TaskSchedulerImpl: Initial job has not accepted any resources;
check your cluster UI to ensure that workers are registered and have sufficient resources
```

The driver connected to the master but no executor can be launched. Causes:

- No worker registered (see above).
- You asked for more memory/cores than a worker has free — lower `--executor-memory` / `--executor-cores`, or check what the worker advertises in the UI.
- A previous shell is still holding all the cores (standalone defaults to grabbing every available core). Stop it, or cap with `--total-executor-cores`.
- Firewall blocking the random driver callback port — pin it with `--conf spark.driver.port=...` and `--conf spark.driver.host=<reachable-ip>`.

---

## Version / Java mismatch

```bash
spark-submit --version    # Spark + Scala + JVM build it expects
java -version             # installed JVM
echo $JAVA_HOME
```

- Spark 3.x needs **Java 8/11/17** (Spark 4.x raises the floor). A too-new or too-old JDK throws `UnsupportedClassVersionError` or obscure startup failures — set `JAVA_HOME` to a supported JDK.
- PySpark version must match the cluster Spark version: `pip show pyspark` vs the server's `spark-submit --version`. A mismatch yields serialization/protocol errors.
- Scala version in `--packages` coordinates must match Spark's Scala build (e.g. `_2.12` vs `_2.13`).

---

## Spark Connect vs classic session conflicts

- Don't pass both `--remote sc://...` and `--master ...` — pick one. With `--remote`, you get a Connect client.
- A Connect session has **no `sc`** (SparkContext) and **no RDD API**. Code that calls `sc.parallelize(...)` or `df.rdd` fails — port it to the DataFrame API or use a classic `--master` session.
- `SparkContext can only be used on the driver` / "RDD ... not supported in Spark Connect" → you're on a Connect session expecting a classic one.
- Confirm which mode you're in: `type(spark)` — a Connect session is `pyspark.sql.connect.session.SparkSession`.

---

## OutOfMemory — driver vs executor

```
java.lang.OutOfMemoryError: Java heap space
```

- **Driver OOM** usually means you pulled too much back: `collect()`, `toPandas()`, a huge `show(n)`, or a broadcast of a not-small table. Fix: `limit()` first, write to disk instead of collecting, raise `--driver-memory`.
- **Executor OOM** means a partition/shuffle is too big. Fix: raise `--executor-memory`, increase `spark.sql.shuffle.partitions` (smaller partitions), avoid skewed joins, prefer `broadcast()` only for genuinely small tables.
- In `local[*]` everything is the driver JVM, so bump `--driver-memory`.

---

## Reading the Spark UI / DAG

Open **http://localhost:4040** while a job runs (`sc.uiWebUrl` prints the exact URL).

- **Jobs** → each action is a job; click into **Stages** to find the slow stage.
- **SQL / DataFrame** tab → the query plan with row counts and per-node time; spot huge `Exchange` (shuffle) or `BroadcastExchange` nodes.
- A long "tail" stage with one straggling task usually means **data skew**.
- Lots of stages with `Exchange` between them = expensive shuffles; reduce with broadcast joins or fewer wide transformations.
- After the app stops the live UI dies; use the **History Server** for past runs.

---

## Common Py4J errors (PySpark)

`Py4JJavaError` wraps a JVM-side exception — **scroll to the `Caused by:` line**, that's the real error (e.g. `Analysisof`, `FileNotFoundException`, `NumberFormatException`).

- `Py4JError: ... does not exist in the JVM` / `Py4JNetworkError` → the JVM gateway died or PySpark/Spark versions mismatch; restart the shell, check versions.
- `AnalysisException: cannot resolve 'col'` → typo'd column or wrong DataFrame; check `df.columns` (this is an analysis error, not a runtime one).
- `Path does not exist` → relative paths resolve against the **driver's** working dir (and against the cluster filesystem in non-local modes) — use absolute paths.

---

## Port already in use (4040 → 4041)

```
WARN Utils: Service 'SparkUI' could not bind on port 4040. Attempting port 4041.
```

Harmless — another Spark session already holds 4040, so this one took the next free port. Check the launch log (or `sc.uiWebUrl`) for the actual port. Pin it if you want a fixed value:

```bash
pyspark --conf spark.ui.port=4050
```

Other ports that collide on a busy box: master `8080`/`8081`, worker `8081`, standalone RPC `7077`, Connect `15002`, history server `18080`.

---

## Docs
- Monitoring & Web UI: https://spark.apache.org/docs/latest/web-ui.html
- Configuration (memory, ports, driver/executor): https://spark.apache.org/docs/latest/configuration.html
- Tuning guide (memory, shuffle, skew): https://spark.apache.org/docs/latest/tuning.html
- Standalone troubleshooting: https://spark.apache.org/docs/latest/spark-standalone.html
- Spark Connect overview & limitations: https://spark.apache.org/docs/latest/spark-connect-overview.html
- Security / network ports: https://spark.apache.org/docs/latest/security.html#configuring-ports-for-network-security
