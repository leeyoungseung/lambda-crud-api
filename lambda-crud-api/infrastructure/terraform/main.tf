# ==============================================
# main.tf (fixed) - Lambda CRUD + packaging + IAM + DynamoDB
# ==============================================
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Project layout assumption:
#   repo_root/
#     lambdas/*.py
#     shared/
#     requirements.txt (optional)
#     infrastructure/terraform/*.tf   <-- execute terraform here
#
# We derive repo root from this module path.
locals {
  project_root = abspath("${path.module}/../..")

  functions = {
    create = {
      file    = "${local.project_root}/lambdas/create_handler.py"
      handler = "create_handler.lambda_handler"
      name    = "crud-api-create-${var.environment}"
      log     = "/aws/lambda/crud-api-create-${var.environment}"
    }
    read = {
      file    = "${local.project_root}/lambdas/read_handler.py"
      handler = "read_handler.lambda_handler"
      name    = "crud-api-read-${var.environment}"
      log     = "/aws/lambda/crud-api-read-${var.environment}"
    }
    update = {
      file    = "${local.project_root}/lambdas/update_handler.py"
      handler = "update_handler.lambda_handler"
      name    = "crud-api-update-${var.environment}"
      log     = "/aws/lambda/crud-api-update-${var.environment}"
    }
    delete = {
      file    = "${local.project_root}/lambdas/delete_handler.py"
      handler = "delete_handler.lambda_handler"
      name    = "crud-api-delete-${var.environment}"
      log     = "/aws/lambda/crud-api-delete-${var.environment}"
    }
  }

  build_root           = "${path.module}/build"
  table_name_with_env  = "${var.table_name}-${var.environment}"

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# -----------------------------
# DynamoDB Table
# -----------------------------
resource "aws_dynamodb_table" "items_table" {
  name         = local.table_name_with_env
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }

  tags = merge(local.common_tags, { Component = "database" })
}

# -----------------------------
# IAM: Lambda execution role + policies
# -----------------------------
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda-crud-api-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = merge(local.common_tags, { Component = "iam" })
}

# CloudWatch basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow Lambda to access our table
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "lambda-dynamodb-access-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      Resource = aws_dynamodb_table.items_table.arn
    }]
  })
}

# -----------------------------
# CloudWatch Log Groups (pre-create with retention)
# -----------------------------
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each          = local.functions
  name              = each.value.log
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# -----------------------------
# Build step (per function): copy handler/shared and vendor requirements
# -----------------------------
resource "null_resource" "build" {
  for_each = local.functions

  triggers = {
    handler_hash = filesha256(each.value.file)
    req_hash     = try(filesha256("${local.project_root}/requirements.txt"), "no-req")
    shared_hash  = try(filesha256("${local.project_root}/shared/__init__.py"), "no-shared")
  }

  provisioner "local-exec" {
    working_dir = path.module
    interpreter = ["/bin/bash", "-c"]
    command = <<EOT
set -euo pipefail

BUILD_DIR="${local.build_root}/${each.key}"
ROOT="${local.project_root}"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy handler
cp "${each.value.file}" "$BUILD_DIR/"

# Copy shared package if exists
if [ -d "$ROOT/shared" ]; then
  cp -r "$ROOT/shared" "$BUILD_DIR/shared"
fi

# Vendor dependencies to the zip root
if [ -s "$ROOT/requirements.txt" ]; then
  PYBIN="python3"
  # If repo-root/venv exists, prefer it
  if [ -x "$ROOT/venv/bin/python" ]; then PYBIN="$ROOT/venv/bin/python"; fi
  $PYBIN -m ensurepip --upgrade >/dev/null 2>&1 || true
  $PYBIN -m pip install --upgrade pip setuptools wheel >/dev/null
  $PYBIN -m pip install -r "$ROOT/requirements.txt" -t "$BUILD_DIR"
fi
EOT
  }
}

# -----------------------------
# Zip archive (per function)
# -----------------------------
data "archive_file" "lambda_zip" {
  for_each    = local.functions
  type        = "zip"
  source_dir  = "${local.build_root}/${each.key}"
  output_path = "${local.build_root}/${each.key}-function.zip"
  depends_on  = [null_resource.build]
}

# -----------------------------
# Lambda functions (per function)
# -----------------------------
resource "aws_lambda_function" "fn" {
  for_each      = local.functions
  function_name = each.value.name
  role          = aws_iam_role.lambda_execution_role.arn

  filename         = data.archive_file.lambda_zip[each.key].output_path
  source_code_hash = data.archive_file.lambda_zip[each.key].output_base64sha256

  handler     = each.value.handler
  runtime     = var.lambda_runtime
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.items_table.name
      REGION              = var.aws_region     # don't use AWS_REGION reserved key
      ENVIRONMENT         = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = merge(local.common_tags, {
    Component = "lambda"
    Operation = each.key
  })
}
