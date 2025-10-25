# Infra — PLAN (Terraform)

## Goals
- Provision AWS resources for DoDeck:
  - DynamoDB table (`DoDeck`)
  - ECR repository for service image
  - App Runner service (HTTPS public endpoint)
- AWS Secrets Manager entries for runtime config (Auth0, etc.)
  - CloudWatch logs
  - (Later) S3 + CloudFront + ACM for web

## Structure
- `terraform/modules/` — reusable modules
- `terraform/envs/dev/` — dev environment composition
- Remote state recommended: S3 + DynamoDB lock

## Variables to provide
- `aws_region`
- `project_name` (e.g., `dodeck`)
- `auth0_issuer`, `auth0_audience`
- optional domain names for custom endpoints

## Outputs
- App Runner URL
- DynamoDB table name
- ECR repo URL

## Apply Order
1. `terraform init`
2. `terraform plan`
3. `terraform apply`

_Note: App Runner supports HTTPS by default; custom domain can be added later with ACM + DNS._
