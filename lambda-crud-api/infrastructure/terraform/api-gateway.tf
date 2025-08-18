# ==============================================
# api-gateway.tf — API Gateway REST (v1) → Lambda proxy
# ==============================================
data "aws_region" "current" {}

resource "aws_api_gateway_rest_api" "crud_api" {
  name        = "crud-rest-api-${var.environment}"
  description = "CRUD REST API (Lambda proxy)"
  endpoint_configuration { types = ["REGIONAL"] }
  tags = local.common_tags
}

# Resources
resource "aws_api_gateway_resource" "items" {
  rest_api_id = aws_api_gateway_rest_api.crud_api.id
  parent_id   = aws_api_gateway_rest_api.crud_api.root_resource_id
  path_part   = "items"
}

resource "aws_api_gateway_resource" "item_id" {
  rest_api_id = aws_api_gateway_rest_api.crud_api.id
  parent_id   = aws_api_gateway_resource.items.id
  path_part   = "{id}"
}

# Methods
resource "aws_api_gateway_method" "post_items" {
  rest_api_id   = aws_api_gateway_rest_api.crud_api.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "get_items" {
  rest_api_id   = aws_api_gateway_rest_api.crud_api.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "get_item" {
  rest_api_id   = aws_api_gateway_rest_api.crud_api.id
  resource_id   = aws_api_gateway_resource.item_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "put_item" {
  rest_api_id   = aws_api_gateway_rest_api.crud_api.id
  resource_id   = aws_api_gateway_resource.item_id.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "delete_item" {
  rest_api_id   = aws_api_gateway_rest_api.crud_api.id
  resource_id   = aws_api_gateway_resource.item_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

# Integrations (Lambda proxy)
resource "aws_api_gateway_integration" "post_items" {
  rest_api_id             = aws_api_gateway_rest_api.crud_api.id
  resource_id             = aws_api_gateway_resource.items.id
  http_method             = aws_api_gateway_method.post_items.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fn["create"].invoke_arn
}

resource "aws_api_gateway_integration" "get_items" {
  rest_api_id             = aws_api_gateway_rest_api.crud_api.id
  resource_id             = aws_api_gateway_resource.items.id
  http_method             = aws_api_gateway_method.get_items.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fn["read"].invoke_arn
}

resource "aws_api_gateway_integration" "get_item" {
  rest_api_id             = aws_api_gateway_rest_api.crud_api.id
  resource_id             = aws_api_gateway_resource.item_id.id
  http_method             = aws_api_gateway_method.get_item.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fn["read"].invoke_arn
}

resource "aws_api_gateway_integration" "put_item" {
  rest_api_id             = aws_api_gateway_rest_api.crud_api.id
  resource_id             = aws_api_gateway_resource.item_id.id
  http_method             = aws_api_gateway_method.put_item.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fn["update"].invoke_arn
}

resource "aws_api_gateway_integration" "delete_item" {
  rest_api_id             = aws_api_gateway_rest_api.crud_api.id
  resource_id             = aws_api_gateway_resource.item_id.id
  http_method             = aws_api_gateway_method.delete_item.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fn["delete"].invoke_arn
}

# Deployment + Stage
resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.crud_api.id

  triggers = {
    redeploy_hash = sha1(jsonencode({
      res = [aws_api_gateway_resource.items.id, aws_api_gateway_resource.item_id.id],
      met = [aws_api_gateway_method.post_items.id, aws_api_gateway_method.get_items.id, aws_api_gateway_method.get_item.id, aws_api_gateway_method.put_item.id, aws_api_gateway_method.delete_item.id],
      int = [aws_api_gateway_integration.post_items.id, aws_api_gateway_integration.get_items.id, aws_api_gateway_integration.get_item.id, aws_api_gateway_integration.put_item.id, aws_api_gateway_integration.delete_item.id]
    }))
  }

  lifecycle { create_before_destroy = true }

  depends_on = [
    aws_api_gateway_integration.post_items,
    aws_api_gateway_integration.get_items,
    aws_api_gateway_integration.get_item,
    aws_api_gateway_integration.put_item,
    aws_api_gateway_integration.delete_item
  ]
}

resource "aws_api_gateway_stage" "stage" {
  rest_api_id   = aws_api_gateway_rest_api.crud_api.id
  stage_name    = var.environment
  deployment_id = aws_api_gateway_deployment.this.id

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId      = "$context.requestId",
      ip             = "$context.identity.sourceIp",
      requestTime    = "$context.requestTime",
      httpMethod     = "$context.httpMethod",
      path           = "$context.path",
      status         = "$context.status",
      protocol       = "$context.protocol",
      responseLength = "$context.responseLength"
    })
  }

  tags = local.common_tags
}

# CloudWatch Logs for API
resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigw/crud-rest-api-${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# API Gateway account → CW Logs role
resource "aws_iam_role" "apigw_cloudwatch_role" {
  name = "apigw-cloudwatch-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "apigateway.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "apigw_push_to_cw" {
  role       = aws_iam_role.apigw_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_api_gateway_account" "account" {
  cloudwatch_role_arn = aws_iam_role.apigw_cloudwatch_role.arn
  depends_on          = [aws_iam_role_policy_attachment.apigw_push_to_cw]
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "allow_apigw_invoke_create" {
  statement_id  = "AllowAPIGWInvokeCreate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["create"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crud_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_read" {
  statement_id  = "AllowAPIGWInvokeRead"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["read"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crud_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_update" {
  statement_id  = "AllowAPIGWInvokeUpdate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["update"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crud_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_delete" {
  statement_id  = "AllowAPIGWInvokeDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fn["delete"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.crud_api.execution_arn}/*/*"
}
