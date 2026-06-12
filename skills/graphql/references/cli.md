## graphqurl — fire queries from the terminal

```bash
npm i -g graphqurl

# Run a query
gq https://api.example.com/graphql -q '{ users { id name } }'

# With auth header
gq https://api.example.com/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -q '{ me { name } }'

# Dump full schema (introspection JSON)
gq https://api.example.com/graphql --introspect

# Save SDL to file
gq https://api.example.com/graphql --introspect > schema.json
```

---

## get-graphql-schema — SDL from any endpoint

```bash
# Outputs SDL (human-readable schema)
npx get-graphql-schema https://api.example.com/graphql > schema.graphql

# With auth
npx get-graphql-schema https://api.example.com/graphql \
  -h "Authorization=Bearer $TOKEN" > schema.graphql
```

---

## graphql-inspector — schema diffing & query validation

```bash
# Diff two schemas (breaking vs safe changes)
npx graphql-inspector diff old-schema.graphql new-schema.graphql

# Diff two live endpoints
npx graphql-inspector diff \
  https://staging.api.com/graphql \
  https://prod.api.com/graphql

# Validate query files against a schema
npx graphql-inspector validate 'queries/**/*.graphql' schema.graphql

# Check for deprecated field usage
npx graphql-inspector similar schema.graphql
```

---

## rover (Apollo) — schema registry

```bash
npm i -g @apollo/rover

# Introspect a local or remote endpoint
rover graph introspect https://api.example.com/graphql

# Publish schema to Apollo Studio
rover graph publish my-graph@current --schema schema.graphql

# Diff against published schema
rover graph check my-graph@current --schema schema.graphql
```

---

## Raw curl

```bash
# Simple query
curl -s -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id name } }"}' | jq .

# Query with variables
curl -s -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetUser($id: ID!) { user(id: $id) { name } }",
    "operationName": "GetUser",
    "variables": {"id": "123"}
  }' | jq .

# Check errors only
curl -s -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users { id } }"}' | jq '.errors'

# Enable Apollo tracing (if server supports it)
curl -s -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -H "X-Apollo-Tracing: 1" \
  -d '{"query":"{ users { id name posts { title } } }"}' | jq '.extensions.tracing'
```

---

## GraphQL Playground / Altair / Insomnia

- **GraphQL Playground** — browser IDE; visit `/graphql` in Apollo Server 2 (disabled in prod by default)
- **Altair** — cross-platform desktop client; supports subscriptions, environments, collections
- **Insomnia** — REST + GraphQL client with schema sync and env variables

All three auto-fetch schema via introspection on connect — if introspection is off, import the SDL file manually.
