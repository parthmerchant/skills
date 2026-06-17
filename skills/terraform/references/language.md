## Block types & terraform settings

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"   # registry: namespace/name
      version = "~> 5.40"         # >= 5.40.0, < 6.0.0
    }
  }
}

provider "aws" {
  region = var.region
}

# A second, aliased provider instance (multi-region)
provider "aws" {
  alias  = "us_east"
  region = "us-east-1"
}
```

`~> 5.40` allows patch+minor up to (not incl.) `6.0`; `~> 5.40.1` allows only patch. Reference an aliased provider with `provider = aws.us_east` on a resource.

---

## Resources & data sources

```hcl
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs"
  tags   = local.common_tags
}

# Data source: read something that already exists (resolved at plan time)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
}
```

Reference syntax: `aws_s3_bucket.logs.arn` (resource), `data.aws_ami.ubuntu.id` (data source). The address `aws_s3_bucket.logs` is what lives in state.

---

## Variables, outputs, locals

```hcl
variable "region" {
  type        = string
  default     = "us-west-2"
  description = "AWS region"
}

variable "instance_count" {
  type    = number
  default = 2
  validation {
    condition     = var.instance_count > 0
    error_message = "instance_count must be positive."
  }
}

variable "db_password" {
  type      = string
  sensitive = true   # redacted from CLI output (still plaintext in state)
}

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  common_tags = merge(var.tags, {
    project   = var.project
    managedBy = "terraform"
  })
}

output "bucket_arn" {
  value       = aws_s3_bucket.logs.arn
  description = "ARN of the logs bucket"
}

output "db_password" {
  value     = var.db_password
  sensitive = true   # required, else apply errors when emitting a sensitive value
}
```

Set variables (highest precedence last): defaults → env `TF_VAR_region` → `terraform.tfvars` / `*.auto.tfvars` → `-var-file` → `-var` flag.

---

## Expressions

```hcl
# Conditional (ternary)
instance_type = var.env == "prod" ? "m5.large" : "t3.micro"

# String interpolation & heredoc
name = "${var.project}-${var.env}"
policy = <<-EOT
  { "Version": "2012-10-17" }
EOT

# for expressions
ids   = [for s in aws_subnet.this : s.id]          # list
bymap = { for s in aws_subnet.this : s.az => s.id } # map
big   = [for n in var.names : upper(n) if length(n) > 3]

# Splat
all_ids = aws_instance.web[*].id

# Null coalescing & optional object attrs
port = coalesce(var.port, 8080)
```

---

## Meta-arguments

```hcl
# count — index-based; good for a fixed number of identical things
resource "aws_instance" "web" {
  count         = var.instance_count
  instance_type = "t3.micro"
  tags = { Name = "web-${count.index}" }
}
# referenced as aws_instance.web[0], or aws_instance.web[*].id

# for_each — keyed; preferred so removing one item doesn't reindex others
resource "aws_iam_user" "team" {
  for_each = toset(["alice", "bob"])
  name     = each.key
}
resource "aws_subnet" "this" {
  for_each          = var.subnets          # map(string) => cidr
  cidr_block        = each.value
  availability_zone = each.key
}
# referenced as aws_subnet.this["us-west-2a"]

# depends_on — explicit ordering when there's no reference dependency
resource "aws_instance" "app" {
  depends_on = [aws_iam_role_policy.app]
}

# lifecycle
resource "aws_db_instance" "main" {
  lifecycle {
    prevent_destroy       = true             # block accidental deletion
    create_before_destroy = true             # avoid downtime on replace
    ignore_changes        = [tags["LastSeen"]]
  }
}
```

`count` and `for_each` are mutually exclusive on one resource. Switching a resource between them (or changing `count` mid-list) re-indexes addresses and can destroy/recreate — use `moved` blocks to migrate.

---

## Functions (common ones)

```hcl
merge(a, b)                       # combine maps; b wins on conflict
concat(list1, list2)              # join lists
lookup(map, "key", "default")     # safe map access
try(local.maybe.value, "fallback")# first non-erroring expression
coalesce(a, b, c)                 # first non-null
join(",", list)  / split(",", s)  # list <-> string
jsonencode(obj)  / jsondecode(s)  # JSON (great for IAM policies)
file("${path.module}/p.json")     # read file contents
templatefile("u.tftpl", { x = 1 })# render a template with vars
cidrsubnet("10.0.0.0/16", 8, 2)   # => 10.0.2.0/24
format("%s-%03d", name, n)        # printf-style
```

Test any function in the REPL: `terraform console`, then type `merge({a=1},{b=2})`.

---

## Docs
- Language overview — https://developer.hashicorp.com/terraform/language
- Resources — https://developer.hashicorp.com/terraform/language/resources
- Data sources — https://developer.hashicorp.com/terraform/language/data-sources
- Variables — https://developer.hashicorp.com/terraform/language/values/variables
- Outputs — https://developer.hashicorp.com/terraform/language/values/outputs
- Locals — https://developer.hashicorp.com/terraform/language/values/locals
- Expressions — https://developer.hashicorp.com/terraform/language/expressions
- Meta-arguments (for_each) — https://developer.hashicorp.com/terraform/language/meta-arguments/for_each
- lifecycle — https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle
- Built-in functions — https://developer.hashicorp.com/terraform/language/functions
