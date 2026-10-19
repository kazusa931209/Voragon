variable "aws_region" {
  description = "Region for ACM and Route 53 (must match EKS / ALB)."
  type        = string
  default     = "ap-northeast-1"
}

variable "api_fqdn" {
  description = "Public API hostname (WebSocket + HTTPS health), e.g. api.voragon.example."
  type        = string
  default     = "api.voragon.example"
}

variable "create_hosted_zone" {
  description = "Create a new Route 53 public hosted zone for domain_zone_name."
  type        = bool
  default     = false
}

variable "domain_zone_name" {
  description = "Route 53 zone apex when create_hosted_zone=true (e.g. voragon.example)."
  type        = string
  default     = "voragon.example"
}

variable "hosted_zone_id" {
  description = "Existing Route 53 hosted zone ID when create_hosted_zone=false."
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "ALB hostname from Ingress status; set on apply after k8s/eks/alb Ingress exists."
  type        = string
  default     = ""
}
