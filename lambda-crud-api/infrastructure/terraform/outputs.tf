# ==============================================
# outputs.tf
# ==============================================
output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.items_table.name
}

output "lambda_function_names" {
  description = "Lambda function names by operation"
  value       = { for k, v in aws_lambda_function.fn : k => v.function_name }
}

output "lambda_function_arns" {
  description = "Lambda function ARNs by operation"
  value       = { for k, v in aws_lambda_function.fn : k => v.arn }
}

output "rest_api_id" {
  description = "REST API id"
  value       = aws_api_gateway_rest_api.crud_api.id
}

output "rest_api_invoke_url" {
  description = "Invoke URL for the deployed stage"
  value       = "https://${aws_api_gateway_rest_api.crud_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "rest_api_execution_arn" {
  description = "Execution ARN (useful for permissions)"
  value       = aws_api_gateway_rest_api.crud_api.execution_arn
}
