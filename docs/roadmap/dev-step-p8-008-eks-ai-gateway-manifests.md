# P8-008: EKS AI Gateway Manifests

| Field | Value |
|-------|-------|
| **ID** | P8-008 |
| **Phase** | 8 |
| **Status** | done |
| **Commit** | `d9e73503` |
| **PR** | — |
| **Branch** | `dev-step/p8-008-eks-ai-gateway-manifests` |

## Spec References

- [Kubernetes Architecture](../architecture/kubernetes.md) — `ai-gateway` Service :8080, `ai-gateway-config`
- [AI Gateway](../architecture/ai-gateway.md)
- [dev-step-p8-007](dev-step-p8-007-ai-gateway-image.md)
- [dev-step-p8-006](dev-step-p8-006-realtime-routes-via-gateway.md)

## Scope

One verifiable behavior: `kubectl apply -k k8s/eks` **deploys** `ai-gateway` **(Deployment + ClusterIP Service on 8080) with model registry ConfigMap; realtime can reach** `http://ai-gateway:8080`**.**

- `ai-gateway-config` ConfigMap mounts registry YAML (`asr.default` → `asr-service:8081`)
- Probes on `GET /health`
- Kustomize image `voragon/ai-gateway:ecr`
- Kind/local (`k8s/local/`) unchanged — in-process ASR only

## Out of Scope

- HPA / 2+ replicas (future)
- Gateway `/metrics` (P8-009)
- Phase 8 exit doc (P8-010)

## Acceptance Criteria

- [x] pytest contract tests for EKS ai-gateway manifests
- [x] `kustomization.yaml` includes gateway resources + image stanza
- [x] Operator: apply on EKS; `curl` from realtime pod to `http://ai-gateway:8080/health`

## Manual Test

1. Push `voragon/ai-gateway` image; `kustomize edit set image` per [k8s/eks/README.md](../../k8s/eks/README.md)
2. `kubectl apply -k k8s/eks`; wait for `app=ai-gateway` Ready
3. `kubectl exec -n voragon deploy/realtime-backend -- curl -sf http://ai-gateway:8080/v1/models`

## Automated Tests

```bash
cd backend && pytest -q tests/test_eks_ai_gateway_manifests.py tests/test_eks_remote_realtime_config.py
```

## Spec Changes

Expected: [k8s/eks/README.md](../../k8s/eks/README.md)

---

## Completion

### Summary

- EKS Deployment/Service/ConfigMap for `ai-gateway`; registry points at in-cluster `asr-service`.

### Spec Changes

- `k8s/eks/README.md`

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_eks_ai_gateway_manifests.py tests/test_eks_remote_realtime_config.py
```

### Manual Test Result

- [x] Pass — 2026-10-19; EKS apply + curl from realtime pod

### Commit

- **Hash:** `d9e73503`
- **Message:** [P8-008] EKS AI Gateway manifests
