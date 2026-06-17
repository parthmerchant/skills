## What state is

Terraform records a mapping of config addresses → real resource IDs in `terraform.tfstate` (JSON). It is the source of truth for what Terraform manages. It contains **secrets in plaintext** (passwords, keys, generated values). Never commit it; always use an encrypted remote backend in a team.

```bash
terraform show               # human-readable current state
terraform show -json | jq .  # machine-readable
terraform state list         # all resource addresses in state
terraform state show aws_s3_bucket.logs   # one resource's attributes
```

---

## Remote backend: S3 + locking

```hcl
terraform {
  backend "s3" {
    bucket       = "my-tfstate-bucket"
    key          = "prod/network/terraform.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true          # native S3 lock (TF >= 1.10); no DynamoDB needed
  }
}
```

Pre-1.10 (or to keep DynamoDB locking), use a lock table instead of `use_lockfile`:

```hcl
backend "s3" {
  bucket         = "my-tfstate-bucket"
  key            = "prod/network/terraform.tfstate"
  region         = "us-west-2"
  encrypt        = true
  dynamodb_table = "terraform-locks"   # table with primary key "LockID" (String)
}
```

```bash
# One-time bootstrap of the lock table
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

Backend blocks **cannot use variables** — values are literals or passed via `terraform init -backend-config=...`.

---

## Remote backend: Terraform Cloud / HCP

```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces { name = "prod-network" }
  }
}
```

```bash
terraform login    # stores an API token in ~/.terraform.d/credentials.tfrc.json
```

TFC handles state storage, locking, and (optionally) remote runs automatically.

---

## `terraform state` subcommands

```bash
terraform state list                          # list addresses
terraform state show <addr>                   # inspect one resource
terraform state mv <src> <dst>                # rename/move (refactor without destroy)
terraform state mv aws_instance.web aws_instance.app
terraform state rm <addr>                      # forget a resource (stops managing it; does NOT delete it)
terraform state pull > backup.tfstate          # download remote state
terraform state push backup.tfstate            # upload (dangerous; last resort)
terraform state replace-provider \
  registry.terraform.io/-/aws hashicorp/aws    # repoint a provider source
```

Always `terraform state pull > backup` before surgery. Prefer `moved`/`removed` blocks (below) over imperative `state mv/rm` so the change is reviewable and reproducible.

---

## Importing existing infrastructure

Declarative `import` block (TF >= 1.5, runs on next plan/apply, generatable):

```hcl
import {
  to = aws_s3_bucket.logs
  id = "my-existing-bucket-name"
}
```

```bash
# Generate starter HCL for imported resources
terraform plan -generate-config-out=generated.tf
terraform apply

# Imperative form (writes state only; you must hand-write the resource HCL)
terraform import aws_s3_bucket.logs my-existing-bucket-name
terraform import 'aws_instance.web["a"]' i-0abc123   # for_each / count address
```

---

## Moving & removing resources via config

```hcl
# Rename a resource without destroy/recreate (replaces `terraform state mv`)
moved {
  from = aws_instance.web
  to   = aws_instance.app
}

# Stop managing a resource without destroying it (TF >= 1.7)
removed {
  from = aws_s3_bucket.old
  lifecycle { destroy = false }
}
```

These run during normal `apply`, are code-reviewed, and work in automation — preferred over imperative state commands.

---

## Drift & locking

```bash
# Detect drift: refresh state and show diffs without changing anything
terraform plan -refresh-only
terraform apply -refresh-only      # accept observed drift into state

# Force-unlock a stuck lock (only after confirming no run is active)
terraform force-unlock <LOCK_ID>
```

Drift = real infra changed outside Terraform. A plan reconciles config → desired; a `-refresh-only` plan reconciles state → reality. If someone's apply crashed, the lock may persist — get the `LOCK_ID` from the error and `force-unlock`.

---

## Docs
- State — https://developer.hashicorp.com/terraform/language/state
- Backend configuration — https://developer.hashicorp.com/terraform/language/backend
- S3 backend — https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform Cloud (`cloud` block) — https://developer.hashicorp.com/terraform/cli/cloud/settings
- `terraform state` — https://developer.hashicorp.com/terraform/cli/commands/state
- Import — https://developer.hashicorp.com/terraform/language/import
- `moved` block — https://developer.hashicorp.com/terraform/language/modules/develop/refactoring
- `removed` block — https://developer.hashicorp.com/terraform/language/resources/syntax#removing-resources
- State locking — https://developer.hashicorp.com/terraform/language/state/locking
