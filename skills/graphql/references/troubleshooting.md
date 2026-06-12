## Decoding Common Errors

### "Cannot query field X on type Y"
Field was renamed or removed. Re-introspect and grep for the type:
```bash
gq https://api.example.com/graphql --introspect | jq '.data.__schema.types[] | select(.name=="Y") | .fields[].name'
# or against a saved SDL
grep -A30 '^type Y' schema.graphql
```

### "Variable $x of type String used in position expecting Int"
Type mismatch between the variable declaration and the argument. Check the schema:
```graphql
{ __type(name: "Query") { fields { name args { name type { name kind } } } } }
```

### "Field X must not have a selection since type Z has no subfields"
You added `{ }` to a scalar field (String, Int, Boolean, etc.). Scalars have no subfields — remove the braces.

### "Unknown argument 'X' on field Y"
Argument was removed or renamed. Check current args:
```graphql
{ __schema { queryType { fields { name args { name } } } } }
```

### Null where you expect data
1. Backend resolver returned null — check server logs.
2. Field is nullable in the schema — null is a valid response.
3. Nullability cascade from a child resolver throwing — check `errors[]` for the actual message.

```bash
curl ... | jq '{data: .data, errors: .errors}'
```

---

## HTTP 200 ≠ Success

GraphQL **always** returns HTTP 200, even on partial or full errors. Never check the status code alone.

```bash
# Wrong
curl -f -X POST ...    # -f treats 4xx/5xx as failure — useless here

# Right
curl ... | jq 'if .errors then error(.errors | tostring) else .data end'
```

---

## N+1 Detection and Fix

**Symptom**: 1 query for a list, then N queries for each item's related data.

```bash
# Enable tracing to see resolver timing
curl ... -H "X-Apollo-Tracing: 1" | jq '.extensions.tracing.execution.resolvers[] | select(.duration > 10000)'
```

**Fix server-side**: DataLoader batches N individual DB lookups into 1.  
**Temporary client-side workaround**: add `@defer` on expensive fields (Apollo only) or reduce page size.

---

## Schema Mismatch Between Environments

```bash
npx graphql-inspector diff \
  https://staging.api.com/graphql \
  https://prod.api.com/graphql
```

Treat **BREAKING** changes (removed fields, changed types) as deployment blockers.
**DANGEROUS** changes (nullability relaxed, args added without defaults) need coordinated deploys.

---

## CORS Errors (Browser Only)

GraphQL endpoints must:
1. Allow `Content-Type: application/json` in CORS headers
2. Respond to `OPTIONS` preflight requests

If curl works but the browser fails, it's CORS. Fix it server-side — don't proxy in production just to paper over it.

---

## Introspection Disabled in Production

Most production APIs disable introspection. Options:
- Run tooling against staging
- Use Apollo Studio / Stellate as a schema registry
- Import a saved `schema.graphql` into your IDE/client

---

## Persisted Queries (APQ) Failures

If the server doesn't recognize an APQ hash, it returns:
```json
{ "errors": [{ "message": "PersistedQueryNotFound" }] }
```
The client must retry with the full query string. If your client doesn't implement the APQ fallback, disable APQ.

---

## Gotchas Reference

| Gotcha | Detail |
|---|---|
| Enum casing | `role: ADMIN` not `role: admin` — enums are exact-case over the wire |
| ID is always a string | Even when DB stores integers; never compare with `=== number` in JS |
| Input ≠ Type | Can't reuse `type User` as a mutation arg; define a separate `input UpdateUserInput` |
| Mutations are sequential | Multiple mutations in one request run one at a time; queries run in parallel |
| `__typename` on unions | Include it — zero cost, prevents "cannot read property of undefined" in clients |
| Subscriptions protocol | `graphql-ws` (modern) vs `subscriptions-transport-ws` (legacy) are incompatible |
| Nullability cascade | Non-null resolver throws → null bubbles up to nearest nullable ancestor |
| List nullability | `[Post!]!` has two `!` — read both; they are independent assertions |
