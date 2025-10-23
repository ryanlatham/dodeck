variable "service_name" {
  type = string
}

variable "image" {
  type = string
}

variable "table_name" {
  type = string
}

variable "table_arn" {
  type = string
}

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "env_secret_arns" {
  type    = map(string)
  default = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}

data "aws_partition" "current" {}
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  runtime_env_vars = merge({ TABLE_NAME = var.table_name }, var.env_vars)
  runtime_env_secrets = [
    for name, arn in var.env_secret_arns : {
      name  = name
      value = arn
    }
  ]
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "instance" {
  statement {
    sid = "DynamoDBAccess"
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:UpdateItem",
    ]
    resources = [var.table_arn]
  }

  dynamic "statement" {
    for_each = length(local.runtime_env_secrets) > 0 ? [1] : []
    content {
      sid = "SSMParameterAccess"
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
      ]
      resources = values(var.env_secret_arns)
    }
  }

  dynamic "statement" {
    for_each = length(local.runtime_env_secrets) > 0 ? [1] : []
    content {
      sid     = "KMSDecrypt"
      actions = ["kms:Decrypt"]
      resources = [
        "arn:${data.aws_partition.current.partition}:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:alias/aws/ssm"
      ]
    }
  }
}

resource "aws_iam_role" "instance" {
  name               = "${var.service_name}-instance"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "instance" {
  name   = "${var.service_name}-instance-policy"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.instance.json
}

resource "aws_apprunner_service" "this" {
  service_name = var.service_name
  source_configuration {
    image_repository {
      image_identifier      = var.image
      image_repository_type = "ECR"
      image_configuration {
        port                          = "8080"
        runtime_environment_variables = local.runtime_env_vars
        runtime_environment_secrets   = local.runtime_env_secrets
      }
    }
    auto_deployments_enabled = true
  }

  instance_configuration {
    instance_role_arn = aws_iam_role.instance.arn
  }

  observability_configuration { observability_enabled = true }
  tags = var.tags
}

output "service_url" { value = aws_apprunner_service.this.service_url }
output "instance_role_arn" { value = aws_iam_role.instance.arn }
