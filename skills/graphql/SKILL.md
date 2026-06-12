---
name: graphql
description: GraphQL best practices, schema interpretation, querying patterns, CLI tools, and common gotchas. Use when writing queries/mutations, reading an SDL schema, debugging GraphQL errors, or setting up GraphQL tooling.
---

# GraphQL

App-agnostic fundamentals. Read the reference that matches your task.

## References
- `references/schema.md` — SDL syntax, nullability, types, interfaces, unions, introspection
- `references/querying.md` — variables, aliases, fragments, directives, pagination, mutations, subscriptions
- `references/cli.md` — graphqurl, graphql-inspector, rover, get-graphql-schema, curl
- `references/troubleshooting.md` — decoding errors, N+1, schema diffing, gotchas

## TL;DR
- `!` = non-null. `[Post!]!` has two layers — both list and items are non-null.
- Always use **named operations** and **variables** — never interpolate user data into query strings.
- GraphQL always returns **HTTP 200**; errors live in `response.errors[]`, not the status code.
- **Introspection** is often disabled in production — run tooling against staging or a schema registry.
- Include `id` and `__typename` on every object you fetch — clients use them for caching and union discrimination.
- N+1 is the most common performance bug; fix it server-side with DataLoader/batching.
