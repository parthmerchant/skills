---
name: terraform
description: Terraform / HCL infrastructure-as-code best practices — language syntax, state & remote backends, modules, CLI workflow, and troubleshooting. Use when writing or reviewing .tf files, running terraform plan/apply/init, configuring S3/DynamoDB or Terraform Cloud backends, authoring/consuming modules, importing resources, fixing state locks, drift, or provider auth errors.
---

# Terraform

App-agnostic, provider-agnostic fundamentals for Terraform and HCL. Read the reference that matches your task.

## References
- `references/language.md` — HCL: providers, resources, data sources, variables, outputs, locals, expressions, meta-arguments, functions
- `references/state.md` — state file, remote backends (S3+DynamoDB, Terraform Cloud), `terraform state` subcommands, import, drift, locking
- `references/modules.md` — authoring & consuming modules, sources, inputs/outputs, versioning, composition
- `references/cli-workflow.md` — init/plan/apply/destroy, fmt, validate, workspaces, targeting, tfvars, lock file
- `references/troubleshooting.md` — common errors, state locks, provider auth, TF_LOG debugging, dependency cycles

## TL;DR
- Always `terraform plan -out=plan.tfplan` then `terraform apply plan.tfplan` in CI — applying a saved plan is the only way to guarantee what you reviewed is what runs.
- **Pin everything**: provider versions in `required_providers`, module versions with `?ref=` or `version =`, and commit `.terraform.lock.hcl` to lock provider checksums.
- State holds **secrets in plaintext** — use a remote backend with encryption (S3 SSE) and locking (DynamoDB / native S3 lockfile / TFC); never commit `terraform.tfstate`.
- `count` vs `for_each`: prefer `for_each` (keyed by map/set) so adding/removing one item doesn't re-index and destroy unrelated resources.
- Never edit state by hand — use `terraform state mv/rm`, `import`, and `moved`/`removed` blocks so refactors don't destroy live infrastructure.
- `data` sources read existing infra at **plan time**; if a value isn't known until apply, the plan shows `(known after apply)` and may force downstream replacements.
- `-target` is a break-glass tool, not a workflow — it skips dependency resolution and leaves state partially applied.

## Docs
- Terraform docs — https://developer.hashicorp.com/terraform/docs
- Language reference — https://developer.hashicorp.com/terraform/language
- CLI commands — https://developer.hashicorp.com/terraform/cli/commands
- Registry (providers & modules) — https://registry.terraform.io
