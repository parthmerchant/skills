## pyspark — interactive Python REPL

```bash
# In-process: spins up a local SparkSession, all on this machine
pyspark --master 'local[*]'          # use all cores
pyspark --master 'local[4]'          # 4 worker threads

# Against a local standalone server (see "Local standalone server" below)
pyspark --master spark://localhost:7077
```

`pyspark` drops you into a Python shell with two objects already created — **do not recreate them**:

```python
spark          # SparkSession  -> DataFrame / SQL entry point
sc             # SparkContext  -> low-level RDD / cluster handle

spark.version          # '3.5.x'
sc.master              # 'local[*]'
sc.defaultParallelism  # number of cores Spark sees

df = spark.range(10)   # quick smoke test
df.show()
```

---

## spark-shell — interactive Scala REPL

```bash
spark-shell --master 'local[*]'
spark-shell --master spark://localhost:7077
```

Same pre-created objects, Scala flavor:

```scala
spark            // org.apache.spark.sql.SparkSession
sc               // org.apache.spark.SparkContext

spark.range(10).show()
val df = spark.read.json("data.json")
```

---

## spark-sql — interactive SQL shell

```bash
spark-sql --master 'local[*]'
```

Drops you at a `spark-sql>` prompt; type SQL directly (see `references/spark-sql.md`):

```sql
SHOW DATABASES;
SELECT * FROM parquet.`/data/events.parquet` LIMIT 5;
```

---

## --master values

| Value | Meaning |
|---|---|
| `local` | single thread, in-process |
| `local[4]` | 4 threads, in-process |
| `local[*]` | one thread per core, in-process |
| `spark://host:7077` | connect to a standalone master |
| `yarn` / `k8s://...` | cluster managers (not local) |

If you omit `--master`, Spark falls back to `spark.master` config or `local[*]`.

---

## Spark Connect — thin remote client

Spark Connect talks gRPC to a running Connect server (default port **15002**). The client is decoupled from the JVM cluster.

```bash
# Start a Connect server (once), then connect a shell to it
start-connect-server.sh --packages org.apache.spark:spark-connect_2.12:3.5.1

# pyspark as a Connect client
pyspark --remote sc://localhost:15002

# spark-shell as a Connect client
spark-shell --remote sc://localhost:15002
```

Or from a plain Python process:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.remote("sc://localhost:15002").getOrCreate()
spark.range(5).show()
```

Set it via config instead of a flag:

```bash
pyspark --conf spark.remote=sc://localhost:15002
```

Caveats: a Connect session exposes the **DataFrame/SQL API only** — there is **no `sc` / SparkContext**, no RDDs. Don't combine `--remote` with `--master`.

---

## --conf, --packages, --jars

```bash
# Arbitrary Spark config (repeat --conf as needed)
pyspark --conf spark.sql.shuffle.partitions=8 \
        --conf spark.sql.session.timeZone=UTC

# Pull a Maven coordinate at launch (e.g. Postgres JDBC, Iceberg, Kafka)
pyspark --packages org.postgresql:postgresql:42.7.3

# Add local jar(s) to driver + executor classpaths
spark-shell --jars /opt/libs/mylib.jar,/opt/libs/other.jar
```

You can also set config from inside the session at runtime:

```python
spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.get("spark.sql.shuffle.partitions")
```

---

## Driver / executor memory & cores

```bash
pyspark --master spark://localhost:7077 \
  --driver-memory 4g \
  --executor-memory 4g \
  --executor-cores 2 \
  --total-executor-cores 8
```

- **driver-memory** — JVM heap on the machine running the shell (matters when you `.collect()` lots of rows).
- **executor-memory / executor-cores** — per-executor resources on the workers.
- In `local[*]` there are no separate executors; everything uses the driver JVM, so `--driver-memory` is what counts.

---

## Local standalone server

Start a master + at least one worker, then point shells at the master URL.

```bash
# $SPARK_HOME/sbin
start-master.sh                       # master + UI on :8080, RPC on :7077
start-worker.sh spark://localhost:7077  # register a worker

# Verify
jps                                   # look for Master and Worker
# Master UI -> http://localhost:8080  (shows registered workers + apps)

# Connect a shell
pyspark --master spark://localhost:7077

# Tear down
stop-worker.sh
stop-master.sh
# or stop-all.sh / start-all.sh for both
```

If a shell hangs with *"Initial job has not accepted any resources"*, the worker probably isn't registered or has no free cores/memory — check the master UI. See `references/troubleshooting.md`.

---

## Spark UI

Every running driver serves a live UI at **http://localhost:4040** (jobs, stages, SQL, storage, executors). If 4040 is busy it tries **4041**, **4042**, … — watch the launch log for the actual port. The standalone **master** UI is separate at http://localhost:8080.

```python
sc.uiWebUrl    # exact UI URL for this session
```

---

## Docs
- Submitting / launcher options: https://spark.apache.org/docs/latest/submitting-applications.html
- Configuration reference: https://spark.apache.org/docs/latest/configuration.html
- Spark Connect overview: https://spark.apache.org/docs/latest/spark-connect-overview.html
- Spark Connect (Python quickstart): https://spark.apache.org/docs/latest/api/python/getting_started/quickstart_connect.html
- Standalone mode (start-master/worker, master URL): https://spark.apache.org/docs/latest/spark-standalone.html
- Monitoring & Web UI: https://spark.apache.org/docs/latest/web-ui.html
