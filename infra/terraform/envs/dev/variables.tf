variable "aws_region" { type = string }
variable "project_name" {
  type    = string
  default = "dodeck"
}

variable "auth0_issuer" {
  type = string
}

variable "auth0_audience" {
  type = string
}

variable "cors_allowed_origins" {
  type    = string
  default = "http://localhost:5173"
}

variable "service_image_tag" {
  type    = string
  default = "latest"
}

variable "service_repository_name" {
  type    = string
  default = "dodeck-service"
}

variable "environment_name" {
  type    = string
  default = "dev"
}

variable "alert_emails" {
  type    = list(string)
  default = []
}
