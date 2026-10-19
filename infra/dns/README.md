# DNS and TLS (P6-007)

ACM certificate (DNS validation) and Route 53 alias records for the **ALB Ingress** WebSocket / HTTPS endpoint.

| Role | Host |
|------|------|
| WSS + `/health` | `api_fqdn` (default **`api.voragon.example`**) → ALB |
| JWT mint (P6-005) | API Gateway `execute-api` URL (unchanged unless you add a custom domain later) |

## Prerequisites

- Route 53 **hosted zone** for your domain (or set `create_hosted_zone=true` for a new zone and delegate NS at the registrar).
- [P6-004 Ingress](../../k8s/eks/alb/README.md) applied at least once if you need the ALB DNS name for alias records.

## 1. Issue ACM certificate

Use an **existing** zone (typical):

```bash
export HOSTED_ZONE_ID="Z0123456789ABCDEFGHIJ"
export API_FQDN="api.voragon.example"   # or your staging FQDN

terraform -chdir=infra/dns init
terraform -chdir=infra/dns apply \
  -var="hosted_zone_id=${HOSTED_ZONE_ID}" \
  -var="api_fqdn=${API_FQDN}"
```

Note **`acm_certificate_arn`** output.

## 2. Wire cert + hostname on Ingress

```bash
export ACM_ARN="$(terraform -chdir=infra/dns output -raw acm_certificate_arn)"
export API_FQDN="$(terraform -chdir=infra/dns output -raw api_fqdn)"

cp k8s/eks/alb/ingress.yaml k8s/eks/alb/ingress.yaml.local
sed -i '' "s|REPLACE_ACM_CERTIFICATE_ARN|${ACM_ARN}|g" k8s/eks/alb/ingress.yaml.local
sed -i '' "s|REPLACE_API_FQDN|${API_FQDN}|g" k8s/eks/alb/ingress.yaml.local
kubectl apply -f k8s/eks/alb/ingress.yaml.local
```

Or edit [ingress.yaml](../../k8s/eks/alb/ingress.yaml) in place (do not commit account-specific ARNs).

Wait for Ingress **ADDRESS** (ALB DNS name).

## 3. Route 53 alias to ALB

```bash
export ALB_DNS="$(kubectl get ingress -n voragon realtime-backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"

terraform -chdir=infra/dns apply \
  -var="hosted_zone_id=${HOSTED_ZONE_ID}" \
  -var="api_fqdn=${API_FQDN}" \
  -var="alb_dns_name=${ALB_DNS}"
```

## 4. Verify

```bash
dig +short "${API_FQDN}"
curl -f "https://${API_FQDN}/health"
# Desktop: wss://${API_FQDN}/v1/realtime (+ P6-005 auth settings)
```

## Certificate renewal and rollback

ACM **auto-renews** DNS-validated certs while validation CNAME records remain. If renewal fails, check Route 53 validation records and [ACM console](https://console.aws.amazon.com/acm/) for the certificate status.

**Rollback:** remove or repoint the `api` alias records in Route 53; revert Ingress to the previous cert ARN or ALB-only hostname; clients fall back to the raw ALB DNS name until DNS is updated again.

## Related

- [k8s/eks/dns/README.md](../../k8s/eks/dns/README.md)
- [aws-deployment.md](../../docs/operations/aws-deployment.md)
