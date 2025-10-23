# DoDeck — ROADMAP

**Phase Gate:** Complete **/service** first (public HTTPS + passing integration tests) before starting **/web**.

## Phases
1. **Service (FastAPI + DynamoDB on App Runner)**
   - Implement endpoints, Auth0 JWT validation, data model.
   - Integration tests (pytest + httpx + dynamodb-local) must pass in CI.
   - Containerize and deploy to **App Runner** (HTTPS).

2. **Infra (Terraform)**
   - DynamoDB, ECR, App Runner, SSM/Secrets, CloudWatch.
   - (Later) S3 + CloudFront + ACM for the website.

3. **Web (React + Vite + TS + Tailwind)**
   - Auth0 login (PKCE).
   - Decks/Do UI with glass style.
   - Deploy to S3/CloudFront.

See per-directory **PLAN.md** for details and acceptance criteria.
