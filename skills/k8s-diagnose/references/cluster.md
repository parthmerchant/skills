## Cluster topology

| What | Value |
|---|---|
| Context | `kind-my-kind-cluster` |
| Nodes | `my-kind-cluster-control-plane`, `my-kind-cluster-worker`, `my-kind-cluster-worker2` |
| k8s version | 1.35.0 |
| Runtime | containerd 2.2.0 |
| CNI | kindnet |
| Storage | local-path provisioner |

## Namespace map

| Namespace | Workloads |
|---|---|
| `spark` | Spark Connect Server (gRPC :15002), PySpark / Scala SparkApplications |
| `minio` | MinIO standalone (S3-compatible, Iceberg warehouse at `s3a://warehouse/`) |
| `rag` | rag-api, rag-ui, rag-ingest, postgres, qdrant, ollama |
| `logging` | Loki (single-binary), Grafana (:3000) |
| `opentelemetry` | OTel Collector (OTLP → Loki) |
| `spark-operator` | Spark Operator |
| `keda` | KEDA autoscaler |
| `cert-manager` | Webhook certs (required by Spark Operator) |
| `ingress-nginx` | NGINX ingress controller |

## Justfile shortcuts (run from `~/PM/my-kind-cluster/`)

```bash
just status                     # nodes + all pods at a glance
just logs <app> <namespace>     # tail pod logs by label
just pf-minio                   # port-forward → localhost:9001
just pf-grafana                 # port-forward → localhost:3000
just pf-spark-connect           # port-forward → localhost:15002
just pf-rag-api                 # port-forward → localhost:8000
just pf-qdrant                  # port-forward → localhost:6333
just pf-postgres                # port-forward → localhost:5432
```
