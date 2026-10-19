# Phase 7 End-to-End (GPU)

Contributor path for GPU ASR on EKS. Assumes **Phase 6** is already running ([AWS Deployment — Phase 6](aws-deployment.md#contributor-path-phase-6-end-to-end)) and you have **GPU quota** (g5.xlarge) in the target region.

**Exit sign-off:** [Phase 7 exit checklist](../roadmap/dev-step-phase7-exit.md) after completing this path.

## Prerequisites

| Requirement | Doc |
|-------------|-----|
| Phase 6 EKS + ALB + (optional) DNS/TLS | [aws-deployment.md](aws-deployment.md) |
| AWS CLI, kubectl, Docker, Terraform | Same as Phase 6 |
| GPU node pool enabled in Terraform | [P7-001](../roadmap/dev-step-p7-001-gpu-node-pool.md) |

## Ordered steps

| Step | Dev-step | Action | Doc |
|------|----------|--------|-----|
| 1 | P7-001 | Enable GPU managed node group; apply Terraform; verify `node-type=gpu` nodes | [infra/eks/README.md](../../infra/eks/README.md#gpu-node-pool-p7-001) |
| 2 | P7-002 | Install NVIDIA device plugin; verify `nvidia.com/gpu` allocatable | [infra/eks/README.md](../../infra/eks/README.md#nvidia-device-plugin-p7-002) · [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md) |
| 3 | P7-003 | Build and push **`voragon/asr-inference`** to ECR | [docker/asr-inference/README.md](../../docker/asr-inference/README.md) · [infra/ecr/README.md](../../infra/ecr/README.md) |
| 4 | — | Rebuild and push **`realtime-backend`** (includes remote ASR client from P7-006) | [infra/ecr/README.md](../../infra/ecr/README.md) · [docker/realtime-backend/Dockerfile](../../docker/realtime-backend/Dockerfile) |
| 5 | P7-004–P7-006 | Point Kustomize at **both** ECR URIs; `kubectl apply -k k8s/eks` | [k8s/eks/README.md](../../k8s/eks/README.md) |
| 6 | P7-005 | Confirm `voragon-asr-model-cache` bound; first ASR pod Ready (model download) | [k8s/eks/README.md](../../k8s/eks/README.md#model-weight-pvcs-p7-005) |
| 7 | P7-006 | Verify remote ASR: realtime `/health` + in-cluster `curl` to `asr-service:8081/health` | [k8s/eks/README.md](../../k8s/eks/README.md) (P7-006 section) |
| 8 | P7-007 | Scrape **`GET /metrics`** on asr-service during transcription | [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md#gpu-metrics-p7-007) · [observability.md](observability.md) |
| 9 | — | **Desktop or CLI E2E:** `wss://<api-host>/v1/realtime` → partials/finals | [desktop/README.md](../../desktop/README.md#production-aws-staging) |

## Kustomize apply (both images)

From the **repository root**:

```bash
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export ECR_URI="$(terraform -chdir=infra/ecr output -raw repository_url)"
export ASR_ECR_URI="$(terraform -chdir=infra/ecr output -raw asr_repository_url)"
export TAG="${TAG:-$(git rev-parse --short HEAD)}"

cd k8s/eks
kustomize edit set image "voragon/realtime-backend=${ECR_URI}:${TAG}"
kustomize edit set image "voragon/asr-inference=${ASR_ECR_URI}:${TAG}"
kubectl apply -k .
kubectl wait -n voragon --for=condition=ready pod -l app=asr-service --timeout=900s
kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=600s
```

`realtime-config` sets **`ASR_BACKEND=remote`** and **`ASR_REMOTE_BASE_URL=http://asr-service:8081`** (CPU pods call GPU inference over HTTP).

## Remote ASR smoke

```bash
kubectl exec -n voragon deploy/realtime-backend -- curl -sf http://asr-service:8081/health
kubectl port-forward -n voragon svc/realtime-service 8000:8000
curl -sf http://localhost:8000/health | jq .asr
```

Expect `asr.backend` **`remote`** and `asr.ready` **true** when the GPU service is healthy.

## Metrics during transcription

```bash
kubectl port-forward -n voragon svc/asr-service 8081:8081
# In another terminal, run desktop E2E or send audio via test client, then:
curl -s http://localhost:8081/metrics | grep -E 'voragon_gpu_utilization|voragon_asr_inference_duration'
```

Non-zero **`voragon_gpu_utilization{gpu_index="0"}`** during load confirms the GPU metrics path ([P7-007](../roadmap/dev-step-p7-007-gpu-metrics.md)).

## Latency validation (engineering)

Record baseline from Prometheus or manual timing:

| Signal | Where |
|--------|--------|
| ASR inference latency | `voragon_asr_inference_duration_seconds` on **asr-service** `/metrics` (histogram by `kind=partial\|final`) |
| End-to-end (client) | Desktop stats or logs; compare to targets in [observability.md](observability.md) |

Document p50/p95 in your runbook or Phase 7 exit sign-off; repo targets remain **engineering goals** until you benchmark in AWS.

## Scaling smoke (operator)

```bash
kubectl scale deployment/asr-service -n voragon --replicas=2
kubectl get pods -n voragon -l app=asr-service -o wide
```

With a single **ReadWriteOnce** model-cache PVC ([P7-005](../roadmap/dev-step-p7-005-model-weights-gpu.md)), only **one** GPU pod mounts the volume at a time — a second replica may stay **Pending** until you add ReadWriteMany storage or per-pod PVCs. For MVP exit, verify **rollout restart** (`kubectl delete pod -l app=asr-service`) and client reconnect rather than multi-replica ASR on one PVC.

## Degraded path

```bash
kubectl scale deployment/asr-service -n voragon --replicas=0
# realtime /health should show asr not ready; clients receive ASR_MODEL_UNAVAILABLE per API spec
```

## Related

- [aws-deployment.md](aws-deployment.md) — Phase 6 + Phase 7 summary
- [kubernetes.md](../architecture/kubernetes.md) — GPU node pools and services
- [dev-step-phase7-exit.md](../roadmap/dev-step-phase7-exit.md) — operator sign-off
