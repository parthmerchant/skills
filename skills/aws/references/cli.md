# AWS CLI v2

The single binary for driving every AWS service from the terminal. v2 is the current major version — install it, don't `pip install awscli`.

## Docs
- Install/update v2: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Full command reference: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/index.html
- `--query` / JMESPath: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html
- Output & pagination: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html

---

## Install & verify

```bash
# macOS
brew install awscli
# or official pkg
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Linux (x86_64)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

aws --version          # expect: aws-cli/2.x.x ...
```

---

## Configure

```bash
# Interactive: writes ~/.aws/credentials + ~/.aws/config (default profile)
aws configure

# A named profile
aws configure --profile prod

# Read/write single values without the wizard
aws configure get region --profile prod
aws configure set region us-east-1 --profile prod
aws configure set output json --profile prod

# List what's resolved and where it came from
aws configure list
aws configure list-profiles
```

`~/.aws/config` holds non-secret settings (region, output, sso, role_arn). `~/.aws/credentials` holds `aws_access_key_id` / `aws_secret_access_key`. See `references/auth.md` for the full file format.

---

## SSO login (IAM Identity Center)

```bash
# One-time: configure an SSO-backed profile
aws configure sso --profile dev

# Each session (creds expire — re-run when you hit ExpiredToken)
aws sso login --profile dev

# Logout / clear cached session
aws sso logout
```

---

## Selecting profile & region

```bash
# Per-command flags (highest precedence)
aws s3 ls --profile prod --region us-west-2

# Or via environment for the whole shell
export AWS_PROFILE=prod
export AWS_REGION=us-west-2      # AWS_DEFAULT_REGION also works
aws s3 ls
```

---

## Output formats

```bash
aws ec2 describe-instances --output json     # default; machine-readable
aws ec2 describe-instances --output table    # human-friendly grid
aws ec2 describe-instances --output text     # tab-separated; great for scripts
aws ec2 describe-instances --output yaml     # yaml

# Force/disable color and pager
aws s3 ls --no-cli-pager
export AWS_PAGER=""              # disable the pager globally
```

---

## `--query` (JMESPath) — filter server response client-side

```bash
# Pluck specific fields into a flat list
aws ec2 describe-instances \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType]' \
  --output table

# Filter with a predicate
aws ec2 describe-instances \
  --query "Reservations[].Instances[?State.Name=='running'].InstanceId" \
  --output text

# Project into named keys (objects)
aws s3api list-buckets \
  --query 'Buckets[].{name:Name,created:CreationDate}' --output table

# Single scalar
aws sts get-caller-identity --query Account --output text
```

`--query` runs **after** the response returns. Use service-native `--filters` (e.g. on `ec2 describe-instances`) to filter at the API and reduce data transfer.

---

## Pagination

```bash
# v2 auto-paginates and pipes through a pager. Control it:
aws s3api list-objects-v2 --bucket my-bucket --no-paginate     # one page only
aws s3api list-objects-v2 --bucket my-bucket --max-items 100   # cap results
aws s3api list-objects-v2 --bucket my-bucket --page-size 50    # API page size

# Manual paging with tokens
aws s3api list-objects-v2 --bucket my-bucket --max-items 100 \
  --query 'NextToken' --output text
aws s3api list-objects-v2 --bucket my-bucket --starting-token "$TOKEN"
```

---

## Common service one-liners

```bash
# STS — who am I
aws sts get-caller-identity

# S3 (high-level)
aws s3 ls
aws s3 cp ./file.txt s3://my-bucket/path/
aws s3 sync ./dist s3://my-bucket/ --delete

# EC2
aws ec2 describe-instances --query 'Reservations[].Instances[].InstanceId' --output text
aws ec2 start-instances --instance-ids i-0abc123

# IAM
aws iam list-users
aws iam get-user

# Lambda
aws lambda list-functions --query 'Functions[].FunctionName' --output text
aws lambda invoke --function-name my-fn --payload '{}' /tmp/out.json

# CloudWatch Logs
aws logs tail /aws/lambda/my-fn --follow
```

See `references/core-services.md` for fuller per-service recipes.
