## Compose file — basic structure

```yaml
# compose.yaml (preferred name; docker-compose.yml also works)
# The top-level `version:` key is OBSOLETE in Compose v2 — omit it.
services:
  web:
    build: .                     # build from local Dockerfile
    image: myapp:1.0             # tag the built image
    ports:
      - "8080:80"                # host:container
    environment:
      - NODE_ENV=production
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    networks: [appnet]
    restart: unless-stopped

  db:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks: [appnet]

volumes:
  pgdata:

networks:
  appnet:
```

- Modern Compose (the `docker compose` plugin, v2) ignores the `version:` field — drop it. The old v2/v3 schema numbers only mattered for the legacy `docker-compose` Python tool.
- https://docs.docker.com/reference/compose-file/

---

## Services — build vs image

```yaml
services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: build              # build a specific multi-stage target
      args:
        APP_ENV: prod            # build-time ARG
    image: myorg/api:dev         # name for the resulting image
    command: ["node", "server.js"]   # override CMD
    ports:
      - "3000:3000"
```

- `build:` builds locally; `image:` pulls (or names the build output). Provide both to build and tag.
- https://docs.docker.com/reference/compose-file/services/

---

## depends_on + healthcheck — real ordering

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy   # wait until db's healthcheck passes
      redis:
        condition: service_started    # default: just wait for start
  db:
    image: postgres:17
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5
      start_period: 10s
```

- Plain `depends_on: [db]` only waits for the container to **start**, not to be **ready**. Use the long form with `condition: service_healthy` + a `healthcheck` on the dependency for true readiness.
- https://docs.docker.com/reference/compose-file/services/#depends_on

---

## env_file & environment

```yaml
services:
  api:
    env_file:
      - .env                     # KEY=VALUE lines, loaded into the container
      - .env.local
    environment:
      LOG_LEVEL: debug           # inline; overrides env_file on conflict
      DATABASE_URL: ${DATABASE_URL}   # interpolated from the shell / .env
```

- `${VAR}` interpolation in the compose file itself reads from the shell env or a `.env` file **in the project dir** (different from `env_file:`, which is injected into the container).
- https://docs.docker.com/compose/how-tos/environment-variables/

---

## Volumes & networks

```yaml
services:
  app:
    volumes:
      - pgdata:/var/lib/postgresql/data   # named volume
      - ./src:/app/src                    # bind mount (dev)
      - ./config:/etc/app:ro              # read-only bind mount

volumes:
  pgdata:                        # declare named volumes here

networks:
  appnet:
    driver: bridge
```

- Compose auto-creates a default network; services reach each other by **service name** (e.g. `db:5432`) on it.
- https://docs.docker.com/reference/compose-file/volumes/

---

## Profiles — optional services

```yaml
services:
  app:
    image: myapp:1.0
  debug-tools:
    image: nicolaka/netshoot
    profiles: ["debug"]          # only starts when profile is activated
```

```bash
docker compose --profile debug up    # include profiled services
docker compose up                    # debug-tools NOT started
```

- Services with a `profiles:` list are skipped unless that profile is enabled via `--profile` or `COMPOSE_PROFILES`.
- https://docs.docker.com/compose/how-tos/profiles/

---

## docker compose commands (v2)

```bash
docker compose up -d                 # build (if needed) + start, detached
docker compose up --build            # force rebuild images first
docker compose down                  # stop + remove containers/networks
docker compose down -v               # ALSO remove named volumes (data loss)

docker compose ps                    # status of services
docker compose logs -f api           # follow one service's logs
docker compose exec api sh           # shell into a running service
docker compose run --rm api npm test # one-off command in a new container

docker compose build api             # build a single service
docker compose pull                  # pull images for image: services
docker compose config                # render the fully-resolved config
docker compose restart api
```

- It's `docker compose` (space, the v2 plugin) — the old `docker-compose` (hyphen) is the deprecated standalone tool.
- `exec` runs in an existing container; `run` spins up a fresh one (use for tasks/migrations).
- https://docs.docker.com/reference/cli/docker/compose/

## Docs
- Compose overview: https://docs.docker.com/compose/
- Compose file reference: https://docs.docker.com/reference/compose-file/
- Compose CLI: https://docs.docker.com/reference/cli/docker/compose/
- Environment variables: https://docs.docker.com/compose/how-tos/environment-variables/
- Profiles: https://docs.docker.com/compose/how-tos/profiles/
