# ==============================================
# api-gateway.tf (fixed) - HTTP API (v2) → 4 Lambda routes
# ==============================================

resource "aws_apigatewayv2_api" "http_api" {
  name          = "crud-http-api-${var.environment}"
  protocol_type = "HTTP"
  tags          = local.common_tags
}

# Integrations (Lambda proxy)
resource "aws_apigatewayv2_integration" "create" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.fn["create"].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "read" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.fn["read"].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "update" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.fn["update"].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "delete" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.fn["delete"].invoke_arn
  payload_format_version = "2.0"
}

# Routes
resource "aws_apigatewayv2_route" "create" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /items"
  target    = "integrations/${aws_apigatewayv2_integration.create.id}"
}

resource "aws_apigatewayv2_route" "read" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /items/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.read.id}"
}

resource "aws_apigatewayv2_route" "update" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "PUT /items/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.update.id}"
}

resource "aws_apigatewayv2_route" "delete" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "DELETE /items/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.delete.id}"
}

# Stage (auto-deploy)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  # Access logs (optional) - comment out if you don't want CW logs
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId               = "$context.requestId",
      ip                      = "$context.identity.sourceIp",
      requestTime             = "$context.requestTime",
      httpMethod              = "$context.httpMethod",
      path                    = "$context.path",
      routeKey                = "$context.routeKey",
      status                  = "$context.status",
      responseLength          = "$context.responseLength",
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigwv2/crud-http-api-${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# Lambda invoke permissions for API Gateway
resource "aws_lambda_permission" "apigw_create" {
  statement_id  = "AllowAPIGWInvokeCreate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["create"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_read" {
  statement_id  = "AllowAPIGWInvokeRead"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["read"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_update" {
  statement_id  = "AllowAPIGWInvokeUpdate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["update"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_delete" {
  statement_id  = "AllowAPIGWInvokeDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["delete"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
