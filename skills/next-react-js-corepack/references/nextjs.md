# Next.js (App Router) — fundamentals

## Components
- **Server Components by default.** They run only on the server: fetch data, read
  secrets, keep large deps out of the client bundle.
- Add `"use client"` only for state, effects, event handlers, or browser APIs.
  Push it to the **leaves** of the tree, not the root.
- Server Components can import and render Client Components, not vice-versa. Pass
  data down as serializable props.

## Routing (`app/`)
- Folders = routes. `page.tsx` = UI, `layout.tsx` = shared shell, `route.ts` = API
  handler, `loading.tsx` / `error.tsx` = streaming + error boundaries.
- Dynamic segments: `app/posts/[id]/page.tsx` → `params.id`.
- Route handlers (`app/api/.../route.ts`) export `GET`/`POST`/… and read runtime
  env. Use them to proxy or hide backends.

## Data fetching
- Fetch in Server Components with `await fetch(...)`; Next caches and dedupes.
- Control caching: `fetch(url, { cache: 'no-store' })` or
  `{ next: { revalidate: 60 } }`. Mark a route dynamic with
  `export const dynamic = 'force-dynamic'`.
- Mutations: prefer **Server Actions** (`'use server'`) or route handlers.

## Config & env
- `next.config.mjs`: `output: 'standalone'` for slim Docker images;
  `reactStrictMode: true`.
- **`rewrites()`/`redirects()` are evaluated at build time** — never interpolate a
  runtime value (e.g. an API host) into them. Proxy via a route handler instead.
- `NEXT_PUBLIC_*` is inlined into the client bundle at build → public only.
  Everything else is server-only and read at runtime.

## Production
- `next build` then `next start`, or run `.next/standalone/server.js`.
- Keep client JS small: dynamic-import heavy/below-the-fold components with
  `next/dynamic`; use `next/image` and `next/font`.
