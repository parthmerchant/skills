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
