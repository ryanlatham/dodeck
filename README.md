# DoDeck Monorepo

- `service/` — FastAPI service for Decks/Dos and sharing (Auth0-protected).
- `infra/` — Terraform for AWS resources (DynamoDB, ECR, App Runner, etc.).
- `web/` — React SPA (Auth0 PKCE) with glassmorphism UI.

Start with **service/**; do not begin web until the service meets Phase 1 acceptance criteria.
