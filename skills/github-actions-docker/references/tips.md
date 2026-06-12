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
