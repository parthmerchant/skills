## What a module is

Any directory with `.tf` files is a module. The directory you run Terraform in is the **root module**; it calls **child modules** via `module` blocks. Modules package reusable, parameterized infra — inputs (`variable`), resources, and outputs (`output`).

---

## Authoring a module

```
modules/vpc/
├── main.tf        # resources
├── variables.tf   # inputs
├── outputs.tf     # outputs
├── versions.tf    # required_providers / required_version
└── README.md
```

```hcl
# modules/vpc/variables.tf
variable "cidr_block" {
  type        = string
  description = "VPC CIDR"
}
variable "azs" {
  type    = list(string)
  default = []
}

# modules/vpc/outputs.tf
output "vpc_id"     { value = aws_vpc.this.id }
output "subnet_ids" { value = aws_subnet.this[*].id }
```

A module should **declare its provider requirements** (`required_providers` in `versions.tf`) but **not** configure providers itself — pass configured providers from the root so the module stays reusable.

---

## Consuming a module

```hcl
module "vpc" {
  source     = "./modules/vpc"   # local path
  cidr_block = "10.0.0.0/16"
  azs        = ["us-west-2a", "us-west-2b"]
}

# Use its outputs downstream
resource "aws_instance" "web" {
  subnet_id = module.vpc.subnet_ids[0]
}
```

```bash
terraform init      # downloads/links modules; re-run after adding a module block
terraform get -update   # refresh module sources only
```

---

## Module sources

```hcl
# Local path
source = "./modules/vpc"

# Terraform Registry (namespace/name/provider) — pin with version
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.8"
}

# Generic git — pin to a tag/commit with ?ref=
source = "git::https://github.com/org/repo.git//modules/vpc?ref=v1.4.0"

# GitHub shorthand
source = "github.com/org/repo//modules/vpc?ref=v1.4.0"

# Git over SSH
source = "git::ssh://git@github.com/org/repo.git//modules/vpc?ref=v1.4.0"
```

`//` separates the repo from a **subdirectory**. `?ref=` takes a tag, branch, or commit SHA — always pin (a tag or SHA, never a moving branch) for reproducible builds. `version` only works for Registry sources, not git/local.

---

## Passing providers explicitly

```hcl
module "us_east_buckets" {
  source = "./modules/buckets"
  providers = {
    aws = aws.us_east   # map child's `aws` to root's aliased provider
  }
}
```

---

## for_each / count on modules

```hcl
module "service" {
  source   = "./modules/service"
  for_each = var.services            # map(object)
  name     = each.key
  config   = each.value
}
# module.service["api"].endpoint
```

---

## Composition best practices

- **Keep modules flat**: prefer composing several small modules in the root over deep module-in-module-in-module nesting (hard to trace, slow to refactor).
- **Don't over-modularize**: a module that wraps a single resource with no added value just adds indirection.
- **Inputs in, outputs out**: a child module should never reach into another module's resources — wire them through the root using outputs → inputs.
- **Version pin** every external module; bump deliberately and review the diff.
- **Stable interfaces**: treat variable/output names as a public API. Use `moved` blocks inside a module to refactor internal resource addresses without breaking consumers.
- **No hardcoded provider config** inside reusable modules; accept it from the caller.

---

## Docs
- Modules overview — https://developer.hashicorp.com/terraform/language/modules
- Module sources — https://developer.hashicorp.com/terraform/language/modules/sources
- Calling modules — https://developer.hashicorp.com/terraform/language/modules/syntax
- Developing modules — https://developer.hashicorp.com/terraform/language/modules/develop
- Providers within modules — https://developer.hashicorp.com/terraform/language/modules/develop/providers
- Module composition — https://developer.hashicorp.com/terraform/language/modules/develop/composition
- Public registry — https://registry.terraform.io/browse/modules
