#!/usr/bin/env bash
set -euo pipefail

DOMAIN=${1:-}
CLIENT_ID=${2:-}
CLIENT_SECRET=${3:-}

if [[ -z "$DOMAIN" || -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
  echo "Usage: $0 <domain> <client_id> <client_secret>"
  echo "Example: $0 your-tenant.us.auth0.com abc123 ...secret..."
  exit 2
fi

# -U updates if an item already exists
security add-generic-password -a codex -s AUTH0_DOMAIN -w "$DOMAIN" -U >/dev/null
security add-generic-password -a codex -s AUTH0_CLIENT_ID -w "$CLIENT_ID" -U >/dev/null
security add-generic-password -a codex -s AUTH0_CLIENT_SECRET -w "$CLIENT_SECRET" -U >/dev/null

echo "Stored AUTH0_* in Keychain (services: AUTH0_DOMAIN / AUTH0_CLIENT_ID / AUTH0_CLIENT_SECRET)."
echo "On first use, macOS may prompt; click 'Always Allow' so future runs are hands-free."
