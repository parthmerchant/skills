---
name: deploy-site
description: Deploy any static site to AWS — S3, CloudFront, GitHub Actions, Terraform. Runs locally from your laptop or fully automated in CI.
---

# Deploy Site to AWS

Private S3 bucket behind CloudFront, custom domain + TLS, two-pass cache — all defined in Terraform. Run locally or via GitHub Actions OIDC.

## References
- `references/infra.md` — prerequisites, inputs to gather, Terraform resources created
- `references/react-scaffold.md` — scaffold a Vite React SPA if you don't have a site yet
- `references/local-deploy.md` — Option A: deploy from your laptop
- `references/ci-deploy.md` — Option B: GitHub Actions OIDC workflow, verify, teardown

## TL;DR
- Gather 6 inputs: site bucket, state bucket, custom domain (optional), build command, build output folder, IAM role ARN.
- Two-pass upload: hashed assets with `immutable` cache; HTML with `must-revalidate`.
- Block all public S3 access; serve exclusively through CloudFront via OAC.
- Custom domain: ACM cert must be in `us-east-1`; DNS + cert propagation takes ~10 min on first apply.
