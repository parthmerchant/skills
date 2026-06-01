---
title: GitHub Actions CI/CD for Docker Compose Apps
description: Wire up a complete GitHub Actions pipeline for a Docker Compose application — lint, test, build images, push to a registry, and deploy to a remote host over SSH. Works with any React + FastAPI + PostgreSQL stack.
icon: ⚙️
tags: github-actions, docker, ci-cd, deployment, ssh
---

# GitHub Actions CI/CD for Docker Compose

A production CI/CD pipeline for apps built with Docker Compose. On every push to `main`: run the E2E test suite against a live Compose stack, build and tag images, push to GitHub Container Registry (GHCR), and deploy to a remote host by pulling the new images and running `docker compose up`. Secrets stay in GitHub — nothing is hard-coded.

## What you get

- **CI job** — spins up the full Compose stack (db + backend + frontend) inside the runner, waits for health, runs the stdlib E2E test suite, tears down cleanly.
- **Build + push job** — builds multi-platform images (`linux/amd64,linux/arm64`) and pushes to GHCR with two tags: `sha-<commit>` (immutable) and `latest` (rolling).
- **Deploy job** — SSHes into the remote host, pulls the new images, and does a zero-downtime `docker compose up -d --pull always`. No custom deploy tooling required.
- **Dependency ordering** — deploy only runs if CI and build both pass; build only runs on `main` (PRs only run CI).

## Prerequisites

| Requirement | Notes |
|---|---|
| Remote host | Any Linux VM with Docker + Docker Compose v2 installed |
| SSH access | Key pair — private key goes in GitHub Secrets |
| GHCR access | Automatic — `GITHUB_TOKEN` has `packages: write` when you grant it |

## Ask the user

1. **Registry image names** — one per service that gets deployed (e.g. `ghcr.io/org/myapp-backend`, `ghcr.io/org/myapp-frontend`). Confirm whether the DB image is stock Postgres (most common) or custom.
2. **Remote host** — IP or hostname, SSH username (e.g. `ubuntu`), and where the project lives on the server (e.g. `/opt/myapp`).
3. **Branch that triggers deploy** — default `main`; can be `master` or a release branch.
4. **E2E test script path** — default `tests/e2e_test.py`; adjust if using pytest or a different runner.
5. **Environment variables on the server** — list any `.env` values the stack needs at runtime (DB passwords, API keys). These become GitHub Secrets.

## Secrets to add in GitHub

Go to **Settings → Secrets and variables → Actions** and add:

| Secret name | Value |
|---|---|
| `SSH_PRIVATE_KEY` | Private key for the remote host (paste the full PEM block) |
| `SSH_HOST` | IP or hostname of the remote server |
| `SSH_USER` | SSH username (e.g. `ubuntu`, `ec2-user`) |
| `DEPLOY_PATH` | Absolute path on the server (e.g. `/opt/myapp`) |
| Any app secrets | DB password, API keys, etc. — referenced in the deploy step |

`GITHUB_TOKEN` is automatic — no secret to add for GHCR.

---

## `.github/workflows/ci-cd.yml`

```yaml
name: CI / CD

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{ github.repository_owner }}

jobs:
  # ── 1. Integration tests ──────────────────────────────────────────────────
  test:
    name: E2E tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start Compose stack
        run: docker compose up --build -d

      - name: Wait for backend
        run: |
          echo "Waiting for backend..."
          for i in $(seq 1 30); do
            curl -sf http://localhost:8000/api/items >/dev/null && echo "Ready" && break
            sleep 2
          done

      - name: Run E2E suite
        run: python3 tests/e2e_test.py

      - name: Dump logs on failure
        if: failure()
        run: docker compose logs

      - name: Tear down
        if: always()
        run: docker compose down -v

  # ── 2. Build & push images (main/master only) ────────────────────────────
  build:
    name: Build & push
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'   # skip on PRs
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        include:
          - service: backend
            context: ./backend
          - service: frontend
            context: ./frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU (multi-platform)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push ${{ matrix.service }}
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.context }}
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:latest
            ${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:sha-${{ github.sha }}
          cache-from: type=gha,scope=${{ matrix.service }}
          cache-to:   type=gha,scope=${{ matrix.service }},mode=max

  # ── 3. Deploy to remote host ─────────────────────────────────────────────
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: build
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Install SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H "${{ secrets.SSH_HOST }}" >> ~/.ssh/known_hosts

      - name: Copy compose file to server
        run: |
          scp -i ~/.ssh/deploy_key \
            docker-compose.yml \
            ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }}:${{ secrets.DEPLOY_PATH }}/

      - name: Pull images and restart stack
        run: |
          ssh -i ~/.ssh/deploy_key \
            -o ServerAliveInterval=20 \
            ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} << 'EOF'
              cd ${{ secrets.DEPLOY_PATH }}
              echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
              docker compose pull
              docker compose up -d --remove-orphans
              docker image prune -f
          EOF

      - name: Smoke test
        run: |
          sleep 5
          ssh -i ~/.ssh/deploy_key \
            ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
            "curl -sf http://localhost:8000/api/items"
```

