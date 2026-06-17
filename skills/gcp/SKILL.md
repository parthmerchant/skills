---
name: gcp
description: Google Cloud Platform fundamentals via the gcloud CLI — auth, projects, configurations, and core services (GCS, Compute, GKE, Cloud Run, IAM, Logging). Use when running gcloud/gsutil/bq commands, authenticating with GCP (login, ADC, service accounts, impersonation), switching projects/accounts, deploying to Cloud Run/GKE, or debugging permission/quota/region errors.
---

# Google Cloud Platform (gcloud CLI)

App-agnostic fundamentals for operating GCP from the terminal. Read the reference that matches your task.

## References
- `references/gcloud-cli.md` — installing the Cloud SDK, `gcloud init`, configurations, projects, components, `--format`/`--filter`, gsutil/`gcloud storage`, `bq`
- `references/auth.md` — `gcloud auth login` vs `application-default login`, service accounts, impersonation, workload identity federation, ADC resolution order
- `references/core-services.md` — CLI cheat-sheet for GCS, Compute Engine, GKE, Cloud Run, IAM, Cloud Logging
- `references/troubleshooting.md` — permission/IAM errors, wrong project/account, quotas, ADC issues, region/zone defaults, `--verbosity=debug`, `--log-http`

## TL;DR
- **Two separate auth states:** `gcloud auth login` authenticates the *gcloud tool*; `gcloud auth application-default login` authenticates *your code/SDKs* (ADC). They are independent — you usually need both locally.
- **Avoid service account keys.** Prefer impersonation (`--impersonate-service-account`) locally and Workload Identity Federation in CI. Keys are long-lived secrets that leak.
- **Configurations isolate context.** `gcloud config configurations` holds account+project+region; switch with `gcloud config configurations activate <name>` instead of re-running `init`.
- **Most "permission denied" errors are wrong-project or wrong-account.** Check `gcloud config list` and the active account before debugging IAM.
- **`--format` and `--filter` are universal.** `--format='value(...)'` for scripting, `--filter` for server-side filtering on nearly every `list`/`describe` command.
- **Set defaults to skip prompts:** `gcloud config set compute/region` and `compute/zone`, or pass `--region`/`--zone` explicitly. Cloud Run, Compute, and GKE all need a location.
- **`gcloud storage` is the modern replacement for `gsutil`** — faster, same auth. Use it for new scripts.
- **Debug any command** with `--verbosity=debug` and `--log-http`; `gcloud info` dumps your full environment (SDK paths, active config, ADC).

## Docs
- gcloud CLI overview: https://cloud.google.com/sdk/docs
- gcloud reference: https://cloud.google.com/sdk/gcloud/reference
- Authentication overview: https://cloud.google.com/docs/authentication
