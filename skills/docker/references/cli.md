## docker run — start a container

```bash
# Foreground, interactive shell, removed on exit
docker run -it --rm alpine:3.20 sh

# Detached, named, with a published port (host:container)
docker run -d --name web -p 8080:80 nginx:1.27

# Env vars (single + from file) and a restart policy
docker run -d --name api \
  -e NODE_ENV=production -e PORT=3000 \
  --env-file .env \
  --restart unless-stopped \
  -p 3000:3000 myapp:1.0

# Override the entrypoint / run a one-off command
docker run --rm --entrypoint sh myapp:1.0 -c "node --version"
```

- `-d` detached, `-it` interactive+TTY, `--rm` auto-remove on exit, `--name` for a stable reference.
- `-p HOST:CONTAINER` publishes a port; `-P` publishes all `EXPOSE`d ports to random host ports.
- https://docs.docker.com/reference/cli/docker/container/run/

---

## docker build — build & tag an image

```bash
# Build from cwd context, tag it
docker build -t myapp:1.0 -t myapp:latest .

# Specific Dockerfile + build args
docker build -f docker/Dockerfile.prod --build-arg APP_ENV=prod -t myapp:prod .

# Target one stage of a multi-stage build
docker build --target build -t myapp:build .

# Multi-platform via buildx, push directly to registry
docker buildx build --platform linux/amd64,linux/arm64 -t reg.io/me/myapp:1.0 --push .
```

- The final `.` is the **build context** — keep it small with `.dockerignore`.
- Tag with both a version and `latest`; CI should tag with the git SHA.
- https://docs.docker.com/reference/cli/docker/buildx/build/

---

## exec, logs, ps — inspect running containers

```bash
# Shell into a running container
docker exec -it web sh           # or bash if available

# Run a one-off command inside it
docker exec web env

# Follow logs, last 100 lines, with timestamps
docker logs -f --tail 100 -t web

# List running / all containers
docker ps
docker ps -a                     # includes stopped/exited
docker ps --filter "status=exited" --format '{{.Names}}\t{{.Status}}'

# Live resource usage
docker stats
```

- https://docs.docker.com/reference/cli/docker/container/exec/
- https://docs.docker.com/reference/cli/docker/container/logs/

---

## Lifecycle — stop, start, rm

```bash
docker stop web                  # graceful SIGTERM then SIGKILL after grace period
docker start web
docker restart web
docker rm web                    # remove a stopped container
docker rm -f web                 # force-remove a running one
docker rm $(docker ps -aq)       # remove ALL containers
```

---

## Images — list, tag, rm

```bash
docker images                    # list local images
docker image ls --filter dangling=true

docker tag myapp:1.0 reg.io/me/myapp:1.0   # add a registry-qualified tag

docker rmi myapp:1.0             # remove an image
docker rmi $(docker images -f dangling=true -q)   # remove dangling images

docker history myapp:1.0         # inspect layers (and leaked build args!)
```

- https://docs.docker.com/reference/cli/docker/image/

---

## Registry — login, push, pull

```bash
docker login reg.io                          # or: docker login ghcr.io / Docker Hub
echo "$TOKEN" | docker login ghcr.io -u USER --password-stdin

docker push reg.io/me/myapp:1.0
docker pull reg.io/me/myapp:1.0
```

- Image refs are `registry/namespace/name:tag`; no registry implies Docker Hub.
- https://docs.docker.com/reference/cli/docker/image/push/

---

## Volumes — persistent data

```bash
docker volume create pgdata
docker volume ls
docker volume inspect pgdata

# Named volume (managed by Docker)
docker run -d --name db -v pgdata:/var/lib/postgresql/data postgres:17

# Bind mount (host path -> container path)
docker run --rm -v "$PWD":/app -w /app node:22 npm test

# Read-only mount
docker run --rm -v "$PWD/config":/etc/app:ro myapp:1.0
```

- **Named volumes** are managed by Docker and survive container removal. **Bind mounts** map a host path (great for dev).
- https://docs.docker.com/engine/storage/volumes/

---

## Networks — connect containers

```bash
docker network create appnet
docker network ls
docker network inspect appnet

# Containers on the same user-defined network resolve each other by NAME
docker run -d --name db --network appnet postgres:17
docker run -d --name api --network appnet -e DB_HOST=db myapp:1.0

# Attach an existing container to a network
docker network connect appnet web
```

- On a **user-defined** network, containers reach each other via DNS by container/service name (e.g. `db:5432`). The default `bridge` network does NOT provide name resolution.
- https://docs.docker.com/engine/network/

---

## Prune — reclaim disk

```bash
docker system df                 # see what's using space FIRST

docker container prune           # remove stopped containers
docker image prune               # remove dangling images
docker image prune -a            # remove ALL unused images
docker volume prune              # remove unused volumes (DATA LOSS)
docker network prune

docker system prune -a --volumes # nuke everything unused (careful)
```

- `prune` is destructive — `--volumes` deletes data. Always run `docker system df` first.
- https://docs.docker.com/reference/cli/docker/system/prune/

## Docs
- CLI reference: https://docs.docker.com/reference/cli/docker/
- Storage / volumes: https://docs.docker.com/engine/storage/volumes/
- Networking: https://docs.docker.com/engine/network/
- Prune: https://docs.docker.com/config/pruning/
