variable "aws_region" {
  description = "AWS region (match infra/ecr and image pushes)."
  type        = string
  default     = "ap-northeast-1"
}

variable "cluster_name" {
  description = "EKS cluster name (staging/non-prod)."
  type        = string
  default     = "voragon-staging"
}

variable "cluster_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.31"
}

variable "vpc_cidr" {
  description = "VPC CIDR for the EKS cluster."
  type        = string
  default     = "10.0.0.0/16"
}

variable "node_instance_types" {
  description = "CPU instance types for the managed node group."
  type        = list(string)
  default     = ["m6i.large"]
}

variable "node_desired_size" {
  description = "Desired worker count (staging default: 1)."
  type        = number
  default     = 1
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "enable_gpu_node_group" {
  description = "Create a managed GPU node group (P7-001). Requires g5 quota in the region."
  type        = bool
  default     = true
}

variable "gpu_node_instance_types" {
  description = "GPU instance types for the managed node group (ADR-010: g5.xlarge)."
  type        = list(string)
  default     = ["g5.xlarge"]
}

variable "gpu_node_desired_size" {
  description = "Desired GPU worker count (staging default: 1)."
  type        = number
  default     = 1
}

variable "gpu_node_min_size" {
  type    = number
  default = 0
}

variable "gpu_node_max_size" {
  type    = number
  default = 2
}

variable "nvidia_device_plugin_chart_version" {
  description = "Helm chart version for NVIDIA k8s-device-plugin (P7-002)."
  type        = string
  default     = "0.17.1"
}

variable "cloudwatch_log_group_name" {
  description = "CloudWatch log group for voragon realtime-backend container logs (P6-006)."
  type        = string
  default     = "/voragon/eks/realtime-backend"
}

variable "cloudwatch_log_retention_days" {
  description = "Retention for the realtime-backend CloudWatch log group."
  type        = number
  default     = 14
}
