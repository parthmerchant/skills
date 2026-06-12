## Variables

Always use variables — never interpolate values into query strings.

```graphql
query GetUser($id: ID!) {
  user(id: $id) { name email }
}
# variables: { "id": "123" }
```

Variables are typed and validated before execution. String interpolation bypasses
validation and opens injection surface.

---

## Aliases

Fetch the same field twice with different arguments.

```graphql
{
  activeUsers: users(filter: { status: ACTIVE }) { id name }
  adminUsers:  users(filter: { role: ADMIN })   { id name }
}
```

---

## Fragments

```graphql
fragment UserCard on User { id name email role }

query ListUsers { users { ...UserCard } }
query GetUser($id: ID!) { user(id: $id) { ...UserCard posts { title } } }
```

Inline fragments handle unions and interfaces:

```graphql
{
  search(query: "alice") {
    __typename          # always include on unions
    ... on User { name email }
    ... on Post { title body }
  }
}
```

---

## Directives

```graphql
query GetUser($withPosts: Boolean!, $skipRole: Boolean!) {
  user(id: "1") {
    name
    posts @include(if: $withPosts) { title }
    role  @skip(if: $skipRole)
  }
}
```

`@include(if: Boolean)` — include field when true  
`@skip(if: Boolean)` — skip field when true  
`@deprecated(reason: String)` — schema-level; marks a field for removal

---

## Pagination — cursor over offset

```graphql
query ListUsers($cursor: String) {
  users(first: 20, after: $cursor) {
    edges {
      node { id name email }
      cursor
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

Offset pagination breaks under concurrent inserts/deletes. Cursor pagination
is stable — use it for any list that can change.

---

## Mutations

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    id name email   # always return the created/updated object
  }
}
# variables: { "input": { "name": "Alice", "email": "a@b.com" } }
```

- Mutations in a single request execute **sequentially** (unlike query fields which run in parallel).
- Return the mutated object, not just a boolean — clients need the new state to update caches.
- Use `input` wrapper types so you can add fields later without a breaking change.

---

## Subscriptions

```graphql
subscription OnUserCreated {
  userCreated { id name email }
}
```

Subscriptions run over WebSocket. Two protocols exist and are **incompatible**:
- `graphql-ws` (modern, default in Apollo Server 4+)
- `subscriptions-transport-ws` (legacy; Apollo Server 2/3)

Check server docs to confirm which protocol the endpoint speaks.

---

## Best Practices Checklist

- Named operations — anonymous queries are invisible in server logs and APM
- Request only needed fields — overfetching wastes bandwidth and slows queries
- Include `id` on every object — clients need it for cache keys
- Include `__typename` on unions/interfaces — prevents runtime errors in clients
- Use fragments to share field sets across operations — single source of truth
- Use cursor pagination for mutable lists
- Use `input` types for mutation arguments — easier to evolve
