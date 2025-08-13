# Terraform configuration for Lambda CRUD API infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Variables are defined in variables.tf

# Local values
locals {
  table_name_with_env = "${var.table_name}-${var.environment}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "items_table" {
  name           = local.table_name_with_env
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Component = "database"
  })
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda-crud-api-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Component = "iam"
  })
}

# IAM Policy for DynamoDB Access
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "lambda-dynamodb-access-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.items_table.arn
      }
    ]
  })
}

# Attach basic execution role policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "create_lambda_logs" {
  name              = "/aws/lambda/crud-api-create-${var.environment}"
  retention_in_days = 14
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "read_lambda_logs" {
  name              = "/aws/lambda/crud-api-read-${var.environment}"
  retention_in_days = 14
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "update_lambda_logs" {
  name              = "/aws/lambda/crud-api-update-${var.environment}"
  retention_in_days = 14
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "delete_lambda_logs" {
  name              = "/aws/lambda/crud-api-delete-${var.environment}"
  retention_in_days = 14
  tags              = local.common_tags
}

# Lambda Functions
resource "aws_lambda_function" "create_lambda" {
  filename         = "placeholder.zip"
  function_name    = "crud-api-create-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "create_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      AWS_REGION         = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  reserved_concurrent_executions = 100

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.create_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "create"
  })
}

resource "aws_lambda_function" "read_lambda" {
  filename         = "placeholder.zip"
  function_name    = "crud-api-read-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "read_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      AWS_REGION         = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  reserved_concurrent_executions = 100

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.read_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "read"
  })
}

resource "aws_lambda_function" "update_lambda" {
  filename         = "placeholder.zip"
  function_name    = "crud-api-update-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "update_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      AWS_REGION         = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  reserved_concurrent_executions = 100

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.update_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "update"
  })
}

resource "aws_lambda_function" "delete_lambda" {
  filename         = "placeholder.zip"
  function_name    = "crud-api-delete-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "delete_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      AWS_REGION         = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  reserved_concurrent_executions = 100

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.delete_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "delete"
  })
}

# Outputs are defined in outputs.tf