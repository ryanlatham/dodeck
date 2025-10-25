### [2025-10-22] Decision: Auth0 JWKS overrides for offline testing
**Context:** Integration tests and local dev need deterministic JWKS without external network access.
**Decision:** Support `AUTH0_JWKS_JSON` / `AUTH0_JWKS_PATH` / `AUTH0_JWKS_URL` overrides in service settings; default to live issuer otherwise.
**Rationale:** Enables hermetic tests and local runs while preserving production behavior with real JWKS fetch.
**Implications:** Operators must avoid setting overrides in production; document variable usage in deploy notes. Future smoke tests should verify override vars are unset in prod.
**Review Date:** 2026-01-01

### [2025-10-22] Decision: Store Auth0 service config in SSM SecureString
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

### [2025-10-25] Decision: CloudWatch + SNS monitoring baseline
**Context:** Need actionable alerts when App Runner fails (HTTP 5xx or zero active instances) or DynamoDB throttles, covering every environment with consistent notification plumbing.
**Decision:** Manage monitoring via Terraform module that provisions an SNS topic plus CloudWatch alarms for App Runner (5xx + ActiveInstances) and DynamoDB (ThrottledRequests) per environment; operators provide subscriber emails through `alert_emails`.
**Rationale:** Keeps alarm definitions versioned next to infrastructure, avoids per-env drift, and makes notification routing configurable without editing Terraform code.
**Implications:** Each environment must supply at least one email subscription (or integrate SNS with downstream tooling) to receive alerts; follow-up work can extend the module with Chatbot/webhooks as needs evolve.
**Review Date:** 2026-04-01
