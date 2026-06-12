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
