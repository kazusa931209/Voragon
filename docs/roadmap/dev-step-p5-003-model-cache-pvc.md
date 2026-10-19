# P5-003: Model Cache PVC on Kind

| Field | Value |
|-------|-------|
| **ID** | P5-003 |
| **Phase** | 5 |
| **Status** | done |
| **Commit** | [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e) |
| **PR** | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) |
| **Branch** | `dev-step/p5-003-model-cache-pvc` |

## Spec References

- [dev-step-p4-003](dev-step-p4-003-model-cache-volumes.md)
- [docker/docker-compose.yml](../../docker/docker-compose.yml)
- [kubernetes-local.md](../operations/kubernetes-local.md)

## Scope

One verifiable behavior: **ASR/VAD model caches on a PVC survive pod deletion and speed up the next pod startup.**

- `PersistentVolumeClaim` `voragon-model-cache` in namespace `voragon`
- Deployment `volumeMount` at `/var/lib/voragon/model-cache`
- ConfigMap `HF_HOME` / `TORCH_HOME` under that mount (parity with Compose)

## Out of Scope

- Pre-baking models in the image
- Shared ReadWriteMany storage

## Acceptance Criteria

- [x] PVC manifest `voragon-model-cache` (10Gi RWO)
- [x] Deployment mounts `/var/lib/voragon/model-cache`
- [x] ConfigMap paths match Compose
- [x] Pod delete → faster second startup (operator)

## Manual Test

1. Fresh PVC: apply manifests, wait Ready, note warmup time in logs
2. Delete pod, wait for new Ready pod; confirm faster startup
3. `kubectl get pvc -n voragon voragon-model-cache`

## Automated Tests

```bash
cd backend && pytest -q
```

## Spec Changes

Expected: [kubernetes-local.md](../operations/kubernetes-local.md) storage note.

---

## Completion

### Summary

- Added [`k8s/local/pvc.yaml`](../../k8s/local/pvc.yaml).
- Wired volume in [`realtime-deployment.yaml`](../../k8s/local/realtime-deployment.yaml).
- Documented PVC behavior in [`k8s/README.md`](../../k8s/README.md).

### Spec Changes

- [kubernetes-local.md](../operations/kubernetes-local.md) — architecture includes PVC.

### Automated Tests Run

```bash
cd backend && pytest -q
# 93 passed, 1 skipped (2026-10-15)
```

### Manual Test Result

- [x] Pass — 2026-10-15 (PVC bound; pod delete → faster warmup)

### Commit

- **Hash:** [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e)
