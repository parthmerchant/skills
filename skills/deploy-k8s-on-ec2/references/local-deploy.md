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
