# GraphQL (graphql-ruby) — fundamentals

## Schema shape
- One endpoint: `POST /graphql` → `Schema.execute(query, variables:, context:)`.
- One `Schema` with a `QueryType` (reads) and `MutationType` (writes). Types live
  in `app/graphql/types`, mutations in `app/graphql/mutations`.
- **Class name drops the `Type` suffix** for the GraphQL name:
  `ProspectInputType` (class) → `ProspectInput` (schema). Override with
  `graphql_name "..."` if needed.

## Types & fields
- Map models to object types; expose fields explicitly (don't auto-dump columns).
- Nullability is part of the contract: `field :name, String, null: false`.
- Add computed fields with a resolver method of the same name.
- Use input objects for create/update payloads; enums for fixed sets.

## Queries
- Resolvers stay thin — call scopes/models, return records.
- Arguments for filtering/pagination: `argument :stage, String, required: false`.

## Mutations
- Prefer plain `GraphQL::Schema::Mutation` (args are top-level) over
  `RelayClassicMutation` (wraps args under `input` + adds `clientMutationId`)
  unless you specifically want the Relay shape.
- Return a payload with the node **and** a typed error list — surface expected
  validation failures here, not as top-level errors:
  ```ruby
  field :record, Types::RecordType, null: true
  field :errors, [String], null: false

  def resolve(input:)
    r = Model.new(input.to_h)
    r.save ? { record: r, errors: [] } : { record: nil, errors: r.errors.full_messages }
  end
  ```
- Reserve top-level GraphQL errors (raise `GraphQL::ExecutionError`, or
  `rescue_from`) for exceptional/unexpected cases.

## Performance & safety
- **N+1 is the #1 GraphQL trap.** Batch with `graphql-batch` / a dataloader, or
  eager-load via `includes` in the resolver.
- Bound risk: `max_depth`, `max_complexity`, and pagination on list fields.
- Validate/authorize in resolvers or model layer; never trust client input.
- Explore with GraphiQL in development only; disable it in production.
