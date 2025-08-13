# Terraform outputs for Lambda CRUD API infrastructure

# DynamoDB Outputs
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.items_table.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.items_table.arn
}

output "dynamodb_table_id" {
  description = "ID of the DynamoDB table"
  value       = aws_dynamodb_table.items_table.id
}

# IAM Outputs
output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.name
}

# Lambda Function Outputs
output "create_lambda_function_arn" {
  description = "ARN of the Create Lambda function"
  value       = aws_lambda_function.create_lambda.arn
}

output "create_lambda_function_name" {
  description = "Name of the Create Lambda function"
  value       = aws_lambda_function.create_lambda.function_name
}

output "read_lambda_function_arn" {
  description = "ARN of the Read Lambda function"
  value       = aws_lambda_function.read_lambda.arn
}

output "read_lambda_function_name" {
  description = "Name of the Read Lambda function"
  value       = aws_lambda_function.read_lambda.function_name
}

output "update_lambda_function_arn" {
  description = "ARN of the Update Lambda function"
  value       = aws_lambda_function.update_lambda.arn
}

output "update_lambda_function_name" {
  description = "Name of the Update Lambda function"
  value       = aws_lambda_function.update_lambda.function_name
}

output "delete_lambda_function_arn" {
  description = "ARN of the Delete Lambda function"
  value       = aws_lambda_function.delete_lambda.arn
}

output "delete_lambda_function_name" {
  description = "Name of the Delete Lambda function"
  value       = aws_lambda_function.delete_lambda.function_name
}

# CloudWatch Log Group Outputs
output "create_lambda_log_group_name" {
  description = "Name of the Create Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.create_lambda_logs.name
}

output "read_lambda_log_group_name" {
  description = "Name of the Read Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.read_lambda_logs.name
}

output "update_lambda_log_group_name" {
  description = "Name of the Update Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.update_lambda_logs.name
}

output "delete_lambda_log_group_name" {
  description = "Name of the Delete Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.delete_lambda_logs.name
}

# Environment and Configuration Outputs
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# Useful for API Gateway integration (future use)
output "lambda_function_arns" {
  description = "Map of all Lambda function ARNs"
  value = {
    create = aws_lambda_function.create_lambda.arn
    read   = aws_lambda_function.read_lambda.arn
    update = aws_lambda_function.update_lambda.arn
    delete = aws_lambda_function.delete_lambda.arn
  }
}

output "lambda_function_names" {
  description = "Map of all Lambda function names"
  value = {
    create = aws_lambda_function.create_lambda.function_name
    read   = aws_lambda_function.read_lambda.function_name
    update = aws_lambda_function.update_lambda.function_name
    delete = aws_lambda_function.delete_lambda.function_name
  }
}

# API Gateway Outputs
output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.crud_api.id
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.crud_api.id}.execute-api.${var.aws_region}.amazonaws.com/v1"
}

output "api_gateway_stage_name" {
  description = "API Gateway stage name"
  value       = aws_api_gateway_stage.crud_api_stage.stage_name
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.crud_api.execution_arn
}