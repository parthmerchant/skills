## Step 0 — establish context

Always confirm context before touching anything:

```bash
kubectl config current-context               # must be kind-my-kind-cluster
kubectl get nodes                            # all Ready?
kubectl get pods -A | grep -Ev "Running|Completed"   # anything unhealthy?
```

---

## Step 1 — triage by symptom

### Pod stuck in `Pending`

```bash
kubectl describe pod <pod> -n <ns>    # look at Events section
kubectl get events -n <ns> --sort-by='.lastTimestamp'
```

Common causes on this cluster:
- **Insufficient resources** — kind nodes share the host's Docker VM RAM (typically 4–8 GB). Check `kubectl top nodes` (requires metrics-server) or `docker stats`.
- **Toleration / nodeSelector mismatch** — the ingress-nginx controller is pinned to the control-plane node via `ingress-ready=true` label.
- **PVC stuck** — local-path provisioner only binds when a pod is scheduled; `Pending` PVC is normal until a consumer exists.

### Pod in `CrashLoopBackOff` or `Error`

```bash
kubectl logs <pod> -n <ns> --previous    # logs from the crashed container
kubectl describe pod <pod> -n <ns>       # exit code + reason
```

Exit code cheatsheet:
- `137` — OOMKilled (request more memory or reduce replica count)
- `1` / `2` — application error (check logs)
- `128+n` — killed by signal n (e.g. 143 = SIGTERM)

### Pod in `ImagePullBackOff`

```bash
kubectl describe pod <pod> -n <ns> | grep -A5 "Events:"
```

On kind, images must be loaded into the cluster — they are **not** pulled from local Docker daemon:

```bash
# rebuild and load into kind
just build-load <app>
# or manually:
docker build -t <app>:latest apps/<app>/src/
kind load docker-image <app>:latest --name my-kind-cluster
```

### `OOMKilled` pods

kind runs inside Docker — all nodes share the host VM's memory. On resource pressure:

1. Check which pods are memory-heavy: `kubectl top pods -A --sort-by=memory`
2. Scale down non-essential workloads: `kubectl scale deployment <name> -n <ns> --replicas=0`
3. Ollama (LLM in `rag` namespace) is the biggest consumer — disable it if not needed.

---

## Step 2 — app-specific diagnostics

### Spark / Spark Connect Server

```bash
kubectl get pods -n spark
kubectl logs -l app=spark-connect-server -n spark --tail=50
# SparkApplication CRDs (submitted jobs):
kubectl get sparkapplication -n spark
kubectl describe sparkapplication <name> -n spark
```

Common issues:
- **Driver pod Pending** — insufficient CPU/memory; Spark Operator defaults can be too high for local use. Edit `apps/spark-connect-server/infra/` values.
- **S3A auth failure** — verify `fs.s3a.endpoint=http://minio.minio.svc.cluster.local:9000` and credentials `minioadmin / minioadmin123`.
- **gRPC connection refused** — run `just pf-spark-connect` first; the service is ClusterIP-only.

### MinIO

```bash
kubectl get pods -n minio
kubectl logs -l app=minio -n minio --tail=50
# Access the console after port-forwarding:
# http://localhost:9001  — minioadmin / minioadmin123
```

Common issues:
- **Bucket init Job failed** — `kubectl logs -n minio job/minio-init-buckets`; re-apply with `kubectl delete job minio-init-buckets -n minio && kubectl apply -f apps/minio/infra/init-buckets-job.yaml`
- **S3A 403 from Spark** — MinIO bucket or path doesn't exist; create via the console or `mc`.

### RAG stack (rag namespace)

```bash
kubectl get pods -n rag
kubectl logs -l app=rag-api -n rag --tail=50
kubectl logs -l app=ollama -n rag --tail=50       # slow to start; pulls model on first run
kubectl logs -l app=rag-ingest -n rag --tail=50
# Health check (after port-forward):
curl http://localhost:8000/api/health
```

Common issues:
- **Ollama OOMKilled** — needs ≥2 GB RAM; scale down other workloads or use docker-compose stack (`just rag-compose-up`) for local development instead.
- **qdrant not ready** — `kubectl rollout status deployment/qdrant -n rag`
- **postgres not ready** — `kubectl rollout status deployment/postgres -n rag`
- **rag-api 503** — usually waiting on qdrant or postgres; check both are Running.

### Loki / Grafana

```bash
kubectl get pods -n logging
kubectl logs -l app.kubernetes.io/name=loki -n logging --tail=50
# After port-forward: http://localhost:3000  — admin / admin
# Explore → Loki datasource → query: {namespace="rag"}
```

### OTel Collector

```bash
kubectl get pods -n opentelemetry
kubectl logs -l app=opentelemetry-collector -n opentelemetry --tail=50
```

### cert-manager (Spark Operator dependency)

```bash
kubectl get pods -n cert-manager
kubectl get certificaterequests -A
kubectl get certificates -A
```

If cert-manager is unhealthy, the Spark Operator webhook will refuse all SparkApplication submissions.
