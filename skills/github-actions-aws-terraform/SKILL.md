---
name: github-actions-aws-terraform
description: Wire up a GitHub Actions pipeline with AWS access via OIDC and optional Terraform. No long-lived credentials — the workflow assumes an IAM role directly.
---

# GitHub Actions + AWS + Terraform

OIDC-based AWS auth in GitHub Actions — no stored keys. Optional Terraform plan/apply pattern included.

## References
- `references/oidc.md` — one-time AWS setup: OIDC provider, IAM role, trust policy
- `references/workflow.md` — workflow templates for AWS auth and Terraform plan/apply

## TL;DR
- Use OIDC, not access keys — `aws-actions/configure-aws-credentials@v4` with `role-to-assume`.
- One-time per AWS account: create the OIDC provider + IAM role (Terraform or CLI).
- Store only the IAM role ARN as a GitHub secret (`AWS_ROLE_ARN`).
- Terraform: `plan` on PRs (post output as a comment), `apply` on push to `main`.
- Every job that calls AWS must have `permissions: { id-token: write, contents: read }`.
