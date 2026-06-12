# Workflow Templates

## Minimal — AWS auth only

```yaml
name: deploy
on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - run: aws sts get-caller-identity   # smoke test
      # add your aws cli / cdk / sam / eb steps here
```

---

## Terraform — plan on PR, apply on main

```yaml
name: terraform
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read
  pull-requests: write   # needed to post plan comments

env:
  TF_VERSION: "1.9.5"
  AWS_REGION: us-east-1

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra   # adjust to your tf root

    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Init
        run: terraform init -input=false

      - name: Validate
        run: terraform validate

      - name: Plan
        id: plan
        run: terraform plan -input=false -no-color 2>&1 | tee /tmp/plan.txt
        continue-on-error: true   # post comment even if plan fails

      - name: Post plan comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs')
            const plan = fs.readFileSync('/tmp/plan.txt', 'utf8').slice(0, 65000)
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Terraform Plan\n\`\`\`\n${plan}\n\`\`\``
            })

      - name: Apply
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: terraform apply -input=false -auto-approve
```

---

## Common additions

### ECR image build + push
```yaml
      - name: Log in to ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push
        env:
          REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE: my-app
          TAG: ${{ github.sha }}
        run: |
          docker build -t $REGISTRY/$IMAGE:$TAG .
          docker push $REGISTRY/$IMAGE:$TAG
```

### S3 sync
```yaml
      - name: Deploy to S3
        run: |
          aws s3 sync dist/ s3://${{ secrets.BUCKET }} \
            --cache-control "public, max-age=0, must-revalidate" --delete
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CF_DIST_ID }} --paths "/*"
```

### ECS rolling deploy
```yaml
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster ${{ secrets.ECS_CLUSTER }} \
            --service ${{ secrets.ECS_SERVICE }} \
            --force-new-deployment
          aws ecs wait services-stable \
            --cluster ${{ secrets.ECS_CLUSTER }} \
            --services ${{ secrets.ECS_SERVICE }}
```

---

## Gotchas

| Problem | Fix |
|---|---|
| `Error: Credentials could not be loaded` | Job is missing `permissions: { id-token: write }` |
| Plan applies on PRs from forks | Fork PRs don't get secrets — gate apply on `github.ref` AND `github.event_name == 'push'` |
| Terraform state lock during concurrent runs | Add `concurrency: { group: terraform-${{ github.ref }}, cancel-in-progress: false }` |
| Plan output truncated in comment | Slice to 65 000 chars — GitHub comment body limit is 65 536 |
| OIDC thumbprint mismatch | Re-fetch: `openssl s_client -connect token.actions.githubusercontent.com:443 < /dev/null 2>/dev/null \| openssl x509 -fingerprint -noout -sha1` |
