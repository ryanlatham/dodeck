variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "auth0_issuer" {
  type = string
}

variable "auth0_audience" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  issuer_secret_name   = "/${var.project_name}/service/auth0_issuer"
  audience_secret_name = "/${var.project_name}/service/auth0_audience"
}

resource "aws_secretsmanager_secret" "auth0_issuer" {
  name        = local.issuer_secret_name
  description = "Auth0 issuer for DoDeck service (${var.environment})"
  tags        = var.tags
}

resource "aws_secretsmanager_secret" "auth0_audience" {
  name        = local.audience_secret_name
  description = "Auth0 audience for DoDeck service (${var.environment})"
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "auth0_issuer" {
  secret_id     = aws_secretsmanager_secret.auth0_issuer.id
  secret_string = var.auth0_issuer
}

resource "aws_secretsmanager_secret_version" "auth0_audience" {
  secret_id     = aws_secretsmanager_secret.auth0_audience.id
  secret_string = var.auth0_audience
}

output "auth0_issuer_secret_arn" {
  value = aws_secretsmanager_secret.auth0_issuer.arn
}

output "auth0_audience_secret_arn" {
  value = aws_secretsmanager_secret.auth0_audience.arn
}

output "auth0_issuer_secret_name" {
  value = aws_secretsmanager_secret.auth0_issuer.name
}

output "auth0_audience_secret_name" {
  value = aws_secretsmanager_secret.auth0_audience.name
}
