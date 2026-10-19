# EKS: realtime-backend (P6-003) + asr-service (P7-004)

Deploy **in-process ASR** `realtime-backend` (CPU) and optional **GPU** `asr-service` to the [P6-002 EKS cluster](../../infra/eks/README.md) using [ECR images](../../infra/ecr/README.md).

Parity with [k8s/local/](../local/) for realtime (Kind), with ECR image pull and `gp2` PVC for model cache. **`asr-service` is EKS-only** (GPU node pool); see [gpu/README.md](gpu/README.md).

## Prerequisites

- P6-002 cluster and kubeconfig (`aws eks update-kubeconfig …`)
- Image pushed to ECR ([infra/ecr/README.md](../../infra/ecr/README.md))

## 1. Point Deployments at ECR

From the **repository root**:

```bash
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export ECR_URI="$(terraform -chdir=infra/ecr output -raw repository_url)"
export ASR_ECR_URI="$(terraform -chdir=infra/ecr output -raw asr_repository_url)"
export TAG="${TAG:-$(git rev-parse --short HEAD)}"

cd k8s/eks
kustomize edit set image "voragon/realtime-backend=${ECR_URI}:${TAG}"
kustomize edit set image "voragon/asr-inference=${ASR_ECR_URI}:${TAG}"
```

This updates `kustomization.yaml` locally (do not commit your account-specific URI unless intentional).

## 2. Apply

```bash
kubectl apply -k .
kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=600s
kubectl wait -n voragon --for=condition=ready pod -l app=asr-service --timeout=900s
```

First startup may take several minutes (ASR warmup + model download into PVC). GPU `asr-service` pods schedule only on nodes with `node-type=gpu` ([gpu/README.md](gpu/README.md)).

**P7-006 / P8-006:** `realtime-config` sets `ASR_BACKEND=remote`, `ASR_REMOTE_VIA_AI_GATEWAY=true`, and `ASR_REMOTE_BASE_URL=http://ai-gateway:8080` so CPU `realtime-backend` transcribes via the AI Gateway (not direct `asr-service`). Requires `ai-gateway` Deployment (P8-008). Kind/Compose keep in-process ASR (`k8s/local/`, Docker Compose).

Verify gateway path (after ai-gateway is deployed):

```bash
kubectl exec -n voragon deploy/realtime-backend -- curl -sf http://ai-gateway:8080/health
```

Degraded behavior when ASR is down:

```bash
kubectl scale deployment/asr-service -n voragon --replicas=0
curl -sf http://localhost:8000/health   # via port-forward; expect asr.ready false / degraded
```

## 3. Health check

```bash
kubectl port-forward -n voragon svc/realtime-service 8000:8000
curl -f http://localhost:8000/health
```

## 4. PVC / pod restart

```bash
kubectl delete pod -n voragon -l app=realtime-backend
kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=600s
```

Second startup should be faster when weights are cached on the PVC.

## Model weight PVCs (P7-005)

| PVC | Workload | Node pool | Size | Mount path | Cache env |
|-----|----------|-----------|------|------------|-----------|
| `voragon-model-cache` | `realtime-backend` | CPU | 10Gi (`gp2`) | `/var/lib/voragon/model-cache` | `HF_HOME`, `TORCH_HOME` in `realtime-config` |
| `voragon-asr-model-cache` | `asr-service` | GPU | 10Gi (`gp2`) | `/var/lib/voragon/model-cache` | `HF_HOME`, `TORCH_HOME` in `asr-config` |

Whisper weights download on first Ready; faster-whisper uses `ASR_MODEL` from `asr-config` (default `tiny`). GPU pods use a **separate** PVC because `ReadWriteOnce` EBS volumes attach to one node (CPU vs GPU).

ASR pod restart (verify cache):

```bash
kubectl delete pod -n voragon -l app=asr-service
kubectl wait -n voragon --for=condition=ready pod -l app=asr-service --timeout=900s
kubectl exec -n voragon deploy/asr-service -- ls -la /var/lib/voragon/model-cache/huggingface
```

## ALB Ingress (P6-004)

Public HTTPS/WSS via ALB: [alb/README.md](alb/README.md) (after Load Balancer Controller is installed from [infra/eks](../../infra/eks/README.md)).

## JWT auth (P6-005)

Optional staging auth: [infra/apigateway/README.md](../../infra/apigateway/README.md) mints tokens; enable validation with [jwt-auth.example.yaml](jwt-auth.example.yaml). Desktop uses ALB `wss://` URL plus API Gateway token URL settings.

## CloudWatch logging (P6-006)

Fluent Bit → CloudWatch for `realtime-backend` JSON logs: [logging/README.md](logging/README.md) (Terraform in [infra/eks](../../infra/eks/README.md)).

## DNS and TLS (P6-007)

ACM + Route 53 for `api.voragon.example` (or your `api_fqdn`): [dns/README.md](dns/README.md), Terraform [infra/dns](../../infra/dns/README.md).

## Replicas before ALB (P6-004)

Default **1** replica for first E2E. Before ALB Ingress, scale to **2** for rolling updates with `maxUnavailable: 0`:

```bash
kubectl scale deployment/realtime-backend -n voragon --replicas=2
```

## Related

- [k8s/README.md](../README.md) — Kind local path
- [docs/operations/aws-deployment.md](../../docs/operations/aws-deployment.md)
