# P7-005: Model Weights on GPU Pods

| Field | Value |
|-------|-------|
| **ID** | P7-005 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-005-model-weights-gpu` |

## Spec References

- [Model Serving](../architecture/model-serving.md)
- [dev-step-p6-003](dev-step-p6-003-eks-realtime-manifests.md) — model cache PVC pattern
- [dev-step-p7-004](dev-step-p7-004-asr-service-deploy.md)

## Scope

One verifiable behavior: **ASR model weights persist across asr-service pod restarts without re-downloading on every schedule event.**

- PVC or documented init-container download to shared volume (reuse `gp2` / model-cache pattern where applicable)
- Config for model id/path documented for operators

## Out of Scope

- Multi-model registry (Phase 8)
- Changing Whisper model family (unless required for GPU path)

## Acceptance Criteria

- [x] First pod start downloads or mounts weights; readiness becomes true
- [x] Delete pod → replacement Ready faster (cached weights) (operator)
- [x] Document disk size and cache path in k8s README

## Manual Test

1. Deploy asr-service with empty PVC → wait Ready
2. `kubectl delete pod` for asr-service → new pod Ready with shorter startup
3. Verify PVC bound and used

## Automated Tests

```bash
cd backend && pytest -q
```

## Spec Changes

Expected: [k8s/eks/README.md](../../k8s/eks/README.md), [aws-deployment.md](../operations/aws-deployment.md) Configuration Management.

---

## Completion

### Summary

- `k8s/eks/asr-pvc.yaml` — `voragon-asr-model-cache` (10Gi `gp2`, ReadWriteOnce).
- `asr-deployment.yaml` — mount `/var/lib/voragon/model-cache`; `asr-config` sets `HF_HOME` / `TORCH_HOME` and `ASR_MODEL`.

### Spec Changes

- [k8s/eks/README.md](../../k8s/eks/README.md), [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md), [aws-deployment.md](../operations/aws-deployment.md).

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_eks_asr_manifests.py
# 5 passed
cd backend && pytest -q
# 109 passed, 1 skipped
```

### Manual Test Result

- [x] Pass — 2026-10-16; PVC bound, faster restart after pod delete

### Commit

- **Hash:** `26fba6d`

### PR

- **URL:** —
