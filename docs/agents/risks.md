### [2025-10-22] Risk: Service not yet backed by managed DynamoDB/App Runner
**Details:** Local tests use dynamodb-local; Terraform config exists but no AWS environment/remote state or credentials are wired, so the HTTPS gate remains blocked.
**Mitigation:** Set up remote state + IAM roles, run Terraform apply once credentials are in place, and verify App Runner URL before moving to /web.

### [2025-10-22] Risk: Upstream datetime.utcnow deprecations
**Details:** jose/botocore emit `datetime.utcnow()` deprecation warnings during tests; potential future breakage.
**Mitigation:** Track upstream releases; consider shim or pin if warnings become errors in future Python versions.
