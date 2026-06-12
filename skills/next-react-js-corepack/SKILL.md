---
name: next-react-js-corepack
description: Core best practices for Next.js (App Router), React, Corepack, and pnpm. Use when scaffolding or reviewing a Next.js/React frontend or setting up the Node/pnpm toolchain.
---

# Next.js · React · Corepack · pnpm

App-agnostic fundamentals. Read the reference that matches your task; run a
script to bootstrap.

## References
- `references/nextjs.md` — App Router, server vs client components, data, config
- `references/react.md` — hooks, state, rendering, performance
- `references/corepack-pnpm.md` — pinning Node + pnpm, workspaces, CI

## Scripts
- `scripts/setup-node-pnpm.sh` — install Node 24 (nvm), enable corepack, pin pnpm
- `scripts/new-next-app.sh [name]` — scaffold a TypeScript Next.js app with pnpm

## TL;DR
- Pin the toolchain: Node via nvm, pnpm via corepack + `packageManager` field.
- Default to **Server Components**; add `"use client"` only where you need state,
  effects, or browser APIs.
- Never put secrets in `NEXT_PUBLIC_*`. Read runtime env in route handlers, not in
  `next.config` rewrites (those are frozen at build time).
- `pnpm install --frozen-lockfile` everywhere in CI and Docker.
