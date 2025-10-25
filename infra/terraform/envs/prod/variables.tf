variable "aws_region" { type = string }

variable "project_name" {
  type    = string
  default = "dodeck-prod"
}

variable "auth0_issuer" { type = string }
variable "auth0_audience" { type = string }

variable "cors_allowed_origins" {
  type    = string
  default = "https://app.dodeck.com"
}

variable "service_image_tag" {
  type    = string
  default = "prod"
}

variable "service_repository_name" {
  type    = string
  default = "dodeck-service-prod"
}

variable "environment_name" {
  type    = string
  default = "prod"
}

variable "alert_emails" {
  type    = list(string)
  default = []
}
