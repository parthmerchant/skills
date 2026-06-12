## Option B — Run it in GitHub Actions

**`provision-cluster.yml`** — manual (`workflow_dispatch`) with inputs `action`
(`apply`/`destroy`) and `instance_type`:

```yaml
name: provision-cluster
on:
  workflow_dispatch:
    inputs:
      action: { type: choice, options: [apply, destroy], default: apply }
      instance_type: { type: string, default: t3.small }
permissions: { id-token: write, contents: read }
jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_ROLE_ARN }}, aws-region: us-east-1 }
      - uses: hashicorp/setup-terraform@v3
        with: { terraform_version: 1.9.5 }
      - working-directory: infra/<cluster-name>
        run: |
          terraform init -input=false
          terraform validate
          terraform ${{ inputs.action }} -input=false -auto-approve \
            -var "instance_type=${{ inputs.instance_type }}"
```

**`deploy-app.yml`** — on push to `main`/`master` and git tags. Key steps:

```yaml
# After ECR login, before helm upgrade:
- name: Refresh ECR pull secret
  run: |
    ssh -i /tmp/ec2_key.pem -o StrictHostKeyChecking=no \
      -o ServerAliveInterval=20 ubuntu@$EC2_HOST \
      "kubectl create secret docker-registry regcred \
        --docker-server=$REGISTRY \
        --docker-username=AWS \
        --docker-password=\$(aws ecr get-login-password --region $AWS_REGION) \
        -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"

- name: Deploy via Helm
  run: |
    ssh -i /tmp/ec2_key.pem -o StrictHostKeyChecking=no \
      -o ServerAliveInterval=20 ubuntu@$EC2_HOST \
      "helm upgrade --install $RELEASE /tmp/chart.tgz \
        --namespace $NAMESPACE --set image.tag=$IMAGE_TAG \
        --wait --timeout 5m"
```

Use `ServerAliveInterval=20` on all SSH steps — `helm --wait` blocks silently for
minutes and NAT gear will drop the connection without keepalives.
