## Option B — Run it in GitHub Actions

For this path you need an IAM role GitHub can assume via OIDC (no stored keys).
Create `.github/workflows/deploy.yml`:

```yaml
name: deploy
on:
  push: { branches: [main, master] }
  workflow_dispatch:
concurrency: { group: deploy, cancel-in-progress: false }
permissions: { id-token: write, contents: read }
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci && npm run build
      - uses: hashicorp/setup-terraform@v3
        with: { terraform_version: 1.9.5 }
      - name: Apply infra
        working-directory: infra
        run: |
          terraform init -input=false
          terraform apply -input=false -auto-approve
          echo "BUCKET=$(terraform output -raw site_bucket)" >> "$GITHUB_ENV"
          echo "DIST=$(terraform output -raw cloudfront_distribution_id)" >> "$GITHUB_ENV"
      - name: Sync + invalidate
        run: |
          aws s3 sync build/static "s3://$BUCKET/static" \
            --cache-control "public, max-age=31536000, immutable" --delete
          aws s3 sync build "s3://$BUCKET" \
            --cache-control "public, max-age=0, must-revalidate" \
            --exclude "static/*" --delete
          aws cloudfront create-invalidation --distribution-id "$DIST" --paths "/*"
```

Store the role ARN as the `AWS_DEPLOY_ROLE_ARN` repo secret. Push to `main` (or run
the workflow manually) to deploy.

---

## Verify

```bash
# CloudFront domain (also a Terraform output)
curl -I "https://$(terraform -chdir=infra output -raw cloudfront_domain)"
# → HTTP/2 200, with a Cache-Control header on / (must-revalidate)
```

If using a custom domain, DNS + cert propagation takes ~10 min on the first apply.

## Teardown

```bash
aws s3 rm "s3://$BUCKET" --recursive   # empty the bucket first
terraform -chdir=infra destroy
```
