# ==============================================
# outputs.tf (fixed)
# ==============================================

output "dynamodb_table_name" {
  description = "Deployed DynamoDB table name"
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

output "http_api_endpoint" {
  description = "API Gateway HTTP API invoke URL"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "http_api_execution_arn" {
  description = "API Gateway execution ARN"
  value       = aws_apigatewayv2_api.http_api.execution_arn
}
