output "api_fqdn" {
  description = "Public API hostname (desktop Backend URL host)."
  value       = var.api_fqdn
}

output "websocket_url" {
  description = "Production WebSocket URL for desktop settings."
  value       = "wss://${var.api_fqdn}/v1/realtime"
}

output "acm_certificate_arn" {
  description = "ACM cert ARN for ALB Ingress annotation certificate-arn."
  value       = aws_acm_certificate.api.arn
}

output "hosted_zone_id" {
  description = "Route 53 zone ID used for records."
  value       = local.hosted_zone_id
}

output "hosted_zone_name_servers" {
  description = "Delegate parent domain to these when create_hosted_zone=true."
  value       = var.create_hosted_zone ? aws_route53_zone.this[0].name_servers : []
}
