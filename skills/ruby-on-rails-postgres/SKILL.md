---
name: ruby-on-rails-postgres
description: Core best practices for a Ruby on Rails API with PostgreSQL and a GraphQL layer (graphql-ruby). Use when scaffolding or reviewing a Rails GraphQL API, ActiveRecord models/migrations, or Postgres schema design.
---

# Rails · PostgreSQL · GraphQL

App-agnostic fundamentals. Read the reference that matches your task; run a
script to bootstrap.

## References
- `references/rails.md` — API-only Rails, ActiveRecord, migrations, validations
- `references/postgres.md` — schema design, indexing, constraints, arrays/JSONB
- `references/graphql.md` — graphql-ruby types, queries, mutations, N+1

## Scripts
- `scripts/new-rails-graphql-api.sh [name]` — new API-only Rails app + graphql-ruby
- `scripts/db-setup.sh` — create, migrate, and seed the database (idempotent)

## TL;DR
- `rails new --api -d postgresql`. Keep business rules in **model validations**,
  not controllers/resolvers.
- Every schema change is a **migration**; add DB-level constraints + indexes
  (FKs, NOT NULL, unique) — don't rely on app validations alone.
- GraphQL: thin resolvers, one schema, return `{ node, errors: [String] }` from
  mutations, and kill N+1 with `includes` or a dataloader/batch loader.
- Type names drop the `Type` suffix (`ProspectInputType` class → `ProspectInput`).
