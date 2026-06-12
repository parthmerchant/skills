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
