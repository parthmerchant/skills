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
