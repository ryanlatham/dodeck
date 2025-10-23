#!/usr/bin/env bash
set -euo pipefail

: "${AUTH0_DOMAIN:?AUTH0_DOMAIN not set}"
: "${AUTH0_CLIENT_ID:?AUTH0_CLIENT_ID not set}"
: "${AUTH0_CLIENT_SECRET:?AUTH0_CLIENT_SECRET not set}"

if ! command -v npx >/dev/null; then
  echo "npx is required (install Node.js)."
  exit 1
fi

# Idempotently apply the config
npx a0deploy import \
  -c config/auth0/config.json \
  -i config/auth0/tenant.yaml

echo "✅ Deploy CLI import complete."
