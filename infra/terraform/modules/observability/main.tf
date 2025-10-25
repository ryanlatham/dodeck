variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "enable_tracing" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  name = "${var.project_name}-${var.environment}-observability"
}

resource "aws_apprunner_observability_configuration" "this" {
  count = var.enable_tracing ? 1 : 0

  observability_configuration_name = local.name

  trace_configuration {
    vendor = "AWSXRAY"
  }

  tags = var.tags
}

output "observability_configuration_arn" {
  value = var.enable_tracing ? aws_apprunner_observability_configuration.this[0].arn : null
}
