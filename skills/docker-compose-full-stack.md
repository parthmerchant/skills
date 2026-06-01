---
title: Docker Compose Full-Stack (React + FastAPI + PostgreSQL)
description: Scaffold a production-ready 3-tier app — React SPA served by nginx, FastAPI backend, PostgreSQL database — all wired in Docker Compose with health checks, a justfile, and an E2E test suite.
icon: 🐳
tags: docker, fastapi, react, postgresql, vite, tailwind, mui, fullstack
---

# Docker Compose Full-Stack

A complete, runnable 3-tier application scaffold: a React SPA (Vite + MUI + Tailwind) served through nginx, a FastAPI backend with PostgreSQL via psycopg2, Docker Compose with proper dependency ordering, a justfile for developer workflow, and a stdlib-only E2E test suite. Launch with `just launch`.

## What you get

- **Frontend** — React 18 + Vite, built to a static bundle, served by nginx:alpine. Nginx handles SPA routing (`try_files`) and reverse-proxies `/api` to the backend so the browser never touches a different origin.
- **Backend** — FastAPI on Python 3.11-slim with uvicorn. Startup retries the DB connection up to 15× (2 s apart) so the backend survives compose start race conditions. `CREATE TABLE IF NOT EXISTS` on startup — no separate migration step needed for MVPs.
- **Database** — PostgreSQL 15 with a `pg_isready` health check. The backend container uses `condition: service_healthy` so it only starts after Postgres is actually accepting connections, not just running.
- **Docker Compose** — named network, named volume for data persistence, `depends_on` with health conditions, all images built locally.
- **Justfile** — `just launch`, `just stop`, `just logs`, `just test`, `just clean`.
- **E2E tests** — stdlib-only Python (`urllib.request`) — no extra test dependencies. Covers the full CRUD cycle: list → create → fetch → update → delete → 404.

## Tech stack decisions

| Layer | Choice | Why |
|---|---|---|
| Frontend build | Vite 4 | Fast cold starts, ESM-native, minimal config |
| Frontend serve | nginx:alpine | Multi-stage keeps image tiny; nginx handles SPA routing |
| UI components | MUI v5 + Tailwind v3 | MUI for interactive components, Tailwind for layout utilities |
| Dark mode | MUI ThemeProvider + `dark` class on `<html>` | MUI handles component theming; Tailwind's `dark:` utilities pick up the class for custom CSS |
| Backend | FastAPI + psycopg2-binary | Automatic OpenAPI docs, Pydantic validation, synchronous DB keeps it simple |
| DB client | psycopg2-binary | No asyncpg complexity needed for CRUD APIs at this scale |
| Task runner | just | More ergonomic than Makefile; no implicit tab-vs-space issues |
| E2E tests | stdlib urllib | Zero extra deps inside the container or on the host |

## Ask the user

1. **App name / domain** — slug used for container names, the database name, and the page title (e.g. `task-tracker`, `recipe-book`)
2. **Data model** — what entity are we CRUD-ing? List the fields (name, type, nullable). Include a one-sentence description of the app.
3. **UI layout preference** — single-form page, two-panel (list left + form right), or dashboard grid?
4. **Ports** — default frontend `3000`, backend `8000`; override if those are taken.
5. **Auth needed?** — if yes, note it now (adds significant scope); default is no auth.

## Project structure

```
<app-name>/
├── frontend/
│   ├── Dockerfile              # multi-stage: node build → nginx serve
│   ├── nginx.conf              # SPA routing + /api proxy
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx            # entry point — imports index.css
│       ├── index.css           # ALL visual styles: Tailwind + @layer components
│       ├── theme.js            # MUI lightTheme / darkTheme
│       ├── App.jsx             # state + API calls only; no style logic
│       └── components/
│           ├── ItemList.jsx    # left panel or list view
│           └── ItemForm.jsx    # right panel or form view
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── docker-compose.yml
├── justfile
└── tests/
    └── e2e_test.py
```

---

## Backend — `backend/main.py`

Key patterns to follow exactly:

**DB config from env vars with explicit kwargs** (not `**dict` — Pyright chokes on it):
```python
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "<app>_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )
```

**Startup with retry loop** — critical, otherwise the backend crashes while Postgres is initialising:
```python
def init_db():
    for attempt in range(15):
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id          SERIAL PRIMARY KEY,
                    name        VARCHAR(255) NOT NULL,
                    -- ... other fields ...
                    created_at  TIMESTAMP DEFAULT NOW(),
                    updated_at  TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.close(); conn.close()
            return
        except Exception as e:
            print(f"DB attempt {attempt + 1}/15: {e}")
            time.sleep(2)
    raise RuntimeError("Could not connect after 15 attempts")

@app.on_event("startup")
def startup():
    init_db()
```

**`row_to_dict` must be called BEFORE `cur.close()`** — `cur.description` becomes `None` after close:
```python
def row_to_dict(row, cur):
    return dict(zip([d[0] for d in cur.description], row))

@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    row = cur.fetchone()
    if not row:                        # check BEFORE closing
        cur.close(); conn.close()
        raise HTTPException(404, "Not found")
    result = row_to_dict(row, cur)     # capture BEFORE closing
    cur.close(); conn.close()
    return result
```

