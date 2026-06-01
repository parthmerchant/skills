---
title: Diagnose Local kind Cluster
description: Full-context diagnostics and troubleshooting for the my-kind-cluster kind cluster — nodes, pods, apps, networking, and kind-specific gotchas.
icon: 🔬
tags: kubernetes, kind, debugging, data-platform
---

# Diagnose Local kind Cluster

Structured triage for the `kind-my-kind-cluster` Kubernetes cluster — a 1 control-plane + 2 worker kind cluster running a local Data Platform (Spark, MinIO, RAG, Loki/Grafana, OTel).

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

---

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

---

## Step 3 — networking

### Service reachability

```bash
# List all services
kubectl get svc -A
# Test from inside the cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -qO- http://minio.minio.svc.cluster.local:9000/minio/health/live
```

### Ingress (NGINX)

```bash
kubectl get ingress -A
kubectl get pods -n ingress-nginx
kubectl logs -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --tail=50
# Test locally (ingress binds to control-plane node's host port):
curl -H "Host: <hostname>" http://localhost/
```

### Port-forward not working

Stale port-forwards leave ghost processes. Kill them:

```bash
pkill -f "kubectl port-forward"
# Then restart: just pf-<app>
```

---

## Step 4 — kind-specific gotchas

| Gotcha | Fix |
|---|---|
| Images not found in pods | `kind load docker-image <img>:latest --name my-kind-cluster` |
| Ingress not routing | Controller must be on node with `ingress-ready=true` label — control-plane only |
| Port-forward drops | SSH keepalive not relevant here, but long `--wait` helm installs can stall; add `--timeout 5m` |
| Node disk pressure | `docker system prune` to recover space; kind stores layers in the Docker VM |
| Cluster gone after Docker restart | kind clusters don't survive Docker daemon restarts by default; `just setup` to rebuild |
| `kubectl` targeting wrong cluster | Run `kubectl config use-context kind-my-kind-cluster` |

---

## Step 5 — full cluster reset

If the cluster is beyond repair:

```bash
cd ~/PM/my-kind-cluster
just teardown      # deletes the kind cluster
just setup         # recreates cluster + operators + all apps (~10 min)
# or for the full UX:
just launch        # setup + port-forwards + open browsers
```

---

## Collecting a diagnostic bundle

When escalating an issue, gather:

```bash
# Save to a file for review
{
  echo "=== Context ==="
  kubectl config current-context
  echo "=== Nodes ==="
  kubectl get nodes -o wide
  echo "=== All Pods ==="
  kubectl get pods -A -o wide
  echo "=== Events (last 50) ==="
  kubectl get events -A --sort-by='.lastTimestamp' | tail -50
  echo "=== Resource usage ==="
  kubectl top nodes 2>/dev/null || echo "(metrics-server not installed)"
  kubectl top pods -A 2>/dev/null
} 2>&1 | tee /tmp/k8s-diag-$(date +%Y%m%d-%H%M%S).txt
```
