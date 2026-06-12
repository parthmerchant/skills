# AWS OIDC Setup for GitHub Actions

One-time setup per AWS account. Do this before writing any workflow.

## Option A — Terraform (recommended)

```hcl
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-<repo-slug>"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:<org>/<repo>:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

# Attach whatever policies the workflow needs, e.g.:
resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
```

## Option B — AWS CLI (one-shot)

```bash
# 1. Create the OIDC provider (once per account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# 2. Create the role with the trust policy
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
cat > trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::${ACCOUNT}:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:<org>/<repo>:*"
      },
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      }
    }
  }]
}
EOF

aws iam create-role --role-name github-actions-<repo-slug> --assume-role-policy-document file://trust.json
aws iam attach-role-policy --role-name github-actions-<repo-slug> \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess   # scope down for prod
rm trust.json
```

## GitHub secret to add

| Secret | Value |
|---|---|
| `AWS_ROLE_ARN` | `arn:aws:iam::<account-id>:role/github-actions-<repo-slug>` |

No `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` — OIDC tokens are short-lived and scoped to the run.

## Trust policy conditions

| Condition | Effect |
|---|---|
| `repo:<org>/<repo>:*` | Any branch or tag in the repo |
| `repo:<org>/<repo>:ref:refs/heads/main` | Main branch only (tightest for apply) |
| `repo:<org>/<repo>:pull_request` | PRs only (read-only plan role) |

Use separate roles for plan (read-only) and apply (write) if the repo has external contributors.
