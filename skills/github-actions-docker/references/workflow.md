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
