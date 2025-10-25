terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0" }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

locals {
  service_name = "${var.project_name}-api"
  tags = {
    Project     = var.project_name
    Environment = "staging"
  }
}

module "ddb" {
  source     = "../../modules/dynamodb"
  table_name = var.project_name
}

data "aws_ecr_repository" "service" {
  name = var.service_repository_name
}

module "auth0_secrets" {
  source         = "../../modules/auth0_secrets"
  project_name   = var.project_name
  environment    = var.environment_name
  auth0_issuer   = var.auth0_issuer
  auth0_audience = var.auth0_audience
  tags           = local.tags
}

module "apprunner" {
  source       = "../../modules/apprunner"
  service_name = local.service_name
  image        = "${data.aws_ecr_repository.service.repository_url}:${var.service_image_tag}"
  table_name   = module.ddb.table_name
  table_arn    = module.ddb.table_arn
  env_vars = {
    REQUIRE_EMAIL_VERIFIED = "true"
    CORS_ALLOWED_ORIGINS   = var.cors_allowed_origins
    LOG_LEVEL              = "info"
    ENVIRONMENT            = var.environment_name
  }
  env_secret_arns = {
    AUTH0_ISSUER   = module.auth0_secrets.auth0_issuer_secret_arn
    AUTH0_AUDIENCE = module.auth0_secrets.auth0_audience_secret_arn
  }
  observability_enabled           = var.enable_observability
  observability_configuration_arn = module.observability.observability_configuration_arn
  tags                            = local.tags
}

module "monitoring" {
  source                 = "../../modules/monitoring"
  project_name           = var.project_name
  environment            = var.environment_name
  apprunner_service_name = local.service_name
  ddb_table_name         = module.ddb.table_name
  alarm_emails           = var.alert_emails
  tags                   = local.tags
}

module "observability" {
  source          = "../../modules/observability"
  project_name    = var.project_name
  environment     = var.environment_name
  enable_tracing  = var.enable_observability
  tags            = local.tags
}

output "service_url"        { value = module.apprunner.service_url }
output "table_name"         { value = module.ddb.table_name }
output "ecr_repo_url"       { value = data.aws_ecr_repository.service.repository_url }
output "auth0_issuer_secret"   { value = module.auth0_secrets.auth0_issuer_secret_name }
output "auth0_audience_secret" { value = module.auth0_secrets.auth0_audience_secret_name }
output "alert_topic_arn"    { value = module.monitoring.sns_topic_arn }
output "alert_topic_name"   { value = module.monitoring.sns_topic_name }
