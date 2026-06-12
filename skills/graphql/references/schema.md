## SDL Syntax Cheatsheet

```graphql
type User {
  id: ID!           # ! = non-nullable
  name: String!
  email: String     # nullable — may be null
  posts: [Post!]!   # non-null list of non-null Posts
  role: Role
}

enum Role { ADMIN MEMBER GUEST }

interface Node { id: ID! }        # shared contract; types declare `implements Node`
union SearchResult = User | Post  # exactly one of the listed types

type Query {                      # read-only entrypoint (required)
  user(id: ID!): User
  users(filter: UserFilter, limit: Int = 10, offset: Int = 0): [User!]!
}

type Mutation { createUser(input: CreateUserInput!): User! }
type Subscription { userCreated: User! }

input CreateUserInput {           # inputs are separate from output types
  name: String!
  email: String!
}
```

### Nullability — the two-layer rule

| Declaration | Meaning |
|---|---|
| `[Post]` | nullable list, nullable items |
| `[Post!]` | nullable list, non-null items |
| `[Post]!` | non-null list, nullable items |
| `[Post!]!` | non-null list, non-null items |

Read both `!` positions independently — they are separate assertions.

### Nullability cascade

If a resolver throws and the field is non-null (`!`), the null propagates **up** through
every non-null ancestor until it hits a nullable boundary. The response will have partial
data plus an entry in `errors[]`. To limit blast radius, make resolvers nullable unless
you are certain they can never fail.

---

## Introspection Queries

```graphql
# All types in the schema
{ __schema { types { name kind } } }

# Fields on a specific type
{ __type(name: "User") {
    fields { name type { name kind ofType { name kind } } }
  }
}

# All available root queries
{ __schema { queryType { fields { name args { name type { name } } description } } } }

# Check whether a field exists (null response = not found)
{ __type(name: "Post") { fields { name } } }

# Directives available
{ __schema { directives { name locations args { name } } } }
```

### Reading a schema SDL file quickly

```bash
grep '^type '         schema.graphql    # all types
grep -A30 '^type Query' schema.graphql  # all root queries
grep 'User[!?\[]'     schema.graphql    # every field that returns User
grep '@deprecated'    schema.graphql    # find deprecated fields
grep -A20 '^type Order' schema.graphql | grep -c '!$'  # count non-nullable fields
```
