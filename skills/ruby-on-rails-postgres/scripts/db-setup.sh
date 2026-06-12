#!/usr/bin/env bash
# Create, migrate, and seed the database. Idempotent: safe to re-run.
# Run from a Rails app root. Reads DB connection from config/database.yml (ENV).
set -euo pipefail

# db:create is a no-op (and harmless error) if the database already exists.
bin/rails db:create 2>/dev/null || true
bin/rails db:migrate

# Seed only when empty, so re-runs don't duplicate data (seeds.rb should also
# guard itself). Adjust the model name to your schema.
bin/rails runner 'Rails.application.load_seed if ActiveRecord::Base.connection.tables.any? && (defined?(Prospect) ? Prospect.count.zero? : true)' \
  || bin/rails db:seed

echo "Database ready: $(bin/rails runner 'print ActiveRecord::Base.connection.current_database')"
