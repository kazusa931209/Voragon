# Custom hostname and TLS (P6-007)

Stable **`wss://<api-host>/v1/realtime`** uses:

1. **ACM** certificate (Terraform [infra/dns](../../../infra/dns/README.md))
2. **Ingress** cert ARN + `host` rule ([../alb/ingress.yaml](../alb/ingress.yaml) — replace `REPLACE_ACM_CERTIFICATE_ARN` and `REPLACE_API_FQDN`)
3. **Route 53** alias A/AAAA from `api_fqdn` → ALB DNS name (second `infra/dns` apply with `alb_dns_name`)

Default documented hostname: **`api.voragon.example`** (change `api_fqdn` to your staging domain).

## Desktop settings (after P6-005)

| Setting | Example |
|---------|---------|
| Backend URL | `wss://api.voragon.example/v1/realtime` |
| Auth token URL | API Gateway `POST …/v1/auth/token` (unchanged) |

## Verify DNS

```bash
dig +short api.voragon.example
curl -f https://api.voragon.example/health
```

See [infra/dns/README.md](../../../infra/dns/README.md) for full apply order and rollback.
