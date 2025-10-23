variable "aws_region" { type = string }

variable "project_name" {
  type    = string
  default = "dodeck-staging"
}

variable "auth0_issuer" { type = string }
variable "auth0_audience" { type = string }

variable "cors_allowed_origins" {
  type    = string
  default = "https://staging.dodeck.com"
}

variable "service_image_tag" {
  type    = string
  default = "staging"
}

variable "service_repository_name" {
  type    = string
  default = "dodeck-service-staging"
}

variable "environment_name" {
  type    = string
  default = "staging"
}
