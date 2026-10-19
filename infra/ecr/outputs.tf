output "repository_url" {
  description = "Docker pull/push URI for the realtime-backend repository."
  value       = aws_ecr_repository.realtime_backend.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository."
  value       = aws_ecr_repository.realtime_backend.arn
}

output "repository_name" {
  description = "ECR repository name (for aws ecr describe-images)."
  value       = aws_ecr_repository.realtime_backend.name
}

output "asr_repository_url" {
  description = "Docker pull/push URI for the asr-inference repository (P7-003)."
  value       = aws_ecr_repository.asr_inference.repository_url
}

output "asr_repository_name" {
  description = "ECR ASR repository name."
  value       = aws_ecr_repository.asr_inference.name
}

output "ai_gateway_repository_url" {
  description = "Docker pull/push URI for the ai-gateway repository (P8-007)."
  value       = aws_ecr_repository.ai_gateway.repository_url
}

output "ai_gateway_repository_name" {
  description = "ECR AI Gateway repository name."
  value       = aws_ecr_repository.ai_gateway.name
}
