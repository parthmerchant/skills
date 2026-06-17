---
name: docker
description: Docker fundamentals — CLI, images, containers, Dockerfile authoring, multi-stage builds, and Compose. Use when writing a Dockerfile, building/tagging/pushing images, running or debugging containers, wiring up docker-compose, or fixing build cache, networking, port, or permission issues.
---

# Docker

App-agnostic fundamentals for building images and running containers. Read the reference that matches your task.

## References
- `references/dockerfile.md` — instructions, multi-stage builds, layer caching, BuildKit, `.dockerignore`, small/secure image practices
- `references/cli.md` — run/build/exec/logs/ps/images/rm/rmi, volumes, networks, ports, env, tags, push/pull, prune
- `references/compose.md` — Compose v2/v3 file syntax, services, `depends_on` + healthcheck, volumes, networks, env_file, profiles, `docker compose` commands
- `references/troubleshooting.md` — build cache, layer bloat, exited containers, port conflicts, permissions, container networking, `inspect`/`logs`/`exec`

## TL;DR
- **Order Dockerfile layers cheap-to-expensive**: copy dependency manifests and install deps *before* copying source, so code edits don't bust the dependency cache.
- **`CMD` vs `ENTRYPOINT`**: `ENTRYPOINT` is the fixed executable; `CMD` is the default args. Use exec form (`["cmd","arg"]`) — shell form breaks signal handling (PID 1 won't get `SIGTERM`).
- **Multi-stage builds** keep toolchains out of the final image — `COPY --from=build` only the artifacts you ship.
- **`.dockerignore` is mandatory** — without it, `.git`, `node_modules`, and secrets get sent to the build context and bloat/leak into images.
- **A container exits when its main process exits** — `docker ps -a` shows stopped ones; `docker logs <id>` tells you why.
- **`depends_on` only waits for *start*, not readiness** — add a `healthcheck` + `depends_on: condition: service_healthy` for real ordering.
- **Containers talk to each other by service/container name on a shared user-defined network**, not `localhost` — `localhost` inside a container is the container itself.
- **`docker system prune -a` reclaims space** but deletes all unused images; run `docker system df` first to see what's using disk.

## Docs
- Docker overview: https://docs.docker.com/get-started/
- Reference index: https://docs.docker.com/reference/
- Best practices: https://docs.docker.com/build/building/best-practices/
