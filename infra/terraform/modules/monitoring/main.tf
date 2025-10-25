variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "apprunner_service_name" {
  type = string
}

variable "ddb_table_name" {
  type = string
}

variable "alarm_emails" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  topic_name     = "${var.project_name}-${var.environment}-alerts"
  subscriber_map = { for email in var.alarm_emails : lower(email) => email }
  tags_with_component = merge(var.tags, {
    Component = "monitoring"
  })
}

resource "aws_sns_topic" "alerts" {
  name = local.topic_name
  tags = local.tags_with_component
}

resource "aws_sns_topic_subscription" "email" {
  for_each  = local.subscriber_map
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_cloudwatch_metric_alarm" "apprunner_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-apprunner-5xx"
  alarm_description   = "Alerts when the App Runner service returns HTTP 5xx responses."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  metric_name         = "5xxStatusCodes"
  namespace           = "AWS/AppRunner"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions = {
    ServiceName = var.apprunner_service_name
  }
  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = [aws_sns_topic.alerts.arn]
  tags                      = local.tags_with_component
}

resource "aws_cloudwatch_metric_alarm" "apprunner_instances" {
  alarm_name          = "${var.project_name}-${var.environment}-apprunner-active-instances"
  alarm_description   = "Alerts when App Runner reports zero active instances (service unhealthy)."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  metric_name         = "ActiveInstances"
  namespace           = "AWS/AppRunner"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  treat_missing_data  = "breaching"
  dimensions = {
    ServiceName = var.apprunner_service_name
  }
  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = [aws_sns_topic.alerts.arn]
  tags                      = local.tags_with_component
}

resource "aws_cloudwatch_metric_alarm" "ddb_throttles" {
  alarm_name          = "${var.project_name}-${var.environment}-ddb-throttles"
  alarm_description   = "Alerts when DynamoDB reports throttled requests."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions = {
    TableName = var.ddb_table_name
  }
  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = [aws_sns_topic.alerts.arn]
  tags                      = local.tags_with_component
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "sns_topic_name" {
  value = aws_sns_topic.alerts.name
}
