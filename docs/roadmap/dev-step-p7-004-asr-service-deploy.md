# P7-004: asr-service Deployment on GPU

| Field | Value |
|-------|-------|
| **ID** | P7-004 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-004-asr-service-deploy` |

## Spec References

- [Kubernetes Architecture](../architecture/kubernetes.md) — asr-service
- [dev-step-p7-003](dev-step-p7-003-asr-image-ecr.md)
- [k8s/eks](../../k8s/eks/)

## Scope

One verifiable behavior: **`asr-service` runs on GPU nodes with `nvidia.com/gpu: 1`, ClusterIP Service, readiness when model ready.**

- Manifests under `k8s/eks/` (Kustomize overlay or new base)
- nodeSelector `node-type=gpu`, toleration for GPU taint, resource limits per ADR-010
- Probes aligned with [kubernetes.md](../architecture/kubernetes.md) ASR probe table

## Out of Scope

- Model cache strategy details (P7-005)
- realtime-service routing (P7-006)

## Acceptance Criteria

- [x] `kubectl apply -k` deploys asr-service to GPU nodes only
- [x] `kubectl get pods -n voragon -l app=asr-service` Ready (operator)
- [x] In-cluster `curl` to Service `/health` succeeds from debug pod

## Manual Test

1. Set ECR image tag in Kustomize
2. Apply and wait for Ready
3. Port-forward or exec curl `/health`

## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Spec Changes

Expected: [k8s/eks/README.md](../../k8s/eks/README.md), [kubernetes-local.md](../operations/kubernetes-local.md) note (EKS-only GPU).

---

## Completion

### Summary

- `k8s/eks/asr-{configmap,deployment,service}.yaml` — GPU scheduling, `nvidia.com/gpu: 1`, ClusterIP `:8081`, probes per [kubernetes.md](../architecture/kubernetes.md).
- `k8s/eks/kustomization.yaml` — includes ASR resources and `voragon/asr-inference` image transform.
- `app/asr_inference/main.py` — `/health` returns HTTP 503 until ASR model is ready (readiness probe).

### Spec Changes

- [k8s/eks/README.md](../../k8s/eks/README.md), [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md), [kubernetes-local.md](../operations/kubernetes-local.md), [aws-deployment.md](../operations/aws-deployment.md).

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_eks_asr_manifests.py tests/test_asr_inference_service.py
# 5 passed
cd backend && pytest -q
# 107 passed, 1 skipped
cd desktop && pnpm test
# 16 passed
```

### Manual Test Result

- [x] Pass — 2026-10-16; GPU scheduling, Ready pod, in-cluster `/health`

### Commit

- **Hash:** `b9440c8`

### PR

- **URL:** —
