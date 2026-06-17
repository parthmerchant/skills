## Cloud Storage (GCS)

```bash
gcloud storage buckets create gs://my-bucket --location=us-central1
gcloud storage ls gs://my-bucket
gcloud storage cp ./file.txt gs://my-bucket/
gcloud storage cp -r ./dir gs://my-bucket/dir
gcloud storage rsync ./local gs://my-bucket/remote
gcloud storage rm gs://my-bucket/old.txt

# Make an object public (uniform bucket-level access must allow it)
gcloud storage objects update gs://my-bucket/file.txt \
  --add-acl-grant=entity=allUsers,role=READER

# Signed URL (temporary access without IAM) — needs a key or impersonation
gcloud storage sign-url gs://my-bucket/file.txt --duration=1h
```

Docs: https://cloud.google.com/storage/docs · https://cloud.google.com/sdk/gcloud/reference/storage

---

## Compute Engine

```bash
gcloud compute instances list
gcloud compute instances create my-vm \
  --zone=us-central1-a --machine-type=e2-medium \
  --image-family=debian-12 --image-project=debian-cloud
gcloud compute ssh my-vm --zone=us-central1-a
gcloud compute instances stop my-vm --zone=us-central1-a
gcloud compute instances delete my-vm --zone=us-central1-a

# Firewall + serial console for debugging
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 --direction=INGRESS
gcloud compute instances get-serial-port-output my-vm --zone=us-central1-a
```

Docs: https://cloud.google.com/compute/docs · https://cloud.google.com/sdk/gcloud/reference/compute

---

## GKE (Kubernetes Engine)

`get-credentials` writes a kubeconfig entry so `kubectl` talks to the cluster. Requires the `gke-gcloud-auth-plugin` component.

```bash
gcloud components install gke-gcloud-auth-plugin   # one-time

gcloud container clusters list
gcloud container clusters create my-cluster \
  --zone=us-central1-a --num-nodes=3

# Wire kubectl to the cluster
gcloud container clusters get-credentials my-cluster --zone=us-central1-a
kubectl get nodes

# Regional cluster uses --region instead of --zone
gcloud container clusters get-credentials my-cluster --region=us-central1
```

Docs: https://cloud.google.com/kubernetes-engine/docs · https://cloud.google.com/sdk/gcloud/reference/container/clusters/get-credentials

---

## Cloud Run

```bash
# Deploy from source (Cloud Build builds the container)
gcloud run deploy my-svc \
  --source=. --region=us-central1 --allow-unauthenticated

# Deploy a prebuilt image
gcloud run deploy my-svc \
  --image=us-docker.pkg.dev/my-project/repo/img:tag \
  --region=us-central1

gcloud run services list --region=us-central1
gcloud run services describe my-svc --region=us-central1 \
  --format='value(status.url)'

# Env vars, scaling, service account
gcloud run deploy my-svc --region=us-central1 \
  --set-env-vars=KEY=val --min-instances=0 --max-instances=10 \
  --service-account=my-sa@my-project-id.iam.gserviceaccount.com

# Stream logs
gcloud run services logs read my-svc --region=us-central1
```

Docs: https://cloud.google.com/run/docs · https://cloud.google.com/sdk/gcloud/reference/run

---

## IAM

IAM grants are `member` + `role` on a `resource` (project/bucket/SA/etc).

```bash
# See who has what on a project
gcloud projects get-iam-policy my-project-id

# Grant / revoke a role
gcloud projects add-iam-policy-binding my-project-id \
  --member="user:you@example.com" --role="roles/viewer"
gcloud projects remove-iam-policy-binding my-project-id \
  --member="user:you@example.com" --role="roles/viewer"

# Member prefixes: user: serviceAccount: group: domain:

# Discover roles and what permissions they include
gcloud iam roles list --filter='name:roles/storage'
gcloud iam roles describe roles/storage.objectViewer

# Custom role
gcloud iam roles create myViewer --project=my-project-id \
  --permissions=storage.objects.get,storage.objects.list
```

Docs: https://cloud.google.com/iam/docs · https://cloud.google.com/sdk/gcloud/reference/projects/add-iam-policy-binding

---

## Cloud Logging

```bash
# Read recent logs (Logging query language in --log-filter)
gcloud logging read 'severity>=ERROR' --limit=20 --freshness=1h
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="my-svc"' \
  --limit=50 --format='value(textPayload)'

# Tail in (near) real time
gcloud logging tail 'resource.type="gce_instance"'

# Write a test log entry
gcloud logging write my-log "hello" --severity=INFO

gcloud logging logs list
```

Docs: https://cloud.google.com/logging/docs · https://cloud.google.com/logging/docs/view/logging-query-language

## Docs
- Cloud Storage: https://cloud.google.com/storage/docs
- Compute Engine: https://cloud.google.com/compute/docs
- GKE: https://cloud.google.com/kubernetes-engine/docs
- Cloud Run: https://cloud.google.com/run/docs
- IAM: https://cloud.google.com/iam/docs
- Cloud Logging: https://cloud.google.com/logging/docs
