#!/usr/bin/env bash
# Scaffold a new API-only Rails app with PostgreSQL and graphql-ruby.
# Usage: ./new-rails-graphql-api.sh [app-name]
set -euo pipefail

APP_NAME="${1:-api}"

# Requires Ruby + the rails gem (`gem install rails`).
rails new "$APP_NAME" --api -d postgresql --skip-test --skip-action-cable

cd "$APP_NAME"

# Add graphql-ruby + the dev explorer.
bundle add graphql
bundle add graphiql-rails --group development

# Generates Schema, QueryType, MutationType, base types, and the
# GraphqlController with a POST /graphql route.
bin/rails generate graphql:install

echo "Rails GraphQL API '$APP_NAME' ready."
echo "Next: configure config/database.yml, then ./scripts/db-setup.sh"
