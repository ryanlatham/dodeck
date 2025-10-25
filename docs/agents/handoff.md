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
- **Production scaffolding ready**: `infra/terraform/envs/prod` mirrors staging with Secrets Manager + monitoring integration; workflow already supports `environment=prod`.
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
- **Monitoring/Alerting**: alarms currently email `ryalatham@gmail.com`; confirm SNS subscription and replace with team distro/Slack when available.
- **Production Environment**: provision AWS resources + GitHub `prod` environment secrets/approvals using the new Terraform env.
- **Observability**: FastAPI now emits X-Ray traces; monitor spans and plan log aggregation as traffic ramps up.
- **Secrets Rotation**: decide how/when to rotate the Auth0 secrets now that they live in Secrets Manager.

## Next Suggested Steps
1. Configure notification targets for the CloudWatch alarms (SNS email/webhook).
2. Run Terraform for `infra/terraform/envs/prod` and set up the GitHub `prod` environment secrets/approvals.
3. Instrument FastAPI (X-Ray) so App Runner traces are meaningful.
4. Decide on Auth0 secret rotation cadence (Secrets Manager rotation lambda or manual SOP).

## Key Commands/References
- Run workflow manually (dev/staging only until prod ready):  
  `gh workflow run service-ci -R ryanlatham/dodeck -f environment=dev|staging --ref main`
- Health checks:  
  `curl https://skcdqfw5pt.us-west-2.awsapprunner.com/healthz`  
  `curl https://pi57pcetyg.us-west-2.awsapprunner.com/healthz`
- Terraform validation (local):  
  `terraform -chdir=infra/terraform/envs/dev validate`  
  `terraform -chdir=infra/terraform/envs/staging validate`

All artifacts and environment details have been recorded in the docs directory for continuity.
