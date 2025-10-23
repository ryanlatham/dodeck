# Auth0 Setup

1. Create an **Application → Single Page App**.
   - **Grant**: Authorization Code with **PKCE**.
   - **Allowed Callback URLs**: `http://localhost:5173/callback` (add prod later)
   - **Allowed Logout URLs**: `http://localhost:5173/`
   - **Allowed Web Origins**: `http://localhost:5173`
   - Copy **Domain** and **Client ID** into `web/.env`.

2. Create an **API** (Identifier = your audience; e.g., `dodeck-api`).
   - Signing Algorithm: RS256
   - Copy **Identifier** and issuer URL into `service/.env` (`AUTH0_AUDIENCE`, `AUTH0_ISSUER`).

3. **Action (Post-Login)** to inject namespaced claims:
```js
exports.onExecutePostLogin = async (event, api) => {
  if (event.authorization) {
    api.accessToken.setCustomClaim("https://dodeck.app/email", (event.user.email || "").toLowerCase());
    api.accessToken.setCustomClaim("https://dodeck.app/email_verified", !!event.user.email_verified);
  }
};
```

4. In the SPA, request audience and scopes: `openid profile email`.
