locals {
  hosted_zone_id = var.create_hosted_zone ? aws_route53_zone.this[0].zone_id : var.hosted_zone_id
}

resource "aws_route53_zone" "this" {
  count = var.create_hosted_zone ? 1 : 0
  name  = var.domain_zone_name
}

resource "aws_acm_certificate" "api" {
  domain_name       = var.api_fqdn
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  zone_id         = local.hosted_zone_id
  name            = each.value.name
  records         = [each.value.record]
  type            = each.value.type
  ttl             = 60
}

resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}

data "aws_lb_hosted_zone_id" "alb" {}

resource "aws_route53_record" "api_alias_a" {
  count   = var.alb_dns_name != "" ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.api_fqdn
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = data.aws_lb_hosted_zone_id.alb.id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api_alias_aaaa" {
  count   = var.alb_dns_name != "" ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.api_fqdn
  type    = "AAAA"

  alias {
    name                   = var.alb_dns_name
    zone_id                = data.aws_lb_hosted_zone_id.alb.id
    evaluate_target_health = true
  }
}
