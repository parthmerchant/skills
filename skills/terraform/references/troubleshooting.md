## Debugging with TF_LOG

```bash
export TF_LOG=DEBUG          # TRACE | DEBUG | INFO | WARN | ERROR
export TF_LOG_PATH=tf.log    # write logs to a file
export TF_LOG_PROVIDER=TRACE # provider-only logs (separate from core)
terraform apply
unset TF_LOG                 # noisy — turn it back off
```

`TRACE` shows full RPCs to provider plugins (API requests/responses) — the level to use for "why did it decide to replace this resource".

---

## State lock errors

```
Error: Error acquiring the state lock
Lock Info: ID: 1a2b3c..., Who: user@host, Created: ...
```

A previous run crashed or another run is in progress.

```bash
# Confirm no live run, then unlock with the ID from the message
terraform force-unlock 1a2b3c-...
# DynamoDB backend: inspect/delete the stale lock item if force-unlock fails
aws dynamodb scan --table-name terraform-locks
```

Never `force-unlock` while a real apply is running — you'll corrupt state.

---

## Provider authentication

```bash
# AWS — order: env vars > shared config/credentials > IAM role/instance profile
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_REGION=us-west-2
export AWS_PROFILE=prod
aws sts get-caller-identity        # verify creds resolve before blaming Terraform

# "No valid credential sources" / "operation error STS" => creds not found/expired
```

Auth lives in the **provider/SDK**, not Terraform. Validate with the cloud's own CLI (`aws sts get-caller-identity`, `gcloud auth list`, `az account show`) first. For assumed roles, set the role in the provider block or via `AWS_PROFILE`.

---

## Dependency cycles

```
Error: Cycle: aws_security_group.a, aws_security_group.b
```

Two resources reference each other directly. Break it by extracting the cross-reference into a separate rule resource:

```hcl
# Instead of each SG referencing the other inline, use standalone rules:
resource "aws_security_group" "a" {}
resource "aws_security_group" "b" {}

resource "aws_vpc_security_group_ingress_rule" "a_from_b" {
  security_group_id            = aws_security_group.a.id
  referenced_security_group_id = aws_security_group.b.id
}
```

Visualize the graph to find the loop:

```bash
terraform graph | dot -Tsvg > graph.svg
```

---

## "(known after apply)" forcing replacement

A value computed at apply time (e.g. a new resource's ID) feeds an attribute that forces replacement of a downstream resource. Plan shows `# forces replacement`. Fixes: depend on a stable attribute (ARN/name you set, not a generated ID), or add `lifecycle { create_before_destroy = true }` to avoid downtime, or `ignore_changes` if the churn is benign.

---

## Common errors

```
Error: Inconsistent dependency lock file
```
Lock file lacks a provider/platform. Fix: `terraform init -upgrade`, and `terraform providers lock -platform=linux_amd64 ...` for every CI platform; commit `.terraform.lock.hcl`.

```
Error: Reference to undeclared resource / Invalid index
```
Typo in address, or a `count`/`for_each` resource referenced without `[index]`/`[key]`.

```
Error: Provider configuration not present
```
A resource still in state has no matching provider after a refactor. Fix with `terraform state replace-provider` or re-add the provider block.

```
Error: value depends on resource attributes that cannot be determined until apply
```
You used an unknown (apply-time) value in `count`/`for_each`. These must be known at plan time — key off static input variables, not computed attributes.

```
Error: Saved plan is stale
```
State changed between `plan -out` and `apply <file>`. Re-run plan.

```
Error: Provider produced inconsistent final plan
```
Usually a provider bug or version skew. Try `terraform init -upgrade` to a patched provider; check the provider's GitHub issues.

---

## Recovery checklist

```bash
terraform state pull > backup.tfstate   # ALWAYS back up before surgery
terraform plan -refresh-only            # see drift vs reality without changing infra
terraform plan -out=plan.tfplan         # capture the exact intended change
terraform apply plan.tfplan
terraform force-unlock <ID>             # only when certain no run is active
```

---

## Docs
- Debugging / TF_LOG — https://developer.hashicorp.com/terraform/internals/debugging
- Environment variables — https://developer.hashicorp.com/terraform/cli/config/environment-variables
- force-unlock — https://developer.hashicorp.com/terraform/cli/commands/force-unlock
- graph — https://developer.hashicorp.com/terraform/cli/commands/graph
- replace-provider — https://developer.hashicorp.com/terraform/cli/commands/state/replace-provider
- Dependency lock file — https://developer.hashicorp.com/terraform/language/files/dependency-lock
- AWS provider auth — https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration
