### [2025-10-22] Decision: Auth0 JWKS overrides for offline testing
**Context:** Integration tests and local dev need deterministic JWKS without external network access.
**Decision:** Support `AUTH0_JWKS_JSON` / `AUTH0_JWKS_PATH` / `AUTH0_JWKS_URL` overrides in service settings; default to live issuer otherwise.
**Rationale:** Enables hermetic tests and local runs while preserving production behavior with real JWKS fetch.
**Implications:** Operators must avoid setting overrides in production; document variable usage in deploy notes. Future smoke tests should verify override vars are unset in prod.
**Review Date:** 2026-01-01

### [2025-10-22] Decision: Store Auth0 service config in SSM SecureString _(superseded 2025-10-25)_
**Context:** App Runner needs Auth0 issuer/audience secrets without embedding static values in Terraform state or environment files.
**Decision:** Manage `AUTH0_ISSUER` and `AUTH0_AUDIENCE` as SSM SecureString parameters (`/${project}/service/...`) and reference them via App Runner runtime secrets.
**Rationale:** Keeps credentials in AWS-managed storage, allows rotation without rebuilding infrastructure, and aligns with App Runner best practices.
**Implications:** Terraform requires access to write SSM parameters; CI/deploy pipelines must supply values at plan/apply time. Ensure App Runner IAM role retains `ssm:GetParameter` and `kms:Decrypt` permissions.
**Review Date:** 2026-01-01

### [2025-10-22] Decision: GitHub OIDC for service deploy pipeline
**Context:** Need to grant GitHub Actions permission to push images and run Terraform without managing long-lived keys.
**Decision:** Use GitHub OpenID Connect with an AWS IAM role (`AWS_DEPLOY_ROLE_ARN`) that trusts `token.actions.githubusercontent.com` and limits access to ECR, S3 state bucket, DynamoDB lock table, and Terraform-managed resources.
**Rationale:** Removes static secrets, supports short-lived credentials, and aligns with AWS security guidance.
**Implications:** Must provision IAM role with appropriate trust & permission policies; workflow now assumes role and requires repository secrets/variables documented in `service/DEPLOY_NOTES.md`.
**Review Date:** 2026-01-01

### [2025-10-25] Decision: Store Auth0 config in AWS Secrets Manager
**Context:** Need AWS-native rotation support and reduced IAM surface area compared to SSM parameters while feeding App Runner runtime secrets.
**Decision:** Provision per-environment Secrets Manager secrets (`/${project}/service/auth0_*`) via Terraform and inject them into App Runner using secret ARNs.
**Rationale:** Aligns with AWS best practices, enables lifecycle policies/rotation later, and consolidates permissions around Secrets Manager APIs.
**Implications:** App Runner instance role and deploy IAM role must allow `secretsmanager:GetSecretValue` plus `kms:Decrypt` on `alias/aws/secretsmanager`; legacy SSM dependencies can be retired.
**Review Date:** 2026-04-01

### [2025-10-25] Decision: Deployment promotion policy & approvals
**Context:** Needed a clear rule set for which Git refs may deploy to dev/staging/prod plus a mechanism for manual approvals.
**Decision:** Gate deployments via workflow inputs + environment protection: manual runs default to `dev`, `staging` runs must target `refs/heads/main`, and `prod` deploys are tag-only. GitHub environments (`staging`, `prod`) should enforce manual approvals in the UI.
**Rationale:** Prevents accidental promotions, keeps dev fast, and codifies the expectation that prod releases follow a tagged artefact.
**Implications:** Operators must create/maintain GitHub environment rules (required reviewers, secrets) matching the workflow, and release managers must cut signed tags for prod deploys.
**Review Date:** 2026-04-01
