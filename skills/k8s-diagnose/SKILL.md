---
name: k8s-diagnose
description: Full-context diagnostics and troubleshooting for the my-kind-cluster kind cluster — nodes, pods, apps, networking, and kind-specific gotchas.
---

# Diagnose Local kind Cluster

Structured triage for `kind-my-kind-cluster` — 1 control-plane + 2 workers running Spark, MinIO, RAG, Loki/Grafana, OTel.

## References
- `references/cluster.md` — cluster topology, namespace map, justfile shortcuts
- `references/triage.md` — step-by-step: confirm context, pod states, exit codes, app-specific diagnostics
- `references/networking.md` — service reachability, ingress, port-forward cleanup
- `references/kind-gotchas.md` — kind-specific pitfalls, cluster reset, diagnostic bundle

## TL;DR
- Confirm context first: `kubectl config current-context` must be `kind-my-kind-cluster`.
- Images must be loaded into kind explicitly — they are NOT pulled from the local Docker daemon.
- OOMKilled: scale down Ollama first (largest consumer in the `rag` namespace).
- Stale port-forwards: `pkill -f "kubectl port-forward"`, then restart.
- Full reset: `just teardown && just setup` (~10 min).
