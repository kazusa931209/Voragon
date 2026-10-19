# ALB Ingress: realtime-backend (P6-004)

Expose `realtime-service` on an **internet-facing ALB** with **sticky sessions** (WebSocket affinity) and **HTTPS** (ACM certificate).

## Prerequisites

- [P6-002](../../../infra/eks/README.md) cluster — run `terraform apply` in `infra/eks` (installs **AWS Load Balancer Controller** via Helm)
- [P6-003](../README.md) — `realtime-backend` Running in `voragon`
- **ACM certificate** in the same region as the cluster — provision via [P6-007 infra/dns](../../../infra/dns/README.md) (or import a cert whose SAN covers your API hostname).

Optional before ALB: scale to **2 replicas** for rolling updates with stickiness:

```bash
kubectl scale deployment/realtime-backend -n voragon --replicas=2
```

## 1. Configure certificate and hostname on Ingress

After [infra/dns](../../../infra/dns/README.md) (P6-007) or with your own ACM ARN:

```bash
export ACM_ARN="$(terraform -chdir=infra/dns output -raw acm_certificate_arn)"
export API_FQDN="$(terraform -chdir=infra/dns output -raw api_fqdn)"
sed -i '' "s|REPLACE_ACM_CERTIFICATE_ARN|${ACM_ARN}|g" k8s/eks/alb/ingress.yaml
sed -i '' "s|REPLACE_API_FQDN|${API_FQDN}|g" k8s/eks/alb/ingress.yaml
```

Details: [k8s/eks/dns/README.md](../dns/README.md).

For **HTTP-only** smoke tests (not production), you may temporarily replace `listen-ports` with `'[{"HTTP":80}]'` and remove `certificate-arn` / `ssl-redirect` — revert before sign-off (acceptance uses HTTPS).

## 2. Apply Ingress

```bash
kubectl apply -f k8s/eks/alb/ingress.yaml
kubectl get ingress -n voragon realtime-backend -w
```

Note the **ADDRESS** (ALB DNS name). Warmup: target group healthy after backend ASR startup (several minutes on cold start).

## 3. Verify health

```bash
export ALB_HOST="$(kubectl get ingress -n voragon realtime-backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"
# Prefer custom hostname when Route 53 alias exists (P6-007):
curl -f "https://${API_FQDN:-$ALB_HOST}/health"
```

## 4. WebSocket

```bash
# Example with websocat (install separately):
websocat -n1 "wss://${ALB_HOST}/v1/realtime"
# Expect session.started JSON after client hello per API spec
```

Or point the desktop app at `wss://${ALB_HOST}/v1/realtime` (no API Gateway yet — P6-005).

## Sticky sessions

Target group stickiness is enabled via Ingress annotations (`lb_cookie`, 24h). See [kubernetes architecture — WebSocket scaling](../../../docs/architecture/kubernetes.md).

## Related

- [infra/eks/README.md](../../../infra/eks/README.md) — Load Balancer Controller (Terraform/Helm)
- [docs/operations/aws-deployment.md](../../../docs/operations/aws-deployment.md)
