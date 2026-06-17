---
name: aws
description: AWS CLI and core service fundamentals — install/configure aws cli v2, credentials & profiles, SSO, IAM roles, and common S3/EC2/IAM/Lambda/CloudWatch operations. Use when running aws cli commands, configuring credentials or profiles, assuming IAM roles, doing SSO login, using --query JMESPath, or debugging AccessDenied / expired token / region errors.
---

# AWS CLI & Core Services

App-agnostic fundamentals for the AWS CLI v2 and the handful of services you touch daily. Read the reference that matches your task.

## References
- `references/cli.md` — install/configure aws cli v2, profiles, sso login, output formats, `--query` JMESPath, pagination, common service commands
- `references/auth.md` — credentials chain, `~/.aws/config`/`credentials`, IAM roles, `assume-role`, SSO, MFA, env vars, instance profiles
- `references/core-services.md` — S3, EC2, IAM, Lambda, CloudWatch Logs cheat-sheets
- `references/troubleshooting.md` — AccessDenied, expired token, region not set, throttling, `--debug`, `sts get-caller-identity`, resolution order

## Docs
- AWS CLI v2 install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- AWS CLI command reference: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/index.html
- Configuration & credentials: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html

## TL;DR
- Always pin a target with `--profile NAME` (or `AWS_PROFILE`) and `--region` — there is **no global default** unless you set one, and missing region fails fast.
- Resolution order for creds: CLI flags → env vars → `~/.aws/credentials` → `~/.aws/config` → SSO/role cache → container/instance metadata. First match wins.
- `aws sts get-caller-identity` is your "who am I" — run it first when anything auth-related looks wrong.
- SSO is session-based: `aws sso login --profile X`. **ExpiredToken** almost always means re-run the login, not a permissions problem.
- Server-side filter with `--query` (JMESPath) and shape output with `--output json|table|text`; never grep raw JSON when `--query` can do it.
- The CLI **auto-paginates by default** in v2 unless output is a pager-less pipe — use `--no-paginate` / `--max-items` / `--starting-token` to control it.
- Prefer **roles over long-lived keys**: `assume-role` (cross-account) or an instance profile (on EC2). If you see `aws_access_key_id` in a repo, that's a leak.
- `--debug` dumps the full request/credential-resolution trace — the single best tool for "why did it pick that account/region/identity".
