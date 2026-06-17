## First move: confirm WHO and WHERE you are

Most failures are wrong-account or wrong-project, not real IAM problems. Always check this first.

```bash
gcloud config list           # active account, project, region/zone, impersonation
gcloud auth list             # all credentialed accounts; * = active
gcloud info                  # full env: SDK paths, active config, ADC, properties
```

```bash
gcloud config set account you@example.com
gcloud config set project my-project-id
gcloud config configurations activate prod
```

---

## PERMISSION_DENIED / 403 — IAM

The error message names the **missing permission** and the **identity** that lacked it — read it carefully.

```bash
# Is the API even enabled? (403s often mean "service disabled")
gcloud services list --enabled --filter='config.name:run.googleapis.com'
gcloud services enable run.googleapis.com

# What roles does the failing identity hold?
gcloud projects get-iam-policy my-project-id \
  --flatten='bindings[].members' \
  --filter='bindings.members:you@example.com' \
  --format='value(bindings.role)'

# Which role grants the permission you need?
gcloud iam roles describe roles/storage.objectAdmin

# Grant it
gcloud projects add-iam-policy-binding my-project-id \
  --member="user:you@example.com" --role="roles/storage.objectAdmin"
```

If impersonating, the **token-creator** role is granted on the *SA*, while the SA needs the *resource* role — two separate bindings.

Docs: https://cloud.google.com/iam/docs/troubleshooting-access

---

## Wrong project / wrong account

```bash
# Commands hit the wrong project? The active config project is used unless overridden.
gcloud config get-value project
gcloud <command> --project=other-project       # one-off override
gcloud <command> --account=other@example.com   # one-off account override

# CLI account != ADC account is normal — they're separate (see auth.md).
gcloud auth list                                       # CLI account
gcloud auth application-default print-access-token     # ADC account
```

---

## Quota / RESOURCE_EXHAUSTED errors

```bash
# 429 / quota errors. Inspect and request increases via Console.
gcloud compute regions describe us-central1 \
  --format='table(quotas.metric, quotas.usage, quotas.limit)'

# "quota project" warnings from ADC: set a billing/quota project
gcloud auth application-default set-quota-project my-project-id
```

Quota increases are requested in the Console (IAM & Admin → Quotas) — there's no instant CLI bump.

Docs: https://cloud.google.com/docs/quotas/view-manage

---

## ADC issues (SDKs / Terraform can't authenticate)

```bash
# "Could not automatically determine credentials" / "default credentials were not found"
gcloud auth application-default login

# Is GOOGLE_APPLICATION_CREDENTIALS pointing somewhere stale?
echo $GOOGLE_APPLICATION_CREDENTIALS
unset GOOGLE_APPLICATION_CREDENTIALS    # fall back to gcloud ADC file

# Verify what ADC resolves to
gcloud auth application-default print-access-token
```

Resolution order (env var → ADC file → metadata server) is in `auth.md`. A leftover env var beats your `application-default login`.

Docs: https://cloud.google.com/docs/authentication/application-default-credentials

---

## Region / zone defaults

```bash
# "required argument --zone not specified" → set a default or pass it
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

# Resource not found is often a region mismatch — list across regions
gcloud run services list                  # omit --region to scan all? no: pass each
gcloud compute instances list             # global list shows zone per row
```

Cloud Run/GKE regional clusters need `--region`; zonal resources need `--zone`. Missing-location errors almost always mean an unset default.

---

## Deep debugging

```bash
# Verbose internals (auth attempts, retries, resolution)
gcloud <command> --verbosity=debug

# Dump the raw HTTP request/response to the API (headers, body, status)
gcloud <command> --log-http

# Combine for maximum signal
gcloud compute instances list --verbosity=debug --log-http

# Where are logs/config stored?
gcloud info --show-log         # prints the path to the last command log
gcloud info                    # config dir, ADC path, active properties
```

`--log-http` is the fastest way to see the exact 403/404 the API returned and the project/headers gcloud actually sent.

Docs: https://cloud.google.com/sdk/gcloud/reference#--verbosity · https://cloud.google.com/sdk/gcloud/reference#--log-http

## Docs
- Troubleshooting access (IAM): https://cloud.google.com/iam/docs/troubleshooting-access
- View & manage quotas: https://cloud.google.com/docs/quotas/view-manage
- ADC: https://cloud.google.com/docs/authentication/application-default-credentials
- gcloud global flags: https://cloud.google.com/sdk/gcloud/reference
- `gcloud info`: https://cloud.google.com/sdk/gcloud/reference/info
