---
title: Deploy Static Site to AWS
description: Deploy any static site to AWS — S3, CloudFront, GitHub Actions, Terraform. Runs locally from your laptop or fully automated in CI.
icon: 🚀
tags: aws, terraform, ci-cd, infrastructure
---

# Deploy Site

A complete, reproducible AWS static-site pipeline for any GitHub repo: a private
S3 bucket behind a CloudFront CDN, custom domain + TLS, and a two-pass cache
strategy — all defined in Terraform. Run it **locally** from your laptop, or wire
up the included **GitHub Actions** workflow to deploy on every push via OIDC.

## What you get

- Private S3 bucket (all public access blocked) served only through CloudFront via OAC
- CloudFront distribution with SPA routing (404 → `/index.html`) and HTTPS redirect
- Optional custom domain: ACM cert (`us-east-1`) + Route 53 alias records
- Two-pass cache: hashed assets cached forever, HTML always revalidated
- Reproducible Terraform state in S3 — destroy and recreate at will

## Creating a new React app

If you don't have a site yet, scaffold one with Vite:

```bash
npm create vite@latest my-site -- --template react
cd my-site
npm install
```

Replace `src/App.jsx` and `src/App.css` with the following to get a black-and-white "Coming Soon" page:

```jsx
// src/App.jsx
import './App.css'

export default function App() {
  return (
    <div className="page">
      <div className="card">
        <span className="icon">🚧</span>
        <h1>Coming Soon</h1>
        <p>Something great is on its way.</p>
      </div>
    </div>
  )
}
```

```css
/* src/App.css */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #000;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100dvh;
  display: grid;
  place-items: center;
}

.page { width: 100%; display: grid; place-items: center; padding: 2rem; }

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 3rem 4rem;
  text-align: center;
}

.icon { font-size: 3rem; }

h1 { font-size: clamp(2rem, 6vw, 3.5rem); font-weight: 700; letter-spacing: -0.02em; }

p { font-size: 1.1rem; color: #888; }
```

### Production build for a React SPA

Vite (and Create React App) emit a `dist/` (or `build/`) folder ready to be served as a static site:

```bash
npm run build          # outputs to dist/ (Vite) or build/ (CRA)
npm run preview        # optional local preview of the production bundle
```

Key things the build does:
- Bundles and tree-shakes JS/CSS, adds content-hash filenames (`assets/index-Bx9v1234.js`)
- Inlines small assets, copies public/ files verbatim
- Emits a single `index.html` — all routes must resolve to it (CloudFront's 404 → `/index.html` rule handles this)

When you run the deploy skill, set **Build output folder** to `dist` (Vite default) or `build` (CRA default).

---

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

---

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

---

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

## Commit and open a PR

Stage all new files. Commit message: `"chore: add AWS deploy pipeline (S3 + CloudFront + Terraform)"`. Push to a new branch and open a PR against `main` / `master`.
