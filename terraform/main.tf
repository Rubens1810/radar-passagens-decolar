terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. Tabela DynamoDB (Single-Table Design: PK + SK)
resource "aws_dynamodb_table" "price_history" {
  name         = "${var.project_name}-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = {
    Project = var.project_name
    Managed = "Terraform"
  }
}

# 2. IAM Role para a Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

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
}

# Permissão básica de logs no CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permissão restrita apenas à tabela DynamoDB do projeto (Least Privilege)
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.project_name}-dynamodb-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.price_history.arn
      }
    ]
  })
}

# 3. Função AWS Lambda
resource "aws_lambda_function" "radar_worker" {
  filename         = "${path.module}/../build/lambda_package.zip"
  function_name    = "${var.project_name}-worker"
  role             = aws_iam_role.lambda_role.arn
  handler          = "src.lambda_handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../build/lambda_package.zip")
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      STORAGE_BACKEND     = "dynamodb"
      DYNAMODB_TABLE      = aws_dynamodb_table.price_history.name
      SERPAPI_KEY         = var.serpapi_key
      DISCORD_WEBHOOK_URL = var.discord_webhook_url
    }
  }

  tags = {
    Project = var.project_name
    Managed = "Terraform"
  }
}

# 4. Agendamento diário no Amazon EventBridge (12:00 UTC = 09:00 BRT)
resource "aws_cloudwatch_event_rule" "daily_scan" {
  name                = "${var.project_name}-daily-scan"
  description         = "Dispara o radar de passagens diariamente às 09:00 BRT"
  schedule_expression = "cron(0 12 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_scan.name
  target_id = "TriggerFlightRadarLambda"
  arn       = aws_lambda_function.radar_worker.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.radar_worker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_scan.arn
}