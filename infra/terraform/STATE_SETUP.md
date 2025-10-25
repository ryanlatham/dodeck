# Terraform Remote State Setup

The service environment uses an S3 backend with DynamoDB state locking. Provision
these resources **once** per AWS account/region before running `terraform init`.

## 1. Create Remote State Storage

```bash
AWS_REGION=us-west-2
PROJECT=dodeck

# S3 bucket (must be globally unique)
aws s3api create-bucket \
  --bucket "${PROJECT}-terraform-state" \
  --region "$AWS_REGION" \
  --create-bucket-configuration LocationConstraint="$AWS_REGION"

# DynamoDB lock table
aws dynamodb create-table \
  --table-name "${PROJECT}-terraform-locks" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## 2. Provide Backend Configuration

Copy `infra/terraform/envs/dev/backend.hcl.example` to `backend.hcl` and update:

```hcl
bucket         = "dodeck-terraform-state"
key            = "service/dev/terraform.tfstate"
region         = "us-west-2"
dynamodb_table = "dodeck-terraform-locks"
encrypt        = true
```

Run Terraform with:

```bash
terraform -chdir=infra/terraform/envs/dev init -backend-config=backend.hcl
```

## 3. Credentials

Use a least-privilege IAM role for CI/CD (see `service/DEPLOY_NOTES.md` — CI/CD
Credentials section). Local workflows can rely on `aws sso login` or per-user
profiles.

> **Status (2025-10-22):** `dodeck-terraform-state` bucket and `dodeck-terraform-locks` table created in account 309090259750 (region us-west-2). Update names above if you clone to a different account.

## 4. GitHub OIDC Deploy Role

Created IAM role `arn:aws:iam::309090259750:role/dodeck-service-deploy` trusting
`token.actions.githubusercontent.com` with subject `repo:ryanlatham/OpenAiApps:*`.
If provisioning from another account, recreate using:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

aws iam create-role \
  --role-name dodeck-service-deploy \
  --assume-role-policy-document file://dodeck-oidc-trust.json

aws iam put-role-policy \
  --role-name dodeck-service-deploy \
  --policy-name dodeck-deploy-inline \
  --policy-document file://dodeck-deploy-policy.json
```

Populate GitHub secrets/variables:
- `AWS_DEPLOY_ROLE_ARN=arn:aws:iam::309090259750:role/dodeck-service-deploy`
- `TF_STATE_BUCKET=dodeck-terraform-state`
- `TF_STATE_KEY=service/dev/terraform.tfstate`
- `TF_STATE_LOCK_TABLE=dodeck-terraform-locks`

## 5. Additional Environments

For **staging** (and later production) create distinct Terraform state keys and
secret values:

- S3 object key: `service/staging/terraform.tfstate`
- DynamoDB table: reuse `dodeck-terraform-locks`
- Secrets Manager entries (managed by Terraform):
  - `/dodeck-staging/service/auth0_issuer`
  - `/dodeck-staging/service/auth0_audience`
- ECR repository: `dodeck-service-staging`

Configure GitHub environment-level secrets/variables for `staging` matching the
names used in the workflow (`TF_STATE_*`, `AUTH0_*`, `ECR_REPOSITORY`, etc.).
