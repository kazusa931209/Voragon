# Phase 8 End-to-End (AI Gateway)

Contributor path for the **AI Gateway** on EKS. Assumes **Phase 7** GPU ASR is running ([Phase 7 end-to-end (GPU)](phase7-gpu-path.md)).

**Exit sign-off:** [Phase 8 exit checklist](../roadmap/dev-step-phase8-exit.md) after completing this path.

## Prerequisites

| Requirement | Doc |
|-------------|-----|
| Phase 7 `asr-service` on GPU nodes | [phase7-gpu-path.md](phase7-gpu-path.md) |
| ECR repos for realtime, ASR, ai-gateway | [infra/ecr/README.md](../../infra/ecr/README.md) |
| P8-001–P8-009 implemented in repo | [dev-steps index](../roadmap/dev-steps-index.md#phase-8-ai-gateway) |

## Ordered steps

| Step | Dev-step | Action | Doc |
|------|----------|--------|-----|
| 1 | P8-001–P8-005 | Run ai-gateway locally; registry, proxy, health, fallback (pytest) | [ai-gateway.md](../architecture/ai-gateway.md) |
| 2 | P8-007 | Build and push **`voragon/ai-gateway`** to ECR | [docker/ai-gateway/README.md](../../docker/ai-gateway/README.md) |
| 3 | P8-008 | Extend `k8s/eks` with ai-gateway Deployment/Service/ConfigMap | [k8s/eks/README.md](../../k8s/eks/README.md) |
| 4 | P8-006 | Confirm `realtime-config` uses `ASR_REMOTE_VIA_AI_GATEWAY` + `http://ai-gateway:8080` | [k8s/eks/configmap.yaml](../../k8s/eks/configmap.yaml) |
| 5 | — | `kubectl apply -k k8s/eks`; wait for `app=ai-gateway` Ready | [k8s/eks/README.md](../../k8s/eks/README.md) |
| 6 | P8-009 | Scrape **`GET /metrics`** on ai-gateway during inference | [observability.md](observability.md) |
| 7 | — | **Desktop or CLI E2E:** partials/finals via production WebSocket | [desktop/README.md](../../desktop/README.md#production-aws-staging) |

## Kustomize apply (three images)

From the **repository root**:

```bash
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export ECR_URI="$(terraform -chdir=infra/ecr output -raw repository_url)"
export ASR_ECR_URI="$(terraform -chdir=infra/ecr output -raw asr_repository_url)"
export AI_GATEWAY_ECR_URI="$(terraform -chdir=infra/ecr output -raw ai_gateway_repository_url)"
export TAG="${TAG:-$(git rev-parse --short HEAD)}"

cd k8s/eks
kustomize edit set image "voragon/realtime-backend=${ECR_URI}:${TAG}"
kustomize edit set image "voragon/asr-inference=${ASR_ECR_URI}:${TAG}"
kustomize edit set image "voragon/ai-gateway=${AI_GATEWAY_ECR_URI}:${TAG}"
kubectl apply -k .
kubectl wait -n voragon --for=condition=ready pod -l app=asr-service --timeout=900s
kubectl wait -n voragon --for=condition=ready pod -l app=ai-gateway --timeout=600s
kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=600s
```

## Gateway smoke

```bash
kubectl exec -n voragon deploy/realtime-backend -- curl -sf http://ai-gateway:8080/health
kubectl exec -n voragon deploy/realtime-backend -- curl -sf http://ai-gateway:8080/v1/models | head
```

## Model change without code deploy

Edit **`ai-gateway-config`** registry YAML (capability → model endpoint), then rollout:

```bash
kubectl apply -k k8s/eks
kubectl rollout restart deployment/ai-gateway -n voragon
```

## Fallback validation

With a registry that lists primary + fallback ASR endpoints, stop the primary `asr-service` pod or mark unhealthy; inference via gateway should still succeed (see [P8-005](../roadmap/dev-step-p8-005-fallback-routing.md)).

## Local dev (no EKS)

- **Compose / Kind:** realtime keeps in-process or direct ASR; gateway is optional (`python -m app.ai_gateway.main` + env in [backend/.env.example](../../backend/.env.example)).
- **EKS:** realtime **must** use gateway per `realtime-config` (P8-006).
