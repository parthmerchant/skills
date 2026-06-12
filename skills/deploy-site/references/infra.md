## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Terraform | ≥ 1.9 | `brew install terraform` |
| AWS CLI | v2 | `aws configure` with an admin-ish profile for the first apply |
| Node | per project | for the build step |

One-time: create the Terraform state bucket (once per AWS account):

```bash
aws s3api create-bucket --bucket <tfstate-bucket> --region us-east-1
aws s3api put-bucket-versioning --bucket <tfstate-bucket> \
  --versioning-configuration Status=Enabled
```

## Ask the user (one at a time, conversationally)

1. **Site bucket name** — new S3 bucket for the built site (e.g. `my-site-assets`)
2. **Terraform state bucket** — the one created above
3. **Custom domain?** If yes: domain (e.g. `mysite.com`) + Route 53 hosted zone ID
4. **Build command** — default `npm run build`
5. **Build output folder** — default `build` (`dist`, `out`, …)
6. **IAM role ARN** — only needed for the GitHub Actions path (OIDC role)

## Create infra/

Write four Terraform files: `backend.tf`, `variables.tf`, `main.tf`, `outputs.tf`.

**What the infra creates:**
- Private S3 bucket (all public access blocked)
- CloudFront distribution pointing at the bucket via OAC (Origin Access Control) — the bucket never needs a public endpoint
- Custom error response: 404 → 200 `/index.html` (SPA routing)
- If custom domain: ACM cert in `us-east-1` with DNS validation via Route 53, A-aliases for apex and `www`, both `allow_overwrite = true` so re-runs don't conflict

State backend (`backend.tf`): state bucket provided by user, key `<site-bucket>/terraform.tfstate`.

Outputs: `site_bucket`, `cloudfront_distribution_id`, `cloudfront_domain`.
