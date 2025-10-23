## [2025-10-22 22:30 PT] Provision remote state + deploy IAM role

**Goal**
- Stand up Terraform remote state storage and CI deploy role per pipeline design.

**Context**
- Files/Commands: AWS CLI, infra/terraform/STATE_SETUP.md, docs/agents/decisions.md, service/DEPLOY_NOTES.md
- Related checkpoint: 2025-10-22_08-40-PT

**Plan**
- [x] Create S3 state bucket + enable versioning/encryption
- [x] Create DynamoDB lock table
- [x] Configure GitHub OIDC provider and deploy IAM role with scoped policy
- [x] Update docs/todo with actual resource identifiers

**Work Log**
- 00:04 `aws s3api create-bucket` + enabled versioning/encryption for `dodeck-terraform-state`
- 00:08 `aws dynamodb create-table` for `dodeck-terraform-locks` + wait for ACTIVE
- 00:12 Added OIDC provider (`token.actions.githubusercontent.com`) and IAM role `dodeck-service-deploy` with inline policy for S3/DynamoDB/ECR/AppRunner/IAM/SSM access
- 00:20 Updated deployment docs with ARN/secret names, logged decision, refreshed TODO; validated config via `terraform init -backend=false` + `validate`

**Result**
- done — see checkpoint docs/agents/checkpoints/2025-10-22_22-30-PT.md

**Evidence**
- `aws s3api create-bucket --bucket dodeck-terraform-state --region us-west-2 ...`
- `aws dynamodb create-table --table-name dodeck-terraform-locks ...`
- `aws iam create-open-id-connect-provider ...`
- `aws iam create-role --role-name dodeck-service-deploy ...`
- `AWS_REGION=us-west-2 terraform -chdir=infra/terraform/envs/dev validate`

**Next**
- [ ] Populate GitHub secrets (`AWS_DEPLOY_ROLE_ARN`, `AUTH0_*`, `TF_STATE_*`) and vars (`AWS_REGION`, `ECR_REPOSITORY`, `CORS_ALLOWED_ORIGINS`)
- [ ] Push `_terraform/backend.hcl` and run workflow_dispatch to verify deploy job (dry run ok)
- [ ] Define promotion gates (dev → staging → prod) once staging env ready

**Handoff**
- Current state: ready
- Owner (if any): codex
- Timebox remaining: 0m
## [2025-10-22 08:18 PT] Prep infra & CI for service deploy

**Goal**
- Provision Terraform pieces for DynamoDB/App Runner + wire CI and operator docs.

**Context**
- Files: infra/terraform/modules/**, infra/terraform/envs/dev/**, .github/workflows/service.yml, docs/agents/{todo,decisions}.md
- Prior checkpoints: 2025-10-22_08-05-PT

**Plan**
- [x] enhance Terraform modules with IAM + SSM config
- [x] update CI workflow to run tests with dynamodb-local & build image artifact
- [x] document Auth0 prod mapping & deployment checklist

**Work Log**
- 00:05 reviewed Terraform modules; added IAM role + SSM wiring; installed tfenv to satisfy >=1.6 requirement; ran `terraform -chdir=infra/terraform/envs/dev init`
- 00:18 updated env composition with secure SSM parameters, outputs, and formatting; captured `.terraform.lock.hcl`
- 00:25 patched service CI workflow to compose dynamodb-local, export PYTHONPATH, and build docker image
- 00:32 expanded `DEPLOY_NOTES.md` with Auth0 mapping + deployment checklist; refreshed TODO/decision entries
- 00:38 ran `terraform -chdir=infra/terraform/envs/dev init -backend=false` and `AWS_REGION=us-west-2 terraform -chdir=infra/terraform/envs/dev validate`

**Result**
- done — see checkpoint docs/agents/checkpoints/2025-10-22_08-40-PT.md

**Evidence**
- `terraform -chdir=infra/terraform/envs/dev init`
- `terraform -chdir=infra/terraform/envs/dev init -backend=false`
- `AWS_REGION=us-west-2 terraform -chdir=infra/terraform/envs/dev validate`
- `.github/workflows/service.yml` updated with docker compose + build steps
- `service/DEPLOY_NOTES.md` updated with Auth0 mapping/checklist

**Next**
- [ ] Provision S3 state bucket and DynamoDB lock table in AWS
- [ ] Create GitHub OIDC IAM role + configure repository secrets/vars
- [ ] Trigger `service-ci` deploy job via `workflow_dispatch` once secrets are in place

**Handoff**
- Current state: in progress
- Owner (if any): codex
- Timebox remaining: 60m

## [2025-10-22 08:05 PT] Stand up v1 service API

**Goal**
- Deliver FastAPI v1 deck/do endpoints with Auth0 + DynamoDB per PLAN.

**Context**
- Files: service/src/main.py, service/src/api/v1/decks.py, service/src/repository.py, service/tests/test_decks_integration.py
- Prior checkpoints/decisions: n/a — first entry

**Plan**
- [x] Set up Python 3.12 environment and install dependencies
- [x] Implement Auth0 security + DynamoDB data layer
- [x] Expand integration tests and run full suite
- [x] Build docker image and validate health/auth locally

**Work Log**
- 00:05 Brew-installed python3.12, created virtualenv, installed requirements
- 00:18 Added Auth0 settings/security wiring and dependency helpers; rationale: enable JWKS overrides for tests and local/dev parity
- 00:40 Implemented repository functions for deck/do CRUD + sharing transactions, aligning with single-table model
- 00:52 Built FastAPI routers for decks/dos with owner vs collaborator checks
- 01:10 Created pytest fixtures (RSA JWKS, dynamodb-local) and integration coverage for owner/collaborator/unverified flows
- 01:25 Started dynamodb-local via docker-compose; `PYTHONPATH=src pytest` succeeded
- 01:35 Built docker image, ran container to verify `/healthz` and 401 on unauthenticated `/v1/decks`
- 01:40 Authored `.env` example and `DEPLOY_NOTES.md` for App Runner handoff

**Result**
- done — see checkpoint docs/agents/checkpoints/2025-10-22_08-05-PT.md

**Evidence**
- Test: `PYTHONPATH=src pytest` (5 passed)
- Docker: `docker build -t dodeck-service:local .`
- Runtime: `curl http://localhost:8080/healthz` → 200, `curl http://localhost:8080/v1/decks` → 401

**Next**
- [ ] Provision AWS infra (DynamoDB table, App Runner service, secrets)
- [ ] Wire CI to start dynamodb-local, run pytest, build/push image
- [ ] Document Auth0 production setup + env var mapping for operators

**Handoff**
- Current state: ready
- Owner (if any): codex
- Timebox remaining: 0m
