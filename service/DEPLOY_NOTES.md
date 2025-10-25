# Deploy Notes — DoDeck Service

## Container
- Image exposes port **8080** (`uvicorn --port 8080`).
- Use health check `GET /healthz`.

## Required Environment Variables
| Name | Description |
| --- | --- |
| `AUTH0_ISSUER` | Auth0 tenant issuer URL (e.g. `https://TENANT.us.auth0.com/`). |
| `AUTH0_AUDIENCE` | Auth0 API identifier (e.g. `dodeck-api`). |
| `TABLE_NAME` | DynamoDB table name (default `DoDeck`). |
| `AWS_REGION` | AWS region for DynamoDB (e.g. `us-west-2`). |
| `LOG_LEVEL` | Optional log level (`info` default). |
| `REQUIRE_EMAIL_VERIFIED` | `true/false`; controls collaborator email verification requirement. |
| `CORS_ALLOWED_ORIGINS` | Comma-delimited origins for browser clients. |

## Optional / Local Config
| Name | Purpose |
| --- | --- |
| `DYNAMODB_ENDPOINT_URL` | Override DynamoDB endpoint for local testing (`http://localhost:8000`). |
| `AUTH0_JWKS_JSON` / `AUTH0_JWKS_PATH` | Provide JWKS in non-public environments. |
| `ENVIRONMENT` | Controls docs availability (`docs` disabled when set to `prod`). |

## AWS App Runner
- Configure App Runner health check path `/healthz`.
- Provide IAM role with permissions to read/write the `DoDeck` DynamoDB table.
- Store secrets (Auth0 issuer/audience) in AWS Secrets Manager and map to env vars.
- Ensure outbound HTTPS access to Auth0 JWKS endpoint if not using overrides.
- Observability configuration streams traces to AWS X-Ray; instrument FastAPI to emit spans to take advantage of it.

## Auth0 Configuration
- API (Machine-to-machine):
  - Identifier → `dodeck-api` (matches `AUTH0_AUDIENCE`).
  - Signing algorithm → RS256.
- Post-login Action injects namespaced claims:
  - `https://dodeck.app/email`
  - `https://dodeck.app/email_verified`
- Terraform-managed Secrets Manager entries (per environment):
  - `/${project}/service/auth0_issuer` → `AUTH0_ISSUER`
  - `/${project}/service/auth0_audience` → `AUTH0_AUDIENCE`

## Deployment Checklist
1. Build and push image to ECR (`${project}-service` repo) with deploy tag (e.g. `git sha`).
2. Update Terraform variable file or pipeline secrets with:
   - `auth0_issuer`
   - `auth0_audience`
   - `cors_allowed_origins` (comma list)
3. From `infra/terraform/envs/dev/`:
   ```bash
   terraform init
   terraform plan -var 'aws_region=us-west-2' -var 'auth0_issuer=...' -var 'auth0_audience=...'
   terraform apply -var 'aws_region=us-west-2' -var 'auth0_issuer=...' -var 'auth0_audience=...'
   ```
4. Record outputs:
   - `service_url` (public HTTPS endpoint)
   - `table_name`
   - `auth0_*` secret names
5. Update CI/CD to push new image tag and trigger App Runner auto deployment.
6. Smoke test:
   - `curl $service_url/healthz`
   - Authenticated CRUD via integration script.
   - Current dev URL: `https://skcdqfw5pt.us-west-2.awsapprunner.com`
   - Current staging URL: `https://pi57pcetyg.us-west-2.awsapprunner.com`
   - Production URL will be recorded after first prod deploy.

## CI/CD Credentials & Automation
- **Preferred:** GitHub Actions OIDC → IAM role (see `docs/agents/decisions.md`). Create role `dodeck-service-deploy` with trust policy for `token.actions.githubusercontent.com` and attach permissions for:
  - ECR (`ecr:BatchCheckLayerAvailability`, `ecr:CompleteLayerUpload`, `ecr:InitiateLayerUpload`, `ecr:PutImage`, `ecr:UploadLayerPart`, `ecr:GetAuthorizationToken`)
  - App Runner & supporting services (Terraform-managed IAM policies already cover runtime access).
  - Secrets Manager (create/update Auth0 secrets) plus S3/DynamoDB for Terraform state.
- Configure repository/environment secrets:
  - `AWS_DEPLOY_ROLE_ARN`
  - `TF_STATE_BUCKET`, `TF_STATE_KEY`, `TF_STATE_LOCK_TABLE`
  - `AUTH0_ISSUER`, `AUTH0_AUDIENCE`
- Repository variables:
  - `AWS_REGION` (e.g., `us-west-2`)
  - `ECR_REPOSITORY` (defaults to `dodeck-service` if unset)
  - `CORS_ALLOWED_ORIGINS`
- Trigger deployment via `workflow_dispatch` or tags; job `deploy-<env>` builds, pushes image, and runs Terraform with the new tag.
- Runtime `ENVIRONMENT` value is provided via Terraform (`dev`, `staging`, etc.) and surfaces in `/healthz` responses.
 - Configure GitHub environments for `staging` and `prod` with required reviewers and secrets per the promotion policy.

**Current AWS values (dev account 309090259750):**
- `AWS_DEPLOY_ROLE_ARN` = `arn:aws:iam::309090259750:role/dodeck-service-deploy`
- `TF_STATE_BUCKET` = `dodeck-terraform-state`
- `TF_STATE_KEY` = `service/dev/terraform.tfstate`
- `TF_STATE_LOCK_TABLE` = `dodeck-terraform-locks`
