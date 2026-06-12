---
name: github-actions-docker
description: Wire up a complete GitHub Actions pipeline for a Docker Compose application — lint, test, build images, push to a registry, and deploy to a remote host over SSH. Works with any React + FastAPI + PostgreSQL stack.
---

# GitHub Actions CI/CD for Docker Compose

Three-job pipeline: E2E tests → build + push to GHCR → SSH deploy. Triggers on push to `main`/`master`; PRs run tests only.

## References
- `references/workflow.md` — full ci-cd.yml (test + build + deploy jobs) and GitHub secrets to configure
- `references/prod-compose.md` — production docker-compose.yml using pre-built registry images
- `references/tips.md` — image tagging strategy, build cache, rollback, server bootstrap, common pitfalls

## TL;DR
- Ask 5 inputs: image names, remote host + SSH user + deploy path, trigger branch, E2E script path, runtime env vars.
- Add `-o ServerAliveInterval=20` to every SSH step that blocks.
- `COPY requirements.txt` before `COPY . .` in every Dockerfile to preserve the install cache layer.
- Both `latest` and `sha-<commit>` tags are pushed; pin the sha tag for rollbacks.
- Always add `--remove-orphans` to `docker compose up` in the deploy step.