**Full CRUD router prefix `/api`:**

| Method | Path | Status |
|---|---|---|
| GET | `/api/items` | 200 |
| POST | `/api/items` | 201 |
| GET | `/api/items/{id}` | 200 / 404 |
| PUT | `/api/items/{id}` | 200 / 404 |
| DELETE | `/api/items/{id}` | 204 / 404 |

Always add CORS middleware allowing `"*"` so the Vite dev server and nginx proxy both work:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

**`requirements.txt`:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
psycopg2-binary==2.9.9
pydantic==2.5.0
```

**`backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Frontend — nginx + Vite build

**`frontend/Dockerfile`** — multi-stage is essential; the final image is ~25 MB:
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**`frontend/nginx.conf`** — two critical rules: SPA fallback for client-side routing, `/api` proxy to backend hostname (Docker network DNS resolves `backend`):
```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;   # SPA fallback
    }

    location /api {
        proxy_pass http://backend:8000;     # no trailing slash — preserves full path
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }
}
```

**`tailwind.config.js`** — `important: '#root'` scopes utilities to `#root` giving them higher specificity than MUI's injected styles. `darkMode: 'class'` pairs with toggling `.dark` on `<html>`:
```js
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  important: '#root',
  darkMode: 'class',
  theme: { extend: {} },
  plugins: [],
}
```

**`postcss.config.js`:**
```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

**`package.json` dependencies:**
```json
{
  "dependencies": {
    "@emotion/react": "^11.11.3",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.15.0",
    "@mui/material": "^5.15.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "vite": "^4.4.0"
  }
}
```

---

## CSS architecture — all styles in `src/index.css`

Zero inline styles in JSX components. All visual styles — including dark-mode variants — live in `src/index.css` as `@layer components` classes. JSX uses only Tailwind layout utilities and these class names.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  *, *::before, *::after { box-sizing: border-box; }
  html, body, #root { height: 100%; margin: 0; padding: 0; }
  body { font-family: 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
}

@layer components {
  /* App background — toggled by class on the root div */
  .app-bg      { width: 100%; height: 100vh; background: #f9fafb; transition: background 0.3s; }
  .app-bg--dark { background: #000000; }

  /* Two-panel layout */
  .app-layout  { display: flex; gap: 1.25rem; padding: 1.25rem; height: 100vh; overflow: hidden; }

  /* Sidebar */
  .sidebar               { display: flex; flex-direction: column; width: 340px; flex-shrink: 0; height: 100%; border-radius: 18px; overflow: hidden; }
  .sidebar__header       { display: flex; align-items: center; gap: 0.75rem; padding: 1.1rem 1.25rem; border-bottom: 1px solid #e5e7eb; }
  .dark .sidebar__header { border-color: #1f2937; }
  /* ... repeat pattern for sidebar__search, sidebar__list, sidebar__footer */

  /* List items */
  .item-row             { border-radius: 12px; padding: 0.7rem 0.75rem; cursor: pointer; border: 1px solid transparent; transition: all 0.15s ease; }
  .item-row:hover:not(.item-row--active) { background: rgba(0,0,0,0.04); border-color: #e5e7eb; }
  .dark .item-row:hover:not(.item-row--active) { background: rgba(255,255,255,0.04); border-color: #1f2937; }
  .item-row--active      { background: #000; border-color: #000; color: #fff; }
  .dark .item-row--active { background: #fff; border-color: #fff; color: #000; }

  /* Form panel */
  .main-panel   { flex: 1; overflow-y: auto; }
  .form-wrapper { max-width: 680px; margin: 0 auto; padding: 0.25rem 0 1.5rem; }
  .form-card    { border-radius: 18px; padding: 2rem; }
  .form-grid    { display: grid; grid-template-columns: 1fr 1fr; gap: 1.1rem; margin-top: 1.5rem; }
  .form-col-full { grid-column: 1 / -1; }
  .form-actions { display: flex; gap: 0.75rem; padding-top: 0.75rem; }
}
```

---

## MUI theme — `src/theme.js`

Two themes exported: `lightTheme` and `darkTheme`. Override component defaults here, not in JSX. Key overrides to always include:

```js
import { createTheme } from '@mui/material/styles'

const shared = {
  shape: { borderRadius: 12 },
  typography: { fontFamily: "'Inter', system-ui, sans-serif" },
  components: {
    MuiPaper:       { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiButton:      { styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } } },
    MuiTextField:   { defaultProps: { variant: 'outlined', size: 'small' } },
    MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 10 } } },
  },
}

export const lightTheme = createTheme({
  ...shared,
  palette: { mode: 'light', primary: { main: '#000' }, background: { default: '#f9fafb', paper: '#fff' } },
})

export const darkTheme = createTheme({
  ...shared,
  palette: { mode: 'dark', primary: { main: '#fff', contrastText: '#000' }, background: { default: '#000', paper: '#111' } },
})
```

---

## Dark mode wiring — `src/App.jsx`

