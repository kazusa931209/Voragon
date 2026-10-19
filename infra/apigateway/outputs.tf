output "auth_token_url" {
  description = "POST here with x-api-key to obtain a JWT for WebSocket connect."
  value       = "${aws_apigatewayv2_api.auth_http.api_endpoint}/${aws_apigatewayv2_stage.staging.name}/v1/auth/token"
}

output "jwt_secret_arn" {
  description = "Secrets Manager ARN — sync jwt_secret to EKS (JWT_SECRET) when enabling auth."
  value       = aws_secretsmanager_secret.realtime_jwt.arn
}

output "mint_api_key" {
  description = "x-api-key for POST /v1/auth/token (sensitive)."
  value       = random_password.mint_api_key.result
  sensitive   = true
}
