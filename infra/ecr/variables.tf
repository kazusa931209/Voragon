variable "aws_region" {
  description = "AWS region for the ECR repository."
  type        = string
  default     = "ap-northeast-1"
}

variable "repository_name" {
  description = "ECR repository name (supports nested path with /)."
  type        = string
  default     = "voragon/realtime-backend"
}

variable "asr_repository_name" {
  description = "ECR repository for ASR inference images (P7-003)."
  type        = string
  default     = "voragon/asr-inference"
}
