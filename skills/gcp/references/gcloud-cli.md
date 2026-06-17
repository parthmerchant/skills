## Install the Cloud SDK (gcloud CLI)

```bash
# macOS / Linux — interactive installer
curl https://sdk.cloud.google.com | bash
exec -l $SHELL          # reload PATH

# macOS Homebrew
brew install --cask google-cloud-sdk

# Debian/Ubuntu (apt) — see docs link below for the apt-key/repo steps
sudo apt-get install google-cloud-cli

# Verify
gcloud version
gcloud info                 # full env dump: paths, active config, ADC
```

Docs: https://cloud.google.com/sdk/docs/install

---

## gcloud init — first-time setup

```bash
gcloud init               # interactive: pick account, project, default region/zone
gcloud init --console-only   # for headless/SSH machines (prints a URL to paste)
```

`init` ties together an account, a project, and a *configuration*. Re-run it to add another account/config, or just use the `config` commands below.

---

## Configurations — isolate account + project + region

A configuration is a named bundle of properties (account, project, region, zone). Use one per environment (dev/prod) or per client.

```bash
gcloud config configurations list
gcloud config configurations create prod
gcloud config configurations activate prod
gcloud config configurations describe prod

# Set properties on the ACTIVE config
gcloud config set account you@example.com
gcloud config set project my-project-id
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a

gcloud config list                  # show active config
gcloud config get-value project     # read one property
gcloud config unset compute/zone
```

One-off override without switching configs: `--configuration=prod` on any command.

Docs: https://cloud.google.com/sdk/docs/configurations

---

## Projects

```bash
gcloud projects list
gcloud config set project my-project-id
gcloud projects describe my-project-id

# Resolve a project NUMBER (needed for some APIs/WIF) from its ID
gcloud projects describe my-project-id --format='value(projectNumber)'

# Enable an API/service before using it
gcloud services list --enabled
gcloud services enable run.googleapis.com compute.googleapis.com
```

Docs: https://cloud.google.com/sdk/gcloud/reference/projects

---

## Components — keep the SDK and add-ons updated

```bash
gcloud components list
gcloud components update
gcloud components install gke-gcloud-auth-plugin   # required for kubectl + GKE
gcloud components install beta alpha
```

If installed via apt/Homebrew, `components update` may be disabled — update via the package manager instead.

Docs: https://cloud.google.com/sdk/docs/components

---

## --format — shape any output

```bash
gcloud compute instances list --format=json
gcloud compute instances list --format=yaml

# Tables: pick columns
gcloud compute instances list --format='table(name, zone, status)'

# value() — bare values, perfect for scripts / command substitution
gcloud compute instances list --format='value(name)'
PROJECT=$(gcloud config get-value project)

# CSV, flattened nested fields, sort
gcloud compute instances list --format='csv(name,zone,status)'
gcloud projects list --format='table(projectId, name)' --sort-by=projectId
```

Docs: https://cloud.google.com/sdk/gcloud/reference/topic/formats

---

## --filter — server-side filtering

```bash
# Filter is evaluated server-side where supported (cheaper than grep)
gcloud compute instances list --filter='status=RUNNING'
gcloud compute instances list --filter='zone:us-central1-a AND status=RUNNING'
gcloud compute instances list --filter='name~^web-'     # ~ is regex match
gcloud projects list --filter='projectId:my-*'

# Combine with format for clean scripting
gcloud compute instances list \
  --filter='status=RUNNING' --format='value(name)'
```

Docs: https://cloud.google.com/sdk/gcloud/reference/topic/filters

---

## gcloud compute — VMs, disks, networks

```bash
gcloud compute instances list
gcloud compute instances describe my-vm --zone=us-central1-a
gcloud compute instances create my-vm \
  --zone=us-central1-a --machine-type=e2-medium --image-family=debian-12 \
  --image-project=debian-cloud
gcloud compute ssh my-vm --zone=us-central1-a
gcloud compute instances stop my-vm --zone=us-central1-a
gcloud compute instances delete my-vm --zone=us-central1-a

gcloud compute zones list
gcloud compute machine-types list --filter='zone:us-central1-a'
```

Docs: https://cloud.google.com/sdk/gcloud/reference/compute

---

## gcloud storage / gsutil — Cloud Storage

`gcloud storage` is the modern, faster CLI; `gsutil` still works and shares auth. Prefer `gcloud storage` for new work.

```bash
# gcloud storage (modern)
gcloud storage buckets create gs://my-bucket --location=us-central1
gcloud storage ls
gcloud storage ls gs://my-bucket
gcloud storage cp ./file.txt gs://my-bucket/
gcloud storage cp -r ./dir gs://my-bucket/dir
gcloud storage rsync ./local gs://my-bucket/remote
gcloud storage rm gs://my-bucket/file.txt

# gsutil (legacy equivalents)
gsutil mb -l us-central1 gs://my-bucket
gsutil ls -r gs://my-bucket
gsutil cp file.txt gs://my-bucket/
gsutil -m rsync -r ./local gs://my-bucket/remote   # -m = parallel
```

Docs: https://cloud.google.com/sdk/gcloud/reference/storage · https://cloud.google.com/storage/docs/gsutil

---

## bq — BigQuery CLI

```bash
bq ls                                   # datasets in current project
bq ls my_dataset                        # tables in a dataset
bq mk --dataset my_project:my_dataset
bq show my_dataset.my_table

# Standard SQL query
bq query --use_legacy_sql=false \
  'SELECT name, count(*) c FROM `my_dataset.events` GROUP BY name ORDER BY c DESC LIMIT 10'

# Load / extract
bq load --source_format=CSV my_dataset.t gs://my-bucket/data.csv schema.json
bq extract my_dataset.t gs://my-bucket/out-*.csv
```

Docs: https://cloud.google.com/bigquery/docs/bq-command-line-tool

---

## Common patterns

```bash
# Who/what am I right now?
gcloud config list
gcloud auth list                  # accounts; * marks active

# Scripted project + token for raw API calls
PROJECT=$(gcloud config get-value project)
TOKEN=$(gcloud auth print-access-token)
curl -H "Authorization: Bearer $TOKEN" \
  "https://cloudresourcemanager.googleapis.com/v1/projects/$PROJECT"

# Run a command against another config without switching
gcloud compute instances list --configuration=prod

# Skip interactive prompts in scripts
gcloud compute instances delete my-vm --zone=us-central1-a --quiet
```

## Docs
- gcloud CLI overview: https://cloud.google.com/sdk/docs
- Full command reference: https://cloud.google.com/sdk/gcloud/reference
- Install guide: https://cloud.google.com/sdk/docs/install
- Configurations: https://cloud.google.com/sdk/docs/configurations
- Output formats: https://cloud.google.com/sdk/gcloud/reference/topic/formats
- Filters: https://cloud.google.com/sdk/gcloud/reference/topic/filters
