## Container exited immediately

```bash
docker ps -a --filter "status=exited"    # find it + see exit code
docker logs <container>                  # why did it die?
docker inspect <container> --format '{{.State.ExitCode}} {{.State.Error}}'
```

- A container lives only as long as its **PID 1**. If `CMD`/`ENTRYPOINT` runs and returns, the container exits — there's no daemon keeping it alive.
- Exit `0` = clean exit (the command finished); `137` = SIGKILL (often OOM); `139` = segfault; `143` = SIGTERM.
- Long-running services must run a foreground process. Don't background it (`cmd &`) or use a shell that exits.
- Debug interactively: `docker run -it --entrypoint sh <image>` then run the command by hand.

---

## Build cache not invalidating (or busting too often)

```bash
docker build --no-cache -t myapp .       # force a clean rebuild
docker build --progress=plain .          # see each step + cache hits
```

- A changed instruction invalidates that layer **and everything after it**. If editing source re-runs `npm ci`, your `COPY . .` is above the install — reorder so deps copy/install first.
- `COPY`/`ADD` cache keys depend on file *contents* (checksums); other instructions key on the literal string. Bump a value (e.g. `ARG CACHEBUST=$(date)`) to force-bust a stubborn `RUN`.
- With BuildKit, use cache mounts (`RUN --mount=type=cache,...`) so package caches survive even when the layer re-runs.

---

## Image too big / layer bloat

```bash
docker history --no-trunc myapp:1.0      # which layer added the weight
docker image inspect myapp:1.0 --format '{{.Size}}'
docker scout cves myapp:1.0              # vulnerabilities + base recommendations
```

- Cleaning up in a **later** `RUN` doesn't shrink the image — the files still exist in the earlier layer. Install and clean in the **same** `RUN`: `apt-get install ... && rm -rf /var/lib/apt/lists/*`.
- Use multi-stage builds to drop compilers/build deps; copy only artifacts into a slim/distroless final stage.
- Switch base images: `node:22` → `node:22-slim` → distroless can cut hundreds of MB.

---

## Port conflicts — "address already in use"

```bash
docker ps --format '{{.Names}}\t{{.Ports}}'   # what's bound where
lsof -i :8080                                  # macOS/Linux: who owns the host port
docker run -p 8081:80 nginx                    # remap to a free host port
```

- `Bind for 0.0.0.0:8080 failed: port is already allocated` means another process (or container) already publishes that host port. Change the **host** side of `-p HOST:CONTAINER`.
- Two containers can both use container-port `80` internally — the conflict is only on the published *host* port.

---

## Permission issues (volumes / non-root)

```bash
docker exec <c> id                       # what UID is the process?
ls -ln ./data                            # host file ownership (numeric)
```

- Bind-mounted files keep their **host UID/GID**. If the container runs as `node` (UID 1000) but the host files are owned by another UID, you get `EACCES`/`Permission denied`.
- Fix by aligning UIDs: run with `--user "$(id -u):$(id -g)"`, or `chown` inside the Dockerfile, or set ownership on the host.
- Named volumes are created root-owned by default — `chown` them in an entrypoint or run an init step before dropping privileges.

---

## Containers can't reach each other

```bash
docker network ls
docker network inspect <net>             # which containers are attached
docker exec api getent hosts db          # does the name resolve?
docker exec api ping -c1 db
```

- Use the **service/container name** as the hostname, not `localhost` — inside a container `localhost` is that container itself.
- Name resolution only works on a **user-defined** network (or a Compose network). The default `bridge` network has no DNS — create one: `docker network create appnet` and attach both containers.
- Use the **container port**, not the published host port, for container-to-container traffic (e.g. `db:5432`, even if you published `5433:5432`).

---

## Connecting from container to the host machine

```bash
# Reach a service running on the host (macOS/Windows, and Linux 20.10+ with the flag)
docker run --add-host=host.docker.internal:host-gateway myapp
# then connect to host.docker.internal:<port>
```

- `host.docker.internal` resolves to the host. On Linux you must add `--add-host=host.docker.internal:host-gateway` (it's built in on Docker Desktop).

---

## Inspecting — your three core tools

```bash
# logs — application stdout/stderr
docker logs -f --tail 200 <c>

# inspect — full JSON: state, mounts, networks, env, config
docker inspect <c>
docker inspect <c> --format '{{json .NetworkSettings.Networks}}' | jq
docker inspect <c> --format '{{.State.Health.Status}}'   # healthcheck status

# exec — get inside and poke around
docker exec -it <c> sh
docker exec <c> cat /etc/hosts
docker exec <c> env

# events — watch daemon activity in real time
docker events
```

- `docker inspect` is the source of truth for IPs, mounts, env, restart policy, and health state — pipe `--format '{{json .}}'` into `jq`.
- For a container with no shell (distroless/scratch), debug with an ephemeral sidecar: `docker run -it --rm --pid container:<c> --network container:<c> nicolaka/netshoot`.

## Docs
- Container troubleshooting / logs: https://docs.docker.com/reference/cli/docker/container/logs/
- Inspect: https://docs.docker.com/reference/cli/docker/inspect/
- Networking tutorials: https://docs.docker.com/engine/network/
- Build cache: https://docs.docker.com/build/cache/
- Docker Scout (image analysis): https://docs.docker.com/scout/
