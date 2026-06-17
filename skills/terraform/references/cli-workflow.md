## Core workflow

```bash
terraform init        # download providers/modules, configure backend (run first, and after backend/module changes)
terraform fmt -recursive   # canonical formatting (CI: terraform fmt -check)
terraform validate    # static checks: syntax, types, refs (no API calls)
terraform plan        # show proposed changes
terraform apply       # apply changes (prompts yes/no)
terraform destroy     # tear everything down
```

The safe, reviewable pattern (and the only correct one in CI):

```bash
terraform plan -out=plan.tfplan      # save the exact plan
terraform apply plan.tfplan          # apply precisely what was reviewed (no prompt)
```

```bash
terraform apply -auto-approve        # skip prompt (use only with a saved plan or in trusted automation)
terraform plan -destroy              # preview a destroy
```

---

## init flags

```bash
terraform init -upgrade                       # bump providers within version constraints
terraform init -reconfigure                   # ignore existing backend config, reinit
terraform init -migrate-state                 # move state when changing backends
terraform init -backend-config=prod.tfbackend # supply backend settings at init time
```

---

## fmt & validate

```bash
terraform fmt              # format files in cwd
terraform fmt -recursive   # include subdirectories
terraform fmt -check -diff # CI: fail if unformatted, show diff
terraform validate         # requires init first (needs provider schemas)
```

---

## Variables & tfvars

```bash
# -var (single), -var-file (a file), or env vars
terraform apply -var="region=us-east-1" -var="count=3"
terraform apply -var-file="prod.tfvars"
export TF_VAR_region=us-east-1        # env var form

# Auto-loaded without flags: terraform.tfvars, *.auto.tfvars
```

Precedence (low → high): env `TF_VAR_*` → `terraform.tfvars` → `*.auto.tfvars` (alphabetical) → `-var-file` → `-var`.

---

## Targeting (break-glass only)

```bash
terraform plan  -target=aws_instance.web
terraform apply -target=module.vpc           # apply only this module + its deps
terraform apply -replace=aws_instance.web    # force recreate one resource (replaces deprecated `taint`)
```

`-target` skips full dependency resolution and can leave state inconsistent — use to recover from a bad state, not as a routine workflow.

---

## Workspaces

```bash
terraform workspace list
terraform workspace new staging
terraform workspace select prod
terraform workspace show
# In config: terraform.workspace  =>  "prod"
```

Workspaces give multiple state instances from one config+backend. Good for ephemeral/identical envs; for prod vs staging with different settings, prefer **separate directories/state keys + tfvars** over relying on workspaces.

---

## Output

```bash
terraform output                   # all outputs
terraform output bucket_arn        # one value
terraform output -raw bucket_arn   # unquoted (for scripting)
terraform output -json | jq .      # machine-readable
```

---

## Provider lock file

```bash
# .terraform.lock.hcl records selected provider versions + checksums. COMMIT IT.
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_arm64        # add checksums for CI/other platforms
terraform providers             # show provider requirements tree
terraform init -upgrade         # update the lock file within constraints
```

Without all CI platforms in the lock file, `terraform init` in CI fails with a checksum mismatch. Run `providers lock` for every platform that will run Terraform.

---

## Docs
- CLI commands — https://developer.hashicorp.com/terraform/cli/commands
- init — https://developer.hashicorp.com/terraform/cli/commands/init
- plan — https://developer.hashicorp.com/terraform/cli/commands/plan
- apply — https://developer.hashicorp.com/terraform/cli/commands/apply
- fmt — https://developer.hashicorp.com/terraform/cli/commands/fmt
- validate — https://developer.hashicorp.com/terraform/cli/commands/validate
- Workspaces — https://developer.hashicorp.com/terraform/cli/workspaces
- Variables on the CLI — https://developer.hashicorp.com/terraform/language/values/variables#variables-on-the-command-line
- Dependency lock file — https://developer.hashicorp.com/terraform/language/files/dependency-lock
- Resource targeting — https://developer.hashicorp.com/terraform/cli/commands/plan#resource-targeting
