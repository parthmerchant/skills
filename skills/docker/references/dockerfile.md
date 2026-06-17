## Instructions — the core set

```dockerfile
# Base image — always pin a tag (avoid bare :latest)
FROM node:22-slim

# Build-time variable (not in final image unless re-declared after FROM)
ARG APP_VERSION=dev

# Runtime environment variable (persists in the image)
ENV NODE_ENV=production \
    PORT=3000

# Set/create the working dir for subsequent instructions
WORKDIR /app

# COPY <src> <dest> — prefer COPY over ADD
COPY package.json package-lock.json ./

# RUN executes at build time, creating a layer
RUN npm ci --omit=dev

COPY . .

# Documents the port; does NOT publish it (use -p at run time)
EXPOSE 3000

# Drop root — run as an unprivileged user
USER node

# CMD = default args; ENTRYPOINT = fixed executable (see below)
CMD ["node", "server.js"]
```

- `WORKDIR` creates the directory if missing and is preferred over `RUN cd ...`.
- `EXPOSE` is documentation only — you still publish ports with `docker run -p`.
- https://docs.docker.com/reference/dockerfile/

---

## ARG vs ENV

```dockerfile
ARG BUILD_ID            # available only during build, NOT in running container
ENV BUILD_ID=$BUILD_ID  # persist it into the image/runtime if needed

# ARGs declared before the first FROM are global but must be re-declared
# inside a build stage to be used there:
ARG TAG=22-slim
FROM node:${TAG}
ARG TAG                 # re-declare to use inside this stage
```

- Pass build args: `docker build --build-arg BUILD_ID=123 .`
- Never bake secrets via `ARG` — they're visible in image history (`docker history`). Use BuildKit secrets instead (below).

---

## COPY vs ADD

```dockerfile
COPY src/ /app/src/          # plain file/dir copy — use this 99% of the time
ADD https://x.com/f.tar /tmp # ADD can fetch URLs and auto-extract local tarballs
ADD archive.tar.gz /opt/     # auto-extracts into /opt
```

- Prefer `COPY` for clarity. Only use `ADD` for its auto-extract or remote-fetch behavior.
- https://docs.docker.com/build/building/best-practices/#add-or-copy

---

## CMD vs ENTRYPOINT

```dockerfile
# Exec form (preferred) — no shell, PID 1 receives signals (clean SIGTERM)
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8000"]        # default args appended to ENTRYPOINT

# Shell form — wraps in /bin/sh -c, breaks signal forwarding, NOT recommended
CMD python app.py
```

- `ENTRYPOINT` = the thing that always runs. `CMD` = overridable default args.
- `docker run img --port 9000` overrides `CMD`; `docker run --entrypoint sh img` overrides `ENTRYPOINT`.
- Use **exec form** (`["..."]`) so your process is PID 1 and stops gracefully. Shell form makes `/bin/sh` PID 1 and your app never sees `SIGTERM`.
- https://docs.docker.com/reference/dockerfile/#cmd

---

## HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

- Exit `0` = healthy, `1` = unhealthy. Status shows in `docker ps` as `(healthy)`/`(unhealthy)`.
- `--start-period` gives slow-booting apps grace time before failures count.
- `HEALTHCHECK NONE` disables a healthcheck inherited from the base image.
- https://docs.docker.com/reference/dockerfile/#healthcheck

---

## Multi-stage builds

```dockerfile
# ---- build stage ----
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /bin/app ./cmd/app

# ---- final stage ----
FROM gcr.io/distroless/static-debian12
COPY --from=build /bin/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

- Each `FROM` starts a new stage; the final stage is what ships. Build toolchains/compilers never reach the runtime image.
- `COPY --from=build /path` pulls artifacts from an earlier stage. You can also `COPY --from=alpine:3.20 ...` from an external image.
- Build a specific stage: `docker build --target build -t myapp:debug .`
- https://docs.docker.com/build/building/multi-stage/

---

## Layer caching — order matters

```dockerfile
# GOOD: deps cached independently of source changes
COPY package.json package-lock.json ./
RUN npm ci
COPY . .            # editing source only invalidates from here down

# BAD: any source change re-runs the install
COPY . .
RUN npm ci
```

- Each instruction is a layer; Docker reuses a cached layer if the instruction and its inputs are unchanged.
- Changing one layer invalidates **all** layers after it — put rarely-changing things (deps) early, frequently-changing things (source) late.
- Combine related `RUN`s with `&&` and clean up in the same layer (see below) so cleanup actually shrinks the image.
- https://docs.docker.com/build/cache/

---

## BuildKit

```bash
# BuildKit is the default backend on modern Docker; force it explicitly:
DOCKER_BUILDKIT=1 docker build -t myapp .

# buildx — multi-platform, cache export, etc.
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:multi --push .
```

```dockerfile
# syntax=docker/dockerfile:1

# Cache mount — persist package caches across builds (BuildKit only)
RUN --mount=type=cache,target=/root/.npm npm ci

# Secret mount — secret never lands in a layer or image history
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
```

- Add `# syntax=docker/dockerfile:1` as the first line to enable BuildKit frontend features.
- Pass a secret: `docker build --secret id=npmrc,src=$HOME/.npmrc .`
- https://docs.docker.com/build/buildkit/

---

## .dockerignore

```
.git
node_modules
**/*.log
.env
.env.*
dist
coverage
Dockerfile
.dockerignore
```

- Lives next to the Dockerfile. Excludes files from the **build context** sent to the daemon — smaller context = faster builds and no accidental secrets/`node_modules` in `COPY . .`.
- Syntax mirrors `.gitignore`.
- https://docs.docker.com/build/building/context/#dockerignore-files

---

## Best practices — small & secure images

```dockerfile
# Single cleaned-up apt layer (cache removed in the SAME layer)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Run as non-root
RUN useradd --uid 10001 --no-create-home appuser
USER 10001
```

- **Pin tags / digests** — `node:22-slim` not `node`, or pin a `@sha256:` digest for reproducibility.
- Prefer `-slim`, `alpine`, or **distroless** base images; multi-stage to drop build deps.
- **Don't run as root** — add a `USER`. Use a numeric UID so it works without `/etc/passwd` lookups.
- Clean package manager caches in the same `RUN` layer (`rm -rf /var/lib/apt/lists/*`).
- One concern per container; let the process be PID 1 (exec-form `ENTRYPOINT`/`CMD`).
- Scan images: `docker scout cves myapp:latest`.
- https://docs.docker.com/build/building/best-practices/

## Docs
- Dockerfile reference: https://docs.docker.com/reference/dockerfile/
- Building best practices: https://docs.docker.com/build/building/best-practices/
- Multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- BuildKit: https://docs.docker.com/build/buildkit/
- Build cache: https://docs.docker.com/build/cache/
