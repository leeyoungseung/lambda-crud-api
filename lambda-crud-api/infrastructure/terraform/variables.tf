# ==============================================
# variables.tf
# ==============================================
variable "project_name" {
  type        = string
  default     = "lambda-crud-api"
  description = "Project tag/name"
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Environment (dev|stg|prod)"
}

variable "aws_region" {
  type        = string
  default     = "ap-northeast-1"
  description = "AWS region"
}

variable "table_name" {
  type        = string
  default     = "items"
  description = "Base DynamoDB table name (env suffix appended)"
}

variable "lambda_runtime" {
  type        = string
  default     = "python3.12"
  description = "Lambda runtime"
}

variable "lambda_timeout" {
  type        = number
  default     = 10
  description = "Lambda timeout seconds"
}

variable "lambda_memory_size" {
  type        = number
  default     = 256
  description = "Lambda memory (MB)"
}

variable "log_retention_days" {
  type        = number
  default     = 14
  description = "CloudWatch logs retention days"
}

variable "extra_tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags for all resources"
}
