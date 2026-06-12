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
