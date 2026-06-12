---
name: deploy-k8s-on-ec2
description: Spin up a production Kubernetes cluster on EC2 running kind. Provision and deploy locally from your laptop, or fully automated via GitHub Actions.
---

# Kubernetes on EC2 (kind)

A real, production-grade Kubernetes cluster on a single EC2 instance using kind — ~$15/month on a t3.small. Terraform provisions the instance; a laptop shell or GitHub Actions drives deploys.

## References
- `references/infra.md` — prerequisites, inputs to gather, Terraform resources created
- `references/local-deploy.md` — Option A: provision and deploy from your laptop
- `references/ci-deploy.md` — Option B: provision and deploy via GitHub Actions
- `references/gotchas.md` — rolling update limits on small instances, IMDS hop, verify, teardown

## TL;DR
- Gather 6 inputs before writing: cluster name, instance type, domain, region, worker count, state bucket.
- One-time: create a versioned S3 bucket for Terraform state.
- ECR tokens expire every 12 h inside kind nodes — refresh the pull secret on every deploy.
- Use `maxSurge: 0, maxUnavailable: 1` + `minAvailable: 1` for rolling updates on a t3.small.
- Add `-o ServerAliveInterval=20` to every SSH command that blocks (e.g. helm --wait).
