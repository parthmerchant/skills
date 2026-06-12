## Option A — Run it locally

Everything the CI does, from your laptop:

```bash
# 1. Provision the infrastructure
cd infra
terraform init -input=false
terraform apply -input=false            # review the plan, type "yes"

# capture outputs
BUCKET=$(terraform output -raw site_bucket)
DIST=$(terraform output -raw cloudfront_distribution_id)
cd ..

# 2. Build the site
npm ci
npm run build                           # or your build command

# 3. Two-pass upload (immutable assets, then revalidated HTML)
aws s3 sync build/static "s3://$BUCKET/static" \
  --cache-control "public, max-age=31536000, immutable" --delete
aws s3 sync build "s3://$BUCKET" \
  --cache-control "public, max-age=0, must-revalidate" \
  --exclude "static/*" --delete

# 4. Invalidate the CDN so viewers get the new HTML immediately
aws cloudfront create-invalidation --distribution-id "$DIST" --paths "/*"
```

If your bundler doesn't emit a hashed `static/` folder, collapse steps 3 into a
single `must-revalidate` pass.
