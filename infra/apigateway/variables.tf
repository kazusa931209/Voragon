variable "aws_region" {
  description = "AWS region for API Gateway and Lambda."
  type        = string
  default     = "ap-northeast-1"
}

variable "name_prefix" {
  description = "Prefix for resource names (staging cluster name is a common choice)."
  type        = string
  default     = "voragon-staging"
}

variable "stage_name" {
  description = "API Gateway HTTP API stage name."
  type        = string
  default     = "staging"
}