Toggle MUI theme AND the `.dark` class on `<html>` in one call. Always initialise both from `localStorage` on first load:

```js
function initDark() {
  const stored = localStorage.getItem('theme')
  const isDark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.classList.toggle('dark', isDark)  // for Tailwind dark: variants
  return isDark
}

function toggleDark() {
  setDark(prev => {
    const next = !prev
    localStorage.setItem('theme', next ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', next)
    return next
  })
}

// In JSX:
return (
  <ThemeProvider theme={dark ? darkTheme : lightTheme}>
    <CssBaseline />
    <div className={`app-bg${dark ? ' app-bg--dark' : ''}`}>
      {/* layout */}
    </div>
  </ThemeProvider>
)
```

---

## Docker Compose — `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: <app>_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d <app>_db"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks: [app-net]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      DB_HOST: db
      DB_NAME: <app>_db
      DB_USER: postgres
      DB_PASSWORD: postgres
    depends_on:
      db:
        condition: service_healthy   # waits for pg_isready, not just container start
    networks: [app-net]

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
    networks: [app-net]

volumes:
  pgdata:

networks:
  app-net:
    driver: bridge
```

The `version:` top-level key is obsolete in Compose v2+ — omit it to avoid warnings.

---

## Justfile

```just
default:
    just --list

# Build images and start all services, then open the browser
launch:
    docker compose up --build -d
    @echo "Waiting for services..."
    sleep 12
    open http://localhost:3000

stop:
    docker compose down

logs:
    docker compose logs -f

# Run E2E suite against the running stack
test:
    docker compose up -d
    sleep 15
    python3 tests/e2e_test.py

# Tear down containers, volumes, and images
clean:
    docker compose down -v --rmi all
```

---

## E2E test suite — `tests/e2e_test.py`

stdlib-only — no `requests`, no `pytest`. Tests every HTTP status code in the CRUD cycle:

```python
#!/usr/bin/env python3
import sys, json, urllib.request, urllib.error

BASE = "http://localhost:8000"
failures = []

def req(method, path, body=None):
    url  = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    hdrs = {"Content-Type": "application/json"} if data else {}
    r    = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else None

def check(label, cond, got=None):
    if cond:
        print(f"  \033[92m✓\033[0m {label}")
    else:
        print(f"  \033[91m✗\033[0m {label}" + (f" — got: {got}" if got else ""))
        failures.append(label)

print("\n=== E2E Suite ===\n")

# 1 — list
status, body = req("GET", "/api/items")
check("GET /api/items → 200",       status == 200)
check("returns a list",             isinstance(body, list))

# 2 — create
status, body = req("POST", "/api/items", {"name": "test item", "description": "e2e"})
check("POST /api/items → 201",      status == 201)
check("has id",                     isinstance(body, dict) and "id" in body)
item_id = body["id"] if body and "id" in body else None

# 3 — fetch
if item_id:
    status, body = req("GET", f"/api/items/{item_id}")
    check("GET /api/items/:id → 200",   status == 200)
    check("id matches",                 body and body.get("id") == item_id)

# 4 — update
if item_id:
    status, body = req("PUT", f"/api/items/{item_id}", {"name": "updated"})
    check("PUT /api/items/:id → 200",   status == 200)
    check("name updated",               body and body.get("name") == "updated")

# 5 — delete
if item_id:
    status, _ = req("DELETE", f"/api/items/{item_id}")
    check("DELETE /api/items/:id → 204", status == 204)

# 6 — confirm 404 after delete
if item_id:
    status, _ = req("GET", f"/api/items/{item_id}")
    check("GET after delete → 404",     status == 404)

print(f"\n{'='*30}")
if failures:
    print(f"\033[91mFAILED: {len(failures)}\033[0m")
    [print(f"  - {f}") for f in failures]
    sys.exit(1)
else:
    print(f"\033[92mALL PASSED\033[0m")
```

---

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Backend crashes on start because DB isn't ready | Startup retry loop (15×, 2 s apart) + `condition: service_healthy` in compose |
| `row_to_dict` returns wrong data after `cur.close()` | Call `row_to_dict(row, cur)` **before** `cur.close()` — `cur.description` is `None` after close |
| `psycopg2.connect(**config_dict)` causes Pyright errors | Use explicit kwargs: `psycopg2.connect(host=..., dbname=..., user=..., password=...)` |
| Client-side routes (e.g. `/recipes/1`) return nginx 404 | `try_files $uri $uri/ /index.html` in nginx.conf |
| Tailwind utilities don't override MUI component styles | Set `important: '#root'` in `tailwind.config.js` |
| Dark mode flickers on load | Call `document.documentElement.classList.toggle('dark', isDark)` inside the `useState` initialiser, before first render |
| MUI Paper shows a gradient overlay in dark mode | Add `MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } }` to the theme |
| `version:` key in `docker-compose.yml` shows a deprecation warning | Remove the `version:` key — it is obsolete in Compose V2 |

---

## Commit and open a PR

Stage all new files under `<app-name>/`. Commit message:

```
feat: scaffold <app-name> — React + FastAPI + PostgreSQL in Docker Compose
```

Push to a new branch and open a PR.
