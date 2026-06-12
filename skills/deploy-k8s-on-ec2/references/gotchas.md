## Rolling update gotchas on small instances

**Default strategy fails on 2 GB instances:**

```yaml
# ❌ maxSurge:1 tries to schedule a 4th pod — no room on t3.small
rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }

# ✅ Take one down first, bring the replacement up
rollingUpdate: { maxSurge: 0, maxUnavailable: 1 }
```

**PDB traps the rollout:**

```yaml
# ❌ minAvailable: 2 with replicaCount: 2 — impossible to remove any pod
minAvailable: 2

# ✅ Allow one pod to be unavailable during the rollout
minAvailable: 1
```

**IMDS hop limit:** If pods need the EC2 instance role, set
`metadata_options { http_put_response_hop_limit = 2 }` in Terraform. kind pods are
one Docker hop from the host; the default limit of 1 silently blocks them.

---

## Verify

```bash
# over the SSH tunnel
kubectl get nodes              # control-plane + N workers, all Ready
kubectl get pods -A            # ingress-nginx, cert-manager, your app Running
curl -I https://<your-domain>  # HTTP/2 200, valid Let's Encrypt cert
```

## Teardown

```bash
cd infra/<cluster-name> && terraform destroy
# or run the provision workflow with action=destroy
```
