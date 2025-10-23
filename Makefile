SHELL := /bin/bash
.DEFAULT_GOAL := help

# Resolve secrets from Keychain at runtime (quietly). If missing there, rely on a0_import.sh envs.
A0_DOMAIN       := $(shell security find-generic-password -a codex -s AUTH0_DOMAIN -w 2>/dev/null || printf "")
A0_CLIENT_ID    := $(shell security find-generic-password -a codex -s AUTH0_CLIENT_ID -w 2>/dev/null || printf "")
A0_CLIENT_SECRET:= $(shell security find-generic-password -a codex -s AUTH0_CLIENT_SECRET -w 2>/dev/null || printf "")

.PHONY: help auth0-keychain-add auth0-login a0-import a0-export bootstrap-auth0

help:
	@echo "Targets:"
	@echo "  make auth0-keychain-add DOMAIN=... CLIENT_ID=... CLIENT_SECRET=..."
	@echo "  make auth0-login            # Non-interactive Auth0 CLI login"
	@echo "  make a0-import              # Apply config/auth0/tenant.yaml"
	@echo "  make a0-export              # Snapshot current tenant to config/auth0/export"
	@echo "  make bootstrap-auth0        # login + import"

auth0-keychain-add:
	@if [ -z "$(DOMAIN)" ] || [ -z "$(CLIENT_ID)" ] || [ -z "$(CLIENT_SECRET)" ]; then \
	  echo "Usage: make auth0-keychain-add DOMAIN=... CLIENT_ID=... CLIENT_SECRET=..."; exit 2; fi
	@./scripts/auth0_keychain_bootstrap.sh "$(DOMAIN)" "$(CLIENT_ID)" "$(CLIENT_SECRET)"

auth0-login:
	@./scripts/auth0_login.sh

a0-import:
	@AUTH0_DOMAIN="$(A0_DOMAIN)" AUTH0_CLIENT_ID="$(A0_CLIENT_ID)" AUTH0_CLIENT_SECRET="$(A0_CLIENT_SECRET)" ./scripts/a0_import.sh

a0-export:
	@mkdir -p config/auth0/export
	@AUTH0_DOMAIN="$(A0_DOMAIN)" AUTH0_CLIENT_ID="$(A0_CLIENT_ID)" AUTH0_CLIENT_SECRET="$(A0_CLIENT_SECRET)" \
	  npx a0deploy export -c config/auth0/config.json -o config/auth0/export
	@echo "✅ Exported to config/auth0/export/"

bootstrap-auth0: auth0-login a0-import
	@echo "✅ bootstrap-auth0 complete"
