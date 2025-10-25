## [2025-10-25 09:36 PDT] Define promotion policy & workflow gates

**Goal**
- Enforce an explicit dev → staging → prod promotion policy via GitHub Actions environment gates and documentation updates.

**Context**
- Files: .github/workflows/service.yml, docs/agents/{todo,decisions}.md, docs/agents/checkpoints/**
- Related checkpoints: 2025-10-25_09-45-PDT (secrets migration)

**Plan**
- [x] Review current workflow + GitHub environment settings to identify missing approval gates.
- [x] Update workflow to require staging deploy approval and restrict prod deploy trigger (include job dependencies/conditions).
- [x] Document promotion policy (decisions/todo) and capture checkpoint after validation.

**Work Log**
- 00:01 Created branch `feature/promotion-policy`; reviewed TODO/handoff items to confirm priority.
- 00:12 Added `promotion-policy` guard job + choice input, wired deploy job to guard outputs.
- 00:18 Ran `actionlint` to validate workflow syntax.
- 00:26 Updated docs (TODO, decisions, handoff, checkpoint, journal) to capture the new policy & backlog items.

**Result**
- done — see checkpoint docs/agents/checkpoints/2025-10-25_09-55-PDT.md

**Evidence**
- `actionlint`

**Next**
- [ ] Deliver monitoring/alerting baseline + alert routing.
- [ ] Scaffold production environment + approvals once monitoring lands.

**Handoff**
- Current state: ready
- Owner (if any): codex
- Timebox remaining: 0m

## [2025-10-25 09:10 PDT] Evaluate Auth0 secrets migration to Secrets Manager

**Goal**
- Replace SSM parameters with AWS Secrets Manager secrets for Auth0 issuer/audience and update App Runner + Terraform references accordingly.

**Context**
- Files: infra/terraform/modules/{apprunner,auth0_secrets}, infra/terraform/envs/{dev,staging}/**, service/DEPLOY_NOTES.md, docs/agents/{todo,decisions}.md
- Related checkpoints: 2025-10-22_22-30-PT (remote state + IAM setup)

**Plan**
- [x] Analyze current SSM usage and App Runner secret wiring to define requirements for Secrets Manager.
- [x] Implement Terraform module/changes to create Secrets Manager secrets + App Runner secret mapping for dev/staging; update IAM policies as needed.
- [x] Validate Terraform configs and document migration approach (decision log, TODO updates, checkpoint).

**Work Log**
- 00:02 Confirmed AWS access via `aws sts get-caller-identity`; reviewed TODO request to delay alert email wiring.
- 00:14 Replaced SSM parameters with new `auth0_secrets` Terraform module, updated App Runner IAM policy for Secrets Manager support, and refreshed env outputs/docs/todo entries.
- 00:28 Ran `terraform -chdir=infra/terraform/envs/{dev,staging} init -backend=false` + `validate`; cleaned `.terraform` dirs and recorded decisions/checkpoints.

**Result**
- done — see checkpoint docs/agents/checkpoints/2025-10-25_09-45-PDT.md

**Evidence**
- `aws sts get-caller-identity`
- `terraform -chdir=infra/terraform/envs/dev init -backend=false`
- `terraform -chdir=infra/terraform/envs/dev validate`
- `terraform -chdir=infra/terraform/envs/staging init -backend=false`
- `terraform -chdir=infra/terraform/envs/staging validate`

**Next**
- [ ] Attach alert subscribers (email/SNS) once project lands.
- [ ] Continue with promotion policy + production environment tasks.

**Handoff**
- Current state: ready
- Owner (if any): codex
- Timebox remaining: 0m

## [2025-10-25 08:54 PDT] Add CloudWatch alarms for App Runner & DynamoDB

**Goal**
- Provide baseline monitoring by adding CloudWatch alarms (App Runner health + DynamoDB throttles) and SNS notifications for each environment.

**Context**
- Files: infra/terraform/modules/{apprunner,monitoring}, infra/terraform/envs/{dev,staging}/main.tf, docs/agents/{todo,decisions}.md
- Related checkpoints: 2025-10-23_08-25-PT

**Plan**
- [ ] Confirm existing Terraform outputs support monitoring (service ARN/name, table ARN) & extend as needed.
- [ ] Create reusable monitoring module (SNS topic, optional email subs, CloudWatch alarms for App Runner + DynamoDB).
- [ ] Integrate module into dev/staging envs with variables for notification emails and alarm tuning.
- [ ] Validate Terraform plans locally and update docs/todo/decisions to capture new monitoring baseline.

**Work Log**
- 00:02 Reviewed README + handoff + journal to understand outstanding monitoring tasks.
- 00:18 Built `modules/monitoring` (SNS topic + App Runner/DynamoDB alarms) and wired variables/locals into dev + staging Terraform envs.
- 00:28 Ran `terraform fmt` plus `terraform -chdir=infra/terraform/envs/{dev,staging} init -backend=false` and `validate` to ensure configs compile with AWS provider 6.18.0.
- 00:34 Updated docs (todo + decisions) and captured checkpoint summary; noted need for real subscriber emails per environment.

**Result**
- done — see checkpoint docs/agents/checkpoints/2025-10-25_09-06-PDT.md

**Evidence**
- `terraform -chdir=infra/terraform/envs/dev init -backend=false`
- `terraform -chdir=infra/terraform/envs/dev validate`
- `terraform -chdir=infra/terraform/envs/staging init -backend=false`
- `terraform -chdir=infra/terraform/envs/staging validate`

**Next**
- [ ] Collect/assign alert subscriber endpoints (email/SNS integrations) for each environment.
- [ ] Continue with secrets-manager evaluation for Auth0 config.

**Handoff**
- Current state: ready
- Owner (if any): codex
- Timebox remaining: 0m

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

## [2025-10-23 08:10 PT] First service-ci deploy run

**Goal**
- Execute the new GitHub Actions pipeline end-to-end and record deployment outputs.

**Context**
- Files: .github/workflows/service.yml, infra/terraform/modules/apprunner, AWS resources (ECR, DynamoDB, App Runner, SSM)
- Related checkpoints: 2025-10-22_08-40-PT, 2025-10-22_22-30-PT

**Plan**
- [x] Fix workflow YAML (backend config), add terraform setup
- [x] Iterate on IAM deploy role permissions until terraform apply succeeds
- [x] Ensure ECR repo availability (data source) and App Runner access role
- [x] Capture App Runner URL from successful run

**Work Log**
- 00:10 Committed workflow fixes (`setup-terraform`, map secrets) and iterated IAM trust (OIDC role)
- 00:36 Added S3/DDB state resources, OIDC deploy role, ECR repository; updated Terraform to use data source
- 01:25 Introduced App Runner IAM instance/access roles, disabled observability, and expanded deploy IAM policy to cover DynamoDB/ECR/SSM/IAM actions
- 01:55 Triggered `service-ci` via `gh workflow run ...`; after multiple adjustments run completed with `deploy-dev`
- 02:05 Verified outputs: DynamoDB table `dodeck`, App Runner URL `https://skcdqfw5pt.us-west-2.awsapprunner.com`

**Result**
- done — see workflow run 18741630014 (deploy-dev) and AWS resources

**Evidence**
- `gh run watch 18741630014 -R ryanlatham/dodeck`
- AWS CLI: `aws apprunner list-services`, `aws dynamodb describe-table dodeck`
- App Runner URL: `https://skcdqfw5pt.us-west-2.awsapprunner.com`

**Next**
- [ ] Promote image/terraform changes to staging/prod once environments exist
- [ ] Configure monitoring/alerts for App Runner + DynamoDB (CloudWatch alarms)

**Handoff**
- Current state: ready
- Owner (if any): codex
- Timebox remaining: 0m

## [2025-10-23 08:25 PT] Stage environment scaffolding

**Goal**
- Prepare Terraform and pipeline plumbing for staging deployments.

**Context**
- Files: infra/terraform/envs/{dev,staging}, infra/terraform/modules/apprunner/main.tf, .github/workflows/service.yml, service/DEPLOY_NOTES.md
- Related checkpoints: 2025-10-23_08-10-PT

**Plan**
- [x] Add `ENVIRONMENT` runtime support to App Runner deployment
- [x] Introduce staging Terraform env (backend template, variables, data-driven ECR)
- [x] Update workflow to respect `environment` input (dynamic path, vars)
- [x] Document staging secrets/vars + update TODOs

**Work Log**
- 00:06 Added `environment_name` plumbing so API reports env; disabled App Runner observability by default
- 00:12 Created `infra/terraform/envs/staging`; wired data sources for ECR and SSM parameter defaults
- 00:18 Parameterized service-ci deploy job (dynamic working dir, TF env var, ENVIRONMENT var)
- 00:22 Extended deploy IAM policy for remaining ECR/SSM/IAM actions; reran workflow (dev) to ensure success
- 00:26 Updated deploy notes/state setup with staging guidance; refreshed TODO list
- 00:34 Provisioned staging secrets/ECR; staged run `gh workflow run ... -f environment=staging` → `https://pi57pcetyg.us-west-2.awsapprunner.com`

**Result**
- done — staging env has Terraform scaffolding and pipeline now switches by `environment` input

**Evidence**
- Commit b0bbf4c (`feat(staging): add env config and pipeline support`)
- Workflow summary: `gh run list -R ryanlatham/dodeck --workflow service-ci --limit 1`

**Next**
- [ ] Configure staging GitHub environment secrets + run staging deploy (see TODO)
- [ ] Add monitoring/alerting for service runtime

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