---

## `docker-compose.yml` — production variant

On the server the compose file uses pre-built registry images instead of local builds. Keep a `docker-compose.prod.yml` in the repo (or override the `build:` key with `image:`) so the server never needs the source code:

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB:       ${DB_NAME}
      POSTGRES_USER:     ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks: [app-net]

  backend:
    image: ghcr.io/<org>/<app>-backend:latest   # pulled by CI, never built on server
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks: [app-net]

  frontend:
    image: ghcr.io/<org>/<app>-frontend:latest
    ports: ["80:80", "443:443"]
    depends_on: [backend]
    restart: unless-stopped
    networks: [app-net]

volumes:
  pgdata:

networks:
  app-net:
```

A `.env` file on the server holds runtime secrets (never committed). The deploy step can write it from GitHub Secrets if needed:

```yaml
- name: Write .env on server
  run: |
    ssh -i ~/.ssh/deploy_key ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
      "cat > ${{ secrets.DEPLOY_PATH }}/.env << 'ENVEOF'
      DB_NAME=${{ secrets.DB_NAME }}
      DB_USER=${{ secrets.DB_USER }}
      DB_PASSWORD=${{ secrets.DB_PASSWORD }}
      ENVEOF"
```

---

## Image tagging strategy

Both `latest` and `sha-<commit>` tags are pushed on every main-branch build:

```
ghcr.io/org/app-backend:latest          # always points to newest build
ghcr.io/org/app-backend:sha-a1b2c3d    # immutable — pin this for rollbacks
```

To roll back, SSH into the server and pin the sha tag:

```bash
# On the remote host
docker compose stop backend
docker compose run --rm -e IMAGE_TAG=sha-a1b2c3d backend   # or edit compose directly
docker compose up -d backend
```

---

## Build cache

`cache-from: type=gha` reuses the GitHub Actions layer cache across runs. On a warm cache, a backend image that only changes `main.py` (not `requirements.txt`) rebuilds in under 10 seconds because the `pip install` layer is cached.

Key rule: **COPY requirements.txt before COPY . .** in every Dockerfile so the package layer is cached independently from the source layer:

```dockerfile
# ✅ package layer cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ❌ any source change busts the install layer
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

Same principle for the frontend:

```dockerfile
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build
```

---

## Common pitfalls

| Pitfall | Fix |
|---|---|
| SSH step hangs silently during `docker compose up --wait` | Add `-o ServerAliveInterval=20` to every SSH command that blocks |
| `docker compose pull` fails with "unauthorized" on GHCR | Log in to `ghcr.io` on the server before pulling: `echo TOKEN \| docker login ghcr.io -u USER --password-stdin` |
| Images not visible in GHCR after push | Set `packages: write` permission on the `build` job AND make sure the package visibility is set to the correct org/repo in GHCR settings |
| `docker compose up` leaves orphan containers from renamed services | Add `--remove-orphans` to the up command |
| Old images accumulate on the server | Run `docker image prune -f` after every deploy |
| Smoke test fails because the app needs more than 5 s to start | Replace the fixed `sleep` with a retry loop: `for i in $(seq 1 20); do curl -sf http://localhost:8000/api/items && break; sleep 2; done` |
| Build matrix runs sequentially | `strategy.matrix` with no `max-parallel` limit already runs jobs in parallel on GitHub-hosted runners |
| Multi-platform build much slower than single-platform | Add `platforms: linux/amd64` only during development; enable `linux/arm64` only when deploying to ARM hosts (Graviton, Apple Silicon servers) |

---

## Server bootstrap (one-time)

```bash
# Install Docker on a fresh Ubuntu 22.04 host
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# Verify Compose v2 plugin is present
docker compose version

# Create deploy directory
mkdir -p /opt/myapp
```

Add the server's public key to GitHub Deploy Keys (read-only) if you need to `git clone` on the server, or skip it entirely and use the `scp` step above to sync only the compose file.

---

## Commit and open a PR

Stage `.github/workflows/ci-cd.yml` and any updated `docker-compose.yml`. Commit message:

```
ci: add GitHub Actions pipeline — E2E test, GHCR build, SSH deploy
```

Push to a new branch and open a PR.
