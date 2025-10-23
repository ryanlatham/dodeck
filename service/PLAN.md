# DoDeck Service — PLAN

> **Gate:** Service must be deployed on a **public HTTPS endpoint** and have **passing integration tests** (CRUD + auth + sharing) **before** work starts on `/web`.

## Stack
- **Python 3.12**, **FastAPI**, **Uvicorn**
- **DynamoDB** (single-table)
- **Auth0 JWT** validation (JWKS)
- **Docker** (App Runner)
- **pytest + httpx** integration tests
- **Terraform** for AWS resources

## Data Model (DynamoDB single-table)

**Table:** `DoDeck`  
Partition keys:
- Deck item → `PK = DECK#{deckId}` / `SK = DECK`
- Do item → `PK = DECK#{deckId}` / `SK = DO#{doId}`
- Access row (owner) → `PK = ACCESS#USER#{ownerSub}` / `SK = DECK#{nameLower}#{deckId}`
- Access row (collaborator) → `PK = ACCESS#EMAIL#{emailLower}` / `SK = DECK#{nameLower}#{deckId}`

All emails and `nameLower` stored in lowercase. Collaborator access requires `email_verified = true`.

## API (v1)
- `GET /healthz` — no auth
- **Decks (owner or collaborator unless noted)**  
  - `POST /v1/decks` (owner) → `{ name }`
  - `GET /v1/decks?search=<prefix>&visibility=mine|shared|all`
  - `GET /v1/decks/{deckId}`
  - `PATCH /v1/decks/{deckId}` (owner only) → rename
  - `DELETE /v1/decks/{deckId}` (owner only)
- **Sharing (owner only)**  
  - `POST /v1/decks/{deckId}/collaborators` → `{ email }`
  - `DELETE /v1/decks/{deckId}/collaborators/{email}`
- **Dos (owner or collaborator)**  
  - `GET /v1/decks/{deckId}/dos`
  - `POST /v1/decks/{deckId}/dos` → `{ text }`
  - `PATCH /v1/decks/{deckId}/dos/{doId}` → `{ text?, completed? }`
  - `DELETE /v1/decks/{deckId}/dos/{doId}`

Errors: 400/401/403/404/409/422 as appropriate.

## Auth (Auth0)
- Validate RS256 JWT from Auth0:
  - `iss = https://<tenant>.us.auth0.com/`
  - `aud = <API Identifier>`
  - standard claims `sub`, `exp`, etc.
- Add Action in Auth0 to include namespaced claims:
  - `https://dodeck.app/email` (lowercased)
  - `https://dodeck.app/email_verified` (boolean)

## Environment
```
AUTH0_ISSUER=https://TENANT.us.auth0.com/
AUTH0_AUDIENCE=dodeck-api
REQUIRE_EMAIL_VERIFIED=true
TABLE_NAME=DoDeck
CORS_ALLOWED_ORIGINS=https://app.dodeck.com,http://localhost:5173
LOG_LEVEL=info
```

## Tests (pytest + httpx + dynamodb-local)
Required cases:
- Owner: create/list/search/rename/delete deck; add collaborator.
- Collaborator: list shared, CRUD Dos; cannot manage collaborators.
- Dos lifecycle: add/edit/toggle/delete.
- Access control: 401/403 on bad/missing tokens or unverified email.
- Delete deck cascades dos + access rows.

## Acceptance Criteria
1. All endpoints implemented with authz rules.
2. Integration tests pass locally and in CI.
3. Deployed to App Runner and reachable via HTTPS.
4. OpenAPI exposed at `/openapi.json` (OK in dev; optional in prod).
