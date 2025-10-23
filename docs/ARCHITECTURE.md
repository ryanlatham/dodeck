# Architecture Overview

- **Auth:** Auth0 (OIDC/OAuth). SPA uses Authorization Code + PKCE. API validates RS256 JWT via JWKS.
- **Service:** FastAPI in Docker on AWS App Runner. Data in DynamoDB (single-table).
- **Website:** React + Vite + Tailwind; deployed to S3 + CloudFront.
- **CI/CD:** GitHub Actions. ECR for images; Terraform for infra.

See `service/PLAN.md`, `infra/PLAN.md`, and `web/PLAN.md` for specifics.
