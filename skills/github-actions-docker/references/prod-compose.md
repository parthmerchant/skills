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
