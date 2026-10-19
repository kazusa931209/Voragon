# EKS GPU (Phase 7)

GPU node pool and device plugin are provisioned by Terraform ([infra/eks/README.md](../../../infra/eks/README.md)):

| Step | Dev-step | Component |
|------|----------|-----------|
| Node pool | P7-001 | Managed node group `gpu`, taint `nvidia.com/gpu=true:NoSchedule` |
| Device plugin | P7-002 | Helm `nvidia-device-plugin` in `kube-system` |

## Verify device plugin (P7-002)

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=nvidia-device-plugin -o wide
kubectl describe node -l node-type=gpu | grep -A5 'Capacity:\|Allocatable:'
```

Allocatable should include `nvidia.com/gpu`.

## ASR image (P7-003)

Build and push: [docker/asr-inference/README.md](../../../docker/asr-inference/README.md).

## Deploy asr-service (P7-004)

Requires P7-001 GPU nodes, P7-002 device plugin, and P7-003 image in ECR.

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
```

Verify scheduling on GPU nodes:

```bash
kubectl get pods -n voragon -l app=asr-service -o wide
kubectl describe pod -n voragon -l app=asr-service | grep -E 'Node:|nvidia.com/gpu'
```

In-cluster health (from a debug pod):

```bash
kubectl run -n voragon curl-asr --rm -it --restart=Never --image=curlimages/curl:8.5.0 -- \
  curl -sf http://asr-service:8081/health
```

Port-forward alternative:

```bash
kubectl port-forward -n voragon svc/asr-service 8081:8081
curl -sf http://localhost:8081/health | jq .
```

## Model weight cache (P7-005)

`asr-service` mounts PVC **`voragon-asr-model-cache`** (10Gi `gp2`) at **`/var/lib/voragon/model-cache`**. Hugging Face / faster-whisper caches use **`HF_HOME=/var/lib/voragon/model-cache/huggingface`** and **`TORCH_HOME=/var/lib/voragon/model-cache/torch`** (`asr-config`). Model id: **`ASR_MODEL`** (default `tiny`).

After first Ready, delete the pod and confirm faster startup:

```bash
kubectl delete pod -n voragon -l app=asr-service
kubectl wait -n voragon --for=condition=ready pod -l app=asr-service --timeout=900s
kubectl get pvc -n voragon voragon-asr-model-cache
```

See [k8s/eks/README.md](../README.md#model-weight-pvcs-p7-005) for the full PVC table.

## GPU metrics (P7-007)

`asr-service` exposes Prometheus metrics at **`GET /metrics`** (port 8081), including `voragon_gpu_utilization`, `voragon_gpu_memory_used_bytes`, and `voragon_asr_inference_duration_seconds`. Requires `nvidia-ml-py` in the ASR image (see [docker/asr-inference/Dockerfile](../../../docker/asr-inference/Dockerfile)).

```bash
kubectl port-forward -n voragon svc/asr-service 8081:8081
curl -s http://localhost:8081/metrics | grep voragon_gpu
```

During active transcription, `voragon_gpu_utilization{gpu_index="0"}` should be non-zero on GPU nodes. See [observability.md](../../../docs/operations/observability.md).
