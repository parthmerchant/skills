## Two kinds of login — don't confuse them

GCP has two independent credential stores on your machine:

| Command | Authenticates | Used by |
|---|---|---|
| `gcloud auth login` | the **gcloud/gsutil/bq CLI** | gcloud commands |
| `gcloud auth application-default login` | **Application Default Credentials (ADC)** | your code / client libraries (Python, Go, Node SDKs), Terraform |

Logging in with one does **not** authenticate the other. Locally you typically run both.

```bash
gcloud auth login                          # CLI user creds (opens browser)
gcloud auth application-default login      # ADC for SDKs / Terraform

gcloud auth list                           # all accounts; * = active
gcloud config set account you@example.com  # switch active CLI account
gcloud auth revoke you@example.com         # log out
```

Docs: https://cloud.google.com/docs/authentication · https://cloud.google.com/sdk/gcloud/reference/auth/login

---

## Application Default Credentials (ADC) — resolution order

Client libraries (and `gcloud auth print-access-token` for ADC) look for credentials in this order:

1. `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to a key/credential JSON file
2. The ADC file from `gcloud auth application-default login`
   (`~/.config/gcloud/application_default_credentials.json`)
3. The **attached service account** of the resource (GCE VM, Cloud Run, GKE via Workload Identity, Cloud Functions) via the metadata server

```bash
# Print the ADC access token (what your SDKs will use)
gcloud auth application-default print-access-token

# Point ADC at a specific file (overrides everything above)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json

# Set the ADC quota/billing project (silences quota_project warnings)
gcloud auth application-default set-quota-project my-project-id
```

On GCP-hosted compute you usually need **no** local credentials — the metadata server provides them automatically (step 3).

Docs: https://cloud.google.com/docs/authentication/application-default-credentials

---

## Service accounts & keys — and why to avoid keys

Service accounts (SAs) are non-human identities. Exported **JSON keys are long-lived secrets** — they don't expire, are easy to leak (git, logs, images), and are the #1 source of GCP credential breaches. Prefer impersonation or Workload Identity Federation instead.

```bash
# Create an SA and grant it a role on a project
gcloud iam service-accounts create my-sa --display-name="My SA"
gcloud projects add-iam-policy-binding my-project-id \
  --member="serviceAccount:my-sa@my-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Create a key (avoid if you can) and activate it for the CLI
gcloud iam service-accounts keys create key.json \
  --iam-account=my-sa@my-project-id.iam.gserviceaccount.com
gcloud auth activate-service-account \
  --key-file=key.json    # makes the SA the active CLI account

# List / clean up keys
gcloud iam service-accounts keys list \
  --iam-account=my-sa@my-project-id.iam.gserviceaccount.com
```

Docs: https://cloud.google.com/iam/docs/service-accounts · https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys

---

## Impersonation — use a SA without downloading a key

Grant your user the **Service Account Token Creator** role on the target SA, then impersonate it. No key file, short-lived tokens, full audit trail.

```bash
# Grant yourself permission to impersonate the SA (one-time)
gcloud iam service-accounts add-iam-policy-binding \
  my-sa@my-project-id.iam.gserviceaccount.com \
  --member="user:you@example.com" \
  --role="roles/iam.serviceAccountTokenCreator"

# Impersonate for a single command
gcloud storage ls --impersonate-service-account=my-sa@my-project-id.iam.gserviceaccount.com

# Impersonate for ALL gcloud commands in this config
gcloud config set auth/impersonate_service_account \
  my-sa@my-project-id.iam.gserviceaccount.com

# Make ADC (your SDKs/Terraform) impersonate too
gcloud auth application-default login \
  --impersonate-service-account=my-sa@my-project-id.iam.gserviceaccount.com
```

Docs: https://cloud.google.com/iam/docs/service-account-impersonation · https://cloud.google.com/sdk/gcloud/reference/topic/configurations

---

## Workload Identity Federation — keyless auth from CI / external clouds

Lets GitHub Actions, AWS, or any OIDC provider get short-lived GCP tokens **without a key**. The external identity is mapped to a GCP SA via a workload identity pool/provider.

```bash
# Create a pool and an OIDC provider (example: GitHub Actions)
gcloud iam workload-identity-pools create gh-pool \
  --location=global --display-name="GitHub pool"

gcloud iam workload-identity-pools providers create-oidc gh-provider \
  --location=global --workload-identity-pool=gh-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"

# Let the external identity impersonate a GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  my-sa@my-project-id.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gh-pool/attribute.repository/my-org/my-repo"
```

In GitHub Actions, use `google-github-actions/auth` with the provider + SA — no `GOOGLE_APPLICATION_CREDENTIALS` secret needed.

Docs: https://cloud.google.com/iam/docs/workload-identity-federation · https://github.com/google-github-actions/auth

---

## GKE Workload Identity — keyless auth for pods

Bind a Kubernetes service account to a GCP SA so pods get GCP credentials via the metadata server (no key mounted).

```bash
gcloud iam service-accounts add-iam-policy-binding \
  my-sa@my-project-id.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:my-project-id.svc.id.goog[NAMESPACE/KSA_NAME]"
```

Docs: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity

## Docs
- Authentication overview: https://cloud.google.com/docs/authentication
- ADC: https://cloud.google.com/docs/authentication/application-default-credentials
- Service accounts: https://cloud.google.com/iam/docs/service-accounts
- Impersonation: https://cloud.google.com/iam/docs/service-account-impersonation
- Workload Identity Federation: https://cloud.google.com/iam/docs/workload-identity-federation
- `gcloud auth` reference: https://cloud.google.com/sdk/gcloud/reference/auth
