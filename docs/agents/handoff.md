# DoDeck Service — Handoff Summary (2025-10-25)

## Context & Achievements
- **Service deploy pipeline** (`service-ci`) now builds, pushes, and applies Terraform. Verified dev run (`gh run 18741630014`).
- **App Runner (dev)** live at `https://skcdqfw5pt.us-west-2.awsapprunner.com`. Health returns version `1.0.0` with environment `dev`.
- **DynamoDB (dev)** table `dodeck` provisioned; Auth0 issuer/audience now stored in AWS Secrets Manager (`/${project}/service/auth0_*`) and wired into App Runner.
- **Staging scaffolding** added:
  - `infra/terraform/envs/staging` mirrors dev with separate backend key, env defaults, and `environment_name`.
  - GitHub Actions deploy job accepts `environment` input; dynamic backend config & vars.
  - IAM deploy role expanded to cover staging resources (DynamoDB, Secrets Manager, IAM/ECR API calls).
  - Staging run (`gh run 18753998898`) succeeded: App Runner `https://pi57pcetyg.us-west-2.awsapprunner.com`, DynamoDB table `dodeck-staging`.
- **Promotion policy codified**: workflow_dispatch now defaults to dev, allows staging only from `main`, and restricts prod deploys to signed tags; GitHub environments should enforce manual approvals for staging/prod.
- **Documentation & tracking** updated (`DEPLOY_NOTES.md`, `STATE_SETUP.md`, `docs/agents/journal.md`, checkpoints, TODO).

## Repository State
- Branch `main` clean (`git status` empty).
- Latest commits:
  - `feat(staging): add env config and pipeline support` (b0bbf4c).
  - `docs(deploy): note app runner url` (320d1ea).
  - `docs: capture staging env setup` (a7346bf).
  - `docs: record staging deploy run` (c2ac5fc).
  - `fix(apprunner): move auth config block` (40be827).
- GitHub environment `staging` configured with required secrets/vars; dev defaults remain at repository level.

## Outstanding TODOs
- **Monitoring/Alerting**: add CloudWatch alarms (App Runner health, DynamoDB errors) and notification targets.
- **Production Environment**: mirror staging setup (backend config, secrets/vars, App Runner & DynamoDB resources).
- **Observability**: consider enabling App Runner observability (needs configuration ARN) once logging destination decided.
- **Alert Routing**: once the project stabilizes, attach SNS/email/webhook subscribers to CloudWatch alarms.
- **Secrets Rotation**: decide how/when to rotate the Auth0 secrets now that they live in Secrets Manager.

## Next Suggested Steps
1. Configure CloudWatch alarms/notifications for dev & staging App Runner services (plus downstream notifications).
2. Clone staging into a production Terraform environment and wire GitHub environment secrets/approvals.
3. Decide on Auth0 secret rotation cadence (Secrets Manager rotation lambda or manual SOP).
4. Plan observability (CloudWatch logs/metrics exports) before adding alert subscribers.

## Key Commands/References
- Run workflow manually (dev/staging only):  
  `gh workflow run service-ci -R ryanlatham/dodeck -f environment=dev|staging --ref main`
- Health checks:  
  `curl https://skcdqfw5pt.us-west-2.awsapprunner.com/healthz`  
  `curl https://pi57pcetyg.us-west-2.awsapprunner.com/healthz`
- Terraform validation (local):  
  `terraform -chdir=infra/terraform/envs/dev validate`  
  `terraform -chdir=infra/terraform/envs/staging validate`

All artifacts and environment details have been recorded in the docs directory for continuity.
