# Terraform configuration for Lambda CRUD API infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

# Variables are defined in variables.tf

# Create placeholder ZIP file using data source
data "archive_file" "placeholder_zip" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"
  
  source {
    content = <<EOF
def lambda_handler(event, context):
    """
    Placeholder Lambda function for initial infrastructure deployment.
    This will be replaced with actual function code during deployment.
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '{"message": "Placeholder function - Deploy actual code using deployment scripts"}'
    }
EOF
    filename = "index.py"
  }
}

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
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "read_lambda_logs" {
  name              = "/aws/lambda/crud-api-read-${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "update_lambda_logs" {
  name              = "/aws/lambda/crud-api-update-${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "delete_lambda_logs" {
  name              = "/aws/lambda/crud-api-delete-${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# Lambda Functions
resource "aws_lambda_function" "create_lambda" {
  function_name = "crud-api-create-${var.environment}"
  role         = aws_iam_role.lambda_execution_role.arn
  handler      = "create_handler.lambda_handler"
  runtime      = var.lambda_runtime
  timeout      = var.lambda_timeout
  memory_size  = var.lambda_memory_size

  # Use dynamically created placeholder ZIP
  filename         = data.archive_file.placeholder_zip.output_path
  source_code_hash = data.archive_file.placeholder_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      REGION             = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.create_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "create"
  })

  # Ignore code changes - actual code will be deployed separately
  lifecycle {
    ignore_changes = [
      filename,
      last_modified,
      source_code_hash,
    ]
  }
}

resource "aws_lambda_function" "read_lambda" {
  filename         = data.archive_file.placeholder_zip.output_path
  source_code_hash = data.archive_file.placeholder_zip.output_base64sha256
  function_name    = "crud-api-read-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "read_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      REGION             = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.read_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "read"
  })

  lifecycle {
    ignore_changes = [
      filename,
      last_modified,
      source_code_hash,
    ]
  }
}

resource "aws_lambda_function" "update_lambda" {
  filename         = data.archive_file.placeholder_zip.output_path
  source_code_hash = data.archive_file.placeholder_zip.output_base64sha256
  function_name    = "crud-api-update-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "update_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      REGION             = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.update_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "update"
  })

  lifecycle {
    ignore_changes = [
      filename,
      last_modified,
      source_code_hash,
    ]
  }
}

resource "aws_lambda_function" "delete_lambda" {
  filename         = data.archive_file.placeholder_zip.output_path
  source_code_hash = data.archive_file.placeholder_zip.output_base64sha256
  function_name    = "crud-api-delete-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "delete_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      REGION             = var.aws_region
      ENVIRONMENT        = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.delete_lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = "delete"
  })

  lifecycle {
    ignore_changes = [
      filename,
      last_modified,
      source_code_hash,
    ]
  }
}

# Outputs are defined in outputs.tf