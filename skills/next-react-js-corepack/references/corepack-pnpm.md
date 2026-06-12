# Corepack & pnpm — fundamentals

## Corepack
- Ships with Node ≥ 16. `corepack enable` installs shims for `pnpm`/`yarn` on PATH.
- The package manager is pinned per-project via the **`packageManager`** field:
  ```json
  { "packageManager": "pnpm@9.15.9" }
  ```
  Corepack auto-downloads and uses exactly that version — reproducible across
  machines and CI without a global install.
- Pin Node too: an `.nvmrc` (e.g. `24`) and/or `engines.node` in package.json.

## pnpm essentials
- Content-addressable store + symlinked `node_modules` → fast installs, strict
  dependency resolution (no phantom deps).
- Common commands:
  ```bash
  pnpm install                  # respect lockfile
  pnpm install --frozen-lockfile  # CI/Docker: fail if lockfile is stale
  pnpm add <pkg>  /  pnpm add -D <pkg>
  pnpm <script>                 # run a package.json script (no "run" needed)
  pnpm dlx <pkg>                # one-off, like npx
  ```
- Commit `pnpm-lock.yaml`. Treat it as the source of truth.

## Workspaces (monorepos)
- `pnpm-workspace.yaml`:
  ```yaml
  packages: ['apps/*', 'packages/*']
  ```
- `pnpm -r <script>` runs across packages; `--filter <pkg>` targets one.
- Reference internal packages with `"workspace:*"`.

## Docker / CI
- Order layers for cache hits: copy `package.json` + `pnpm-lock.yaml`, run
  `pnpm install --frozen-lockfile`, then copy the rest.
  ```dockerfile
  FROM node:24-slim
  RUN corepack enable
  COPY package.json pnpm-lock.yaml ./
  RUN pnpm install --frozen-lockfile
  ```
- Optional faster CI caching: mount the store with
  `RUN --mount=type=cache,target=/pnpm/store pnpm install --frozen-lockfile`.
