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
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

# Variables are defined in variables.tf

########################################
# 빌드 관련 로컬 값
########################################
# 이 파일이 있는 경로: .../infrastructure/terraform
# 프로젝트 루트: 두 단계 위
locals {
  project_root = abspath("${path.module}/../..")

  # 함수 메타 (각 핸들러에 lambda_handler가 있다고 가정)
  functions = {
    create = {
      file    = "${local.project_root}/lambdas/create_handler.py"
      handler = "create_handler.lambda_handler"
      log     = "/aws/lambda/crud-api-create-${var.environment}"
      name    = "crud-api-create-${var.environment}"
    }
    read = {
      file    = "${local.project_root}/lambdas/read_handler.py"
      handler = "read_handler.lambda_handler"
      log     = "/aws/lambda/crud-api-read-${var.environment}"
      name    = "crud-api-read-${var.environment}"
    }
    update = {
      file    = "${local.project_root}/lambdas/update_handler.py"
      handler = "update_handler.lambda_handler"
      log     = "/aws/lambda/crud-api-update-${var.environment}"
      name    = "crud-api-update-${var.environment}"
    }
    delete = {
      file    = "${local.project_root}/lambdas/delete_handler.py"
      handler = "delete_handler.lambda_handler"
      log     = "/aws/lambda/crud-api-delete-${var.environment}"
      name    = "crud-api-delete-${var.environment}"
    }
  }

  build_root = "${path.module}/build"

  table_name_with_env = "${var.table_name}-${var.environment}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

########################################
# DynamoDB Table
########################################
resource "aws_dynamodb_table" "items_table" {
  name         = local.table_name_with_env
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

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

  tags = merge(local.common_tags, { Component = "database" })
}

########################################
# IAM Role / Policy
########################################
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

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

########################################
# CloudWatch Log Groups (선제 생성)
########################################
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each          = local.functions
  name              = each.value.log
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

########################################
# (1) 함수별 빌드 단계: 핸들러/공유코드/의존성 수집
########################################
resource "null_resource" "build" {
  for_each = local.functions

  # 핸들러 / requirements.txt / shared 주요 파일 변경 시 재빌드
  triggers = {
    handler_hash = filesha256(each.value.file)
    req_hash     = try(filesha256("${local.project_root}/requirements.txt"), "no-req")
    shared_init  = try(filesha256("${local.project_root}/shared/__init__.py"), "no-shared")
  }

  provisioner "local-exec" {
    working_dir = path.module
    command = <<EOT
set -euo pipefail

BUILD_DIR="${local.build_root}/${each.key}"
ROOT="${local.project_root}"

echo "[Build:${each.key}] prepare build dir: $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# 1) 핸들러 복사
cp "${each.value.file}" "$BUILD_DIR/"

# 2) shared 패키지 복사 (있으면)
if [ -d "$ROOT/shared" ]; then
  cp -r "$ROOT/shared" "$BUILD_DIR/shared"
fi

# 3) 의존성 설치 (requirements.txt가 있으면 zip 루트로 설치)
if [ -s "$ROOT/requirements.txt" ]; then
  PYBIN="python3"
  if [ -x "$ROOT/venv/bin/python" ]; then PYBIN="$ROOT/venv/bin/python"; fi
  $PYBIN -m ensurepip --upgrade >/dev/null 2>&1 || true
  $PYBIN -m pip install --upgrade pip setuptools wheel >/dev/null
  echo "[Build:${each.key}] pip install -r requirements.txt -t $BUILD_DIR"
  $PYBIN -m pip install -r "$ROOT/requirements.txt" -t "$BUILD_DIR"
else
  echo "[Build:${each.key}] no requirements.txt; skip vendoring"
fi
EOT
  }
}

########################################
# (2) zip 생성 (함수별)
########################################
data "archive_file" "lambda_zip" {
  for_each    = local.functions
  type        = "zip"
  source_dir  = "${local.build_root}/${each.key}"
  output_path = "${local.build_root}/${each.key}-function.zip"

  depends_on = [null_resource.build]
}

########################################
# (3) Lambda Functions (함수별)
########################################
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
      REGION              = var.aws_region   # 예약키(AWS_REGION) 대신 사용자 정의 키 사용
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

# Outputs are defined in outputs.tf