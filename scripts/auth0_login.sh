#!/usr/bin/env bash
set -euo pipefail

keychain_get() {
  security find-generic-password -a codex -s "$1" -w 2>/dev/null || true
}

# Prefer Keychain; fallback to ~/.secrets/codex/auth0.env; then env vars
A0_DOMAIN="$(keychain_get AUTH0_DOMAIN)"
A0_CLIENT_ID="$(keychain_get AUTH0_CLIENT_ID)"
A0_CLIENT_SECRET="$(keychain_get AUTH0_CLIENT_SECRET)"

if [[ -z "${A0_DOMAIN}" || -z "${A0_CLIENT_ID}" || -z "${A0_CLIENT_SECRET}" ]]; then
  if [[ -f "${HOME}/.secrets/codex/auth0.env" ]]; then
    # shellcheck disable=SC1090
    source "${HOME}/.secrets/codex/auth0.env"
    A0_DOMAIN="${AUTH0_DOMAIN:-${A0_DOMAIN:-}}"
    A0_CLIENT_ID="${AUTH0_CLIENT_ID:-${A0_CLIENT_ID:-}}"
    A0_CLIENT_SECRET="${AUTH0_CLIENT_SECRET:-${A0_CLIENT_SECRET:-}}"
  fi
fi

A0_DOMAIN="${A0_DOMAIN:-${AUTH0_DOMAIN:-}}"
A0_CLIENT_ID="${A0_CLIENT_ID:-${AUTH0_CLIENT_ID:-}}"
A0_CLIENT_SECRET="${A0_CLIENT_SECRET:-${AUTH0_CLIENT_SECRET:-}}"

if [[ -z "${A0_DOMAIN}" || -z "${A0_CLIENT_ID}" || -z "${A0_CLIENT_SECRET}" ]]; then
  echo "Missing AUTH0 credentials. Use Keychain bootstrap or set ~/.secrets/codex/auth0.env:"
  echo "  AUTH0_DOMAIN=your-tenant.us.auth0.com"
  echo "  AUTH0_CLIENT_ID=..."
  echo "  AUTH0_CLIENT_SECRET=..."
  exit 2
fi

if ! command -v auth0 >/dev/null; then
  echo "Auth0 CLI not found. Install: brew tap auth0/auth0 && brew install auth0"
  exit 1
fi

auth0 login \
  --domain "$A0_DOMAIN" \
  --client-id "$A0_CLIENT_ID" \
  --client-secret "$A0_CLIENT_SECRET" \
  --no-input

echo "✅ Auth0 CLI logged into tenant: $A0_DOMAIN"
