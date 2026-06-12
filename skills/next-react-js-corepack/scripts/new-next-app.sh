#!/usr/bin/env bash
# Scaffold a best-practice Next.js (App Router + TypeScript) app with pnpm.
# Usage: ./new-next-app.sh [app-name]
set -euo pipefail

APP_NAME="${1:-web}"

corepack enable

# create-next-app flags: App Router, TS, Tailwind, ESLint, src-less app dir.
pnpm dlx create-next-app@latest "$APP_NAME" \
  --ts --app --eslint --tailwind --use-pnpm \
  --src-dir false --import-alias "@/*" --no-turbopack

cd "$APP_NAME"

# Pin the package manager for reproducible installs.
node -e "const p=require('./package.json');p.packageManager='pnpm@'+require('child_process').execSync('pnpm -v').toString().trim();require('fs').writeFileSync('./package.json',JSON.stringify(p,null,2)+'\n')"

echo "Created $APP_NAME. Next: cd $APP_NAME && pnpm dev"
