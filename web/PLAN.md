# Web — PLAN

**Prereq Gate:** `/service` deployed and passing tests.

## Stack
- React + Vite + TypeScript
- Tailwind CSS (glassmorphism)
- Auth0 React SDK (PKCE)
- React Query for API calls

## Auth0 Setup
From Auth0 Application (SPA):
- Domain, Client ID
- Allowed Callback URLs: `http://localhost:5173/callback` (and prod)
- Allowed Web Origins: `http://localhost:5173` (and prod)
- Request `audience` = your API identifier

## ENV
```
VITE_AUTH0_DOMAIN=TENANT.us.auth0.com
VITE_AUTH0_CLIENT_ID=... 
VITE_AUTH0_AUDIENCE=dodeck-api
VITE_API_BASE_URL=https://<apprunner-url-or-custom-domain>
```

## UI
- Left panel: decks list + search + "New Deck"
- Right panel: Dos with add/edit/delete/complete
- Owner-only "Share" panel (add/remove collaborator)

## Deploy
- S3 static website + CloudFront + ACM (via Terraform).
