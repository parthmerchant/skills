---
name: docker-compose-full-stack
description: Scaffold a production-ready 3-tier app — React SPA served by nginx, FastAPI backend, PostgreSQL database — all wired in Docker Compose with health checks, a justfile, and an E2E test suite.
---

# Docker Compose Full-Stack

React 18 + Vite + MUI + Tailwind → nginx, FastAPI + psycopg2 → PostgreSQL 15. Launch with `just launch`.

## References
- `references/backend.md` — FastAPI patterns: DB config, startup retry, row_to_dict, full CRUD routes
- `references/frontend.md` — Vite Dockerfile, nginx SPA proxy, Tailwind + MUI config, package.json
- `references/compose-justfile.md` — docker-compose.yml, justfile, E2E test suite, common pitfalls
- `references/css-mui.md` — CSS architecture in index.css, MUI theme, dark-mode wiring

## TL;DR
- Ask 5 inputs: app name/slug, data model + fields, UI layout, ports, auth needed.
- Backend retries DB 15× (2 s apart) + `condition: service_healthy` in compose.
- Call `row_to_dict(row, cur)` **before** `cur.close()` — `cur.description` is None after close.
- Set `important: '#root'` in Tailwind config so utilities override MUI injected styles.
- Omit the `version:` key from `docker-compose.yml` (Compose V2 deprecates it).
