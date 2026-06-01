---
title: Kubernetes on EC2 with kind
description: Spin up a production Kubernetes cluster on EC2 running kind. Provision and deploy locally from your laptop, or fully automated via GitHub Actions.
icon: ☸️
tags: kubernetes, aws, terraform, ci-cd
---

# Deploy Kubernetes on EC2 (kind)

A real, production-grade Kubernetes cluster on a single EC2 instance using
kind — for about **$15/month** on a t3.small. Terraform provisions the instance,
Elastic IP, DNS, and an IAM role; a `user_data` bootstrap installs Docker, kind,
kubectl, Helm, cert-manager, and NGINX ingress on first boot. Drive it **locally**
from your laptop, or use the included **GitHub Actions** workflows to provision and
deploy from CI.

## What you get

- 1 control-plane + N worker nodes (kind), reachable at your domain over HTTPS
- NGINX ingress + cert-manager (Let's Encrypt, auto-renewed)
- ECR image pulls that work inside kind (refresh pull secret before every deploy)
- Zero-downtime `helm upgrade` rollouts sized for a small instance
- Local kubectl/k9s access over an SSH tunnel — the API server is never exposed

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Terraform | ≥ 1.9 | provisioning |
| AWS CLI | v2 | `aws configure` |
| kubectl / helm | latest | local cluster access |

One-time: create the Terraform state bucket (once per AWS account):

```bash
aws s3api create-bucket --bucket <tfstate-bucket> --region us-east-1
aws s3api put-bucket-versioning --bucket <tfstate-bucket> \
  --versioning-configuration Status=Enabled
```

## Ask the user (one at a time, conversationally)

1. **Cluster name** — short slug used for SSM paths and workflow names (e.g. `myapp`, `staging`)
2. **EC2 instance type** — default `t3.small` (~$15/month reserved)
3. **Domain name** — DNS name for your cluster (e.g. `api.yourdomain.com`)
4. **AWS region** — default `us-east-1`
5. **Number of kind worker nodes** — default `3` (1 control-plane + N workers)
6. **Terraform state bucket** — the one created above

## Create infra/\<cluster-name\>/

Write Terraform files: `versions.tf`, `providers.tf`, `variables.tf`, `data.tf`, `iam.tf`, `network.tf`, `keypair.tf`, `ec2.tf`, `dns.tf`, `ssm.tf`, `outputs.tf`, and a `templates/user_data.sh` bootstrap script.

**What the infra creates:**
- EC2 instance (configurable type) + Elastic IP
- Security group allowing 22 (SSH), 80 (HTTP), 443 (HTTPS)
- IAM role with ECR read + SSM read permissions
- Route 53 A record pointing the domain to the EIP
- RSA-4096 key pair stored in SSM SecureString (no plaintext secrets in git)
- SSM params: `/<cluster-name>/ec2-public-ip`, `/<cluster-name>/ec2-instance-id`, `/<cluster-name>/ec2-ssh-key`

**`user_data.sh` installs:** Docker, kubectl, kind (v0.20.0), Helm, AWS CLI v2; a kind
cluster named `<cluster-name>` (1 control-plane + N workers); NGINX ingress (auto-labels
control-plane `ingress-ready=true`); cert-manager; and the local-path storage provisioner.

State backend: state bucket provided by user, key `<cluster-name>/terraform.tfstate`.
Outputs: `instance_id`, `public_ip`, `backend_fqdn`, `ssh_key_ssm_path`.

---

## Option A — Run it locally

```bash
# 1. Provision
cd infra/<cluster-name>
terraform init -input=false
terraform apply -input=false            # ~10 min incl. user-data bootstrap
IP=$(terraform output -raw public_ip)
cd ../..

# 2. Pull the SSH key Terraform stored in SSM
aws ssm get-parameter --name /<cluster-name>/ec2-ssh-key --with-decryption \
  --query Parameter.Value --output text > ~/.ssh/<cluster-name>.pem
chmod 600 ~/.ssh/<cluster-name>.pem

# 3. Open a tunnel to the kind API server
ssh -i ~/.ssh/<cluster-name>.pem -N -L 6443:127.0.0.1:<api-port> ubuntu@"$IP" &

# 4. Refresh ECR pull secret + deploy
ssh -i ~/.ssh/<cluster-name>.pem ubuntu@"$IP" '
  kubectl create secret docker-registry regcred \
    --docker-server=<ecr-registry> \
    --docker-username=AWS \
    --docker-password=$(aws ecr get-login-password --region us-east-1) \
    -n <namespace> --dry-run=client -o yaml | kubectl apply -f -
  helm upgrade --install <release-name> ./chart \
    --namespace <namespace> --set image.tag=<tag> --wait --timeout 5m
  kubectl rollout status deployment/<app-name> -n <namespace> --timeout=5m
'
```

ECR tokens expire every 12 hours inside kind nodes (containerd has no instance role
access). The `--dry-run=client | kubectl apply` pattern refreshes the secret
idempotently on every deploy.

---

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

---

## Rolling update gotchas on small instances

**Default strategy fails on 2 GB instances:**

```yaml
# ❌ maxSurge:1 tries to schedule a 4th pod — no room on t3.small
rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }

# ✅ Take one down first, bring the replacement up
rollingUpdate: { maxSurge: 0, maxUnavailable: 1 }
```

**PDB traps the rollout:**

```yaml
# ❌ minAvailable: 2 with replicaCount: 2 — impossible to remove any pod
minAvailable: 2

# ✅ Allow one pod to be unavailable during the rollout
minAvailable: 1
```

**IMDS hop limit:** If pods need the EC2 instance role, set
`metadata_options { http_put_response_hop_limit = 2 }` in Terraform. kind pods are
one Docker hop from the host; the default limit of 1 silently blocks them.

---

## Verify

```bash
# over the SSH tunnel
kubectl get nodes              # control-plane + N workers, all Ready
kubectl get pods -A            # ingress-nginx, cert-manager, your app Running
curl -I https://<your-domain>  # HTTP/2 200, valid Let's Encrypt cert
```

## Teardown

```bash
cd infra/<cluster-name> && terraform destroy
# or run the provision workflow with action=destroy
```

## Commit and open a PR

Stage all new files. Commit message: `"chore: add kind cluster on EC2 via Terraform and GitHub Actions"`. Push to a new branch and open a PR against `main` / `master`.
