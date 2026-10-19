data "archive_file" "token_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda/token/handler.py"
  output_path = "${path.module}/lambda/token/handler.zip"
}

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "random_password" "mint_api_key" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "realtime_jwt" {
  name                    = "${var.name_prefix}/realtime-jwt"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "realtime_jwt" {
  secret_id = aws_secretsmanager_secret.realtime_jwt.id
  secret_string = jsonencode({
    jwt_secret   = random_password.jwt_secret.result
    mint_api_key = random_password.mint_api_key.result
    audience     = "voragon-realtime"
  })
}

resource "aws_iam_role" "token_lambda" {
  name = "${var.name_prefix}-auth-token-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "token_lambda_basic" {
  role       = aws_iam_role.token_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "auth_token" {
  function_name = "${var.name_prefix}-auth-token"
  role          = aws_iam_role.token_lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 10

  filename         = data.archive_file.token_lambda.output_path
  source_code_hash = data.archive_file.token_lambda.output_base64sha256

  environment {
    variables = {
      JWT_SECRET   = random_password.jwt_secret.result
      MINT_API_KEY = random_password.mint_api_key.result
    }
  }
}

resource "aws_apigatewayv2_api" "auth_http" {
  name          = "${var.name_prefix}-auth"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "auth_token" {
  api_id                 = aws_apigatewayv2_api.auth_http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.auth_token.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "auth_token" {
  api_id    = aws_apigatewayv2_api.auth_http.id
  route_key = "POST /v1/auth/token"
  target    = "integrations/${aws_apigatewayv2_integration.auth_token.id}"
}

resource "aws_apigatewayv2_stage" "staging" {
  api_id      = aws_apigatewayv2_api.auth_http.id
  name        = var.stage_name
  auto_deploy = true
}

resource "aws_lambda_permission" "auth_token_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_token.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.auth_http.execution_arn}/*/*"
}
