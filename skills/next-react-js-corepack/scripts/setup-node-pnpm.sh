#!/usr/bin/env bash
# Install Node 24 via nvm, enable corepack, and pin pnpm.
# Usage: ./setup-node-pnpm.sh [node_major] [pnpm_version]
set -euo pipefail

NODE_MAJOR="${1:-24}"
PNPM_VERSION="${2:-latest}"

# Load nvm (supports both ~/.nvm and the XDG ~/.config/nvm location).
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] || NVM_DIR="$HOME/.config/nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" || {
  echo "nvm not found. Install: https://github.com/nvm-sh/nvm" >&2; exit 1; }

nvm install "$NODE_MAJOR"
nvm alias default "$NODE_MAJOR"
nvm use default

corepack enable
corepack prepare "pnpm@${PNPM_VERSION}" --activate

echo "node $(node -v) | npm $(npm -v) | pnpm $(pnpm -v)"
