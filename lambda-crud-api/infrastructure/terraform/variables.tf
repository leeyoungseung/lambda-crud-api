# ==============================================
# variables.tf (fixed)
# ==============================================

variable "project_name" {
  type        = string
  default     = "lambda-crud-api"
  description = "Project tag/name prefix"
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Environment name (e.g., dev|stg|prod)"
}

variable "aws_region" {
  type        = string
  default     = "ap-northeast-1"
  description = "AWS region to deploy into"
}

variable "table_name" {
  type        = string
  default     = "items"
  description = "Base DynamoDB table name (env suffix will be appended)"
}

variable "lambda_runtime" {
  type        = string
  default     = "python3.12"
  description = "Lambda runtime (e.g., python3.12)"
}

variable "lambda_timeout" {
  type        = number
  default     = 10
  description = "Lambda timeout in seconds"
}

variable "lambda_memory_size" {
  type        = number
  default     = 256
  description = "Lambda memory in MB"
}

variable "log_retention_days" {
  type        = number
  default     = 14
  description = "CloudWatch log retention days"
}

# Optional extra tags
variable "extra_tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags to merge into all resources"
}
