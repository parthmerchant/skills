# Ruby on Rails (API) — fundamentals

## App shape
- `rails new app --api -d postgresql` → no views/cookies/session middleware.
- Controllers inherit `ActionController::API`. Keep them thin: parse input,
  call a model/service, render. No business logic.

## ActiveRecord models
- One model per table; associations declare the graph:
  ```ruby
  has_many :activities, dependent: :destroy
  belongs_to :prospect
  ```
- **Validations are the source of truth** for business rules:
  ```ruby
  validates :email, presence: true
  validates :stage, inclusion: { in: STAGES }
  validate :custom_rule, if: -> { ... }
  ```
  Use `save`/`save!` (raises `RecordInvalid`); check `record.errors.full_messages`.
- Callbacks (`before_validation`, `before_save`) for normalization — keep them
  small and side-effect-free where possible.
- Scopes for reusable queries: `scope :in_stage, ->(s) { where(stage: s) }`.

## Migrations
- Every schema change is a timestamped migration in `db/migrate/`.
- Add DB-level guarantees, not just app validations:
  ```ruby
  t.string :email, null: false
  t.references :prospect, null: false, foreign_key: { on_delete: :cascade }
  add_index :prospects, :stage
  add_index :users, :email, unique: true
  ```
- `bin/rails db:create db:migrate db:seed`. `db:prepare` is idempotent (create +
  migrate + seed-on-create). Migrations are reversible (`change`) when possible.

## Config & env
- `config/database.yml` reads `ENV` (host, user, password) — never hardcode creds.
- Production needs `SECRET_KEY_BASE`; log to STDOUT for containers.
- Boot order in Docker: wait for the DB, run migrations in an entrypoint, then
  start Puma.

## Performance
- Avoid N+1: `Model.includes(:assoc)` to eager-load.
- Select only what you need; paginate large lists; index columns you filter/sort on.
