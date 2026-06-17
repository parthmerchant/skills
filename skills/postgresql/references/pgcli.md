## Install

```bash
# pip (any platform)
pip install -U pgcli

# macOS
brew install pgcli

# Debian/Ubuntu
sudo apt install pgcli

# pipx (isolated, recommended for a global CLI)
pipx install pgcli
```

pgcli is a PostgreSQL client with autocompletion, syntax highlighting, and multiline editing. It speaks almost the same backslash commands as psql. See https://github.com/dbcli/pgcli.

---

## Connect

```bash
# Connection URL / DSN (most explicit)
pgcli postgres://user:pass@host:5432/dbname
pgcli postgresql://user:pass@host:5432/dbname?sslmode=require

# Discrete flags
pgcli -h localhost -p 5432 -U myuser -d mydb

# Just a database name (uses local socket + current OS user)
pgcli mydb

# Via libpq env vars (no args needed)
export PGHOST=localhost PGUSER=myuser PGPASSWORD=secret PGDATABASE=mydb
pgcli
```

Passwords can live in `~/.pgpass` (`host:port:db:user:password`, `chmod 600`) so they never appear on the command line. See https://www.postgresql.org/docs/current/libpq-pgpass.html.

---

## Named connections (favorites)

Define reusable aliases in the `[alias_dsn]` section of `~/.pgclirc`, then connect by name:

```ini
# ~/.pgclirc
[alias_dsn]
prod = postgres://readonly@prod-db.internal:5432/app
local = postgres://dev@localhost:5432/app_dev
```

```bash
pgcli prod          # resolves the alias
pgcli -D prod       # explicit DSN-alias flag
```

List or manage favorite queries from inside pgcli with `\f`.

---

## ~/.pgclirc — key settings

Created on first run; full template at https://github.com/dbcli/pgcli/blob/main/pgcli/pgclirc.

```ini
[main]
smart_completion = True       # context-aware autocomplete (tables, columns, joins)
multi_line = True             # Enter inserts newline; semicolon/Alt-Enter runs
multi_line_mode = psql
auto_expand = False           # auto-switch to expanded view for wide rows
expand = False
timing = True                 # show query duration after each statement
pager = less -SRXF            # -S = no line wrapping (scroll wide output sideways)
syntax_style = monokai
table_format = psql           # psql, fancy_grid, html, csv, ascii, etc.
destructive_warning = all     # confirm before DELETE/DROP/UPDATE without WHERE
```

---

## Autocompletion & multiline

- **Smart completion** suggests tables after `FROM`, columns after `SELECT`/`WHERE`, and even JOIN conditions based on foreign keys. Toggle live with `F2`.
- Press `Tab` to cycle suggestions; `Esc` then `Enter` to force-run.
- Refresh autocomplete metadata after a DDL change with `\refresh`.
- **Multiline**: with `multi_line = True`, statements span lines until a `;`. Use `F3` to toggle multiline on the fly. `\e` opens the current buffer in `$EDITOR`.

---

## Special / meta-commands

pgcli supports the psql backslash commands. List them all:

```sql
\?              -- list all special (backslash) commands
\h SELECT       -- SQL syntax help for a statement
\l              -- list databases
\dt             -- list tables
\d tablename    -- describe a table
\c otherdb      -- connect to another database
\timing         -- toggle query timing on/off
\x              -- toggle expanded (vertical) output; \x auto = auto
\q              -- quit
```

pgcli extras beyond psql:

```sql
\refresh        -- rebuild autocomplete cache
\f              -- list/run favorite (named) queries
\fs name query  -- save a favorite query
\fd name        -- delete a favorite query
\watch 2        -- re-run the last query every 2 seconds
```

---

## Output formats & expanded mode

```sql
\x              -- toggle vertical layout (one column per line) — great for wide rows
\x auto         -- auto-expand only when a row is too wide for the terminal

-- Change table style for the session
\T fancy_grid   -- psql | fancy_grid | html | csv | tsv | ascii | latex ...

-- One-shot CSV to a file from the shell
pgcli mydb -e "COPY (SELECT * FROM users) TO STDOUT WITH CSV HEADER" > users.csv
```

---

## \copy — import/export data

`\copy` runs client-side (file is read/written on *your* machine, no superuser needed), unlike server-side `COPY`.

```sql
-- Export a table to CSV with a header row
\copy users TO 'users.csv' WITH (FORMAT csv, HEADER)

-- Export the result of a query
\copy (SELECT id, email FROM users WHERE active) TO 'active.csv' WITH (FORMAT csv, HEADER)

-- Import a CSV into a table
\copy users FROM 'users.csv' WITH (FORMAT csv, HEADER)
```

See https://www.postgresql.org/docs/current/sql-copy.html.

---

## Running .sql files & non-interactive use

```bash
# Run a script file
pgcli mydb -f migration.sql

# Run a single statement and exit (great for scripting)
pgcli mydb -e "SELECT count(*) FROM users;"

# Pipe SQL in
echo "SELECT now();" | pgcli mydb

# From inside pgcli, run a file:
\i /path/to/script.sql
\ir relative_to_current_file.sql
```

---

## Pager

Wide/long output is sent to the pager (`less` by default). The recommended invocation avoids line-wrapping so you can scroll wide rows horizontally:

```ini
[main]
pager = less -SRXF
```

Disable paging for a session with `\pset pager off` (or set `PAGER`/`enable_pager`).

---

## pgcli vs psql — quick contrast

| Task | pgcli | psql |
|------|-------|------|
| Autocomplete | built-in, smart | none |
| Refresh metadata | `\refresh` | reconnect / `\d` |
| Favorite queries | `\f` / `\fs` | no equivalent |
| Re-run query loop | `\watch N` | `\watch N` (same) |
| Set output format | `\T fancy_grid` | `\pset format` |
| Most `\d*`, `\l`, `\x`, `\timing`, `\copy`, `\i`, `\c` | same | same |

When a script targets psql-only features (e.g. `\gset`, `\if` scripting), run it with `psql` instead.

---

## Docs
- pgcli home — https://www.pgcli.com/
- pgcli source & full `pgclirc` — https://github.com/dbcli/pgcli
- libpq connection strings — https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
- `.pgpass` — https://www.postgresql.org/docs/current/libpq-pgpass.html
- `COPY` — https://www.postgresql.org/docs/current/sql-copy.html
