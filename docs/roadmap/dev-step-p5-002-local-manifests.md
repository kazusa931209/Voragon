# P5-002: Local Kubernetes Manifests

| Field | Value |
|-------|-------|
| **ID** | P5-002 |
| **Phase** | 5 |
| **Status** | done |
| **Commit** | [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e) |
| **PR** | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) |
| **Branch** | `dev-step/p5-002-local-manifests` |

## Spec References

- [kubernetes-local.md](../operations/kubernetes-local.md)
- [Kubernetes Architecture](../architecture/kubernetes.md)
- [dev-step-p5-001](dev-step-p5-001-kind-cluster.md)

## Scope

One verifiable behavior: **`kubectl apply -f k8s/local/` deploys realtime-backend in namespace `voragon`; Pod reaches Ready and Service `realtime-service` exists.**

- `namespace.yaml`, `configmap.yaml`, `realtime-deployment.yaml`, `realtime-service.yaml` under `k8s/local/`
- Single Deployment, 1 replica, in-process ASR (same image as Compose)
- Basic env from ConfigMap (`ASR_MODEL=tiny`, cache paths) — PVC mount in P5-003

## Out of Scope

- PersistentVolumeClaim (P5-003)
- Full probe tuning / rolling restart (P5-004)
- Multi-replica or HPA

## Acceptance Criteria

- [x] Manifests under `k8s/local/` for namespace, configmap, deployment, service
- [x] After P5-001 image load, `kubectl apply -f k8s/local/` succeeds (operator)
- [x] Pod **Ready** after ASR warmup (operator)
- [x] Service `realtime-service` ClusterIP :8000 defined in manifests

## Manual Test

1. Complete P5-001 cluster + image load
2. `kubectl apply -f k8s/local/`
3. `kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=300s`
4. `kubectl port-forward -n voragon svc/realtime-service 8000:8000` → `curl -f http://localhost:8000/health`

## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Spec Changes

Expected: [kubernetes-local.md](../operations/kubernetes-local.md) manifest list (single-pod MVP).

---

## Completion

### Summary

- Added [`k8s/local/namespace.yaml`](../../k8s/local/namespace.yaml), [`configmap.yaml`](../../k8s/local/configmap.yaml), [`realtime-deployment.yaml`](../../k8s/local/realtime-deployment.yaml), [`realtime-service.yaml`](../../k8s/local/realtime-service.yaml).

### Spec Changes

- [kubernetes-local.md](../operations/kubernetes-local.md) — manifest tree updated.

### Automated Tests Run

```bash
cd backend && pytest -q   # 93 passed, 1 skipped (2026-10-15)
cd desktop && pnpm test  # 14 passed (2026-10-15)
```

### Manual Test Result

- [x] Pass — 2026-10-15 (apply, Ready pod, `/health` via port-forward)

### Commit

- **Hash:** [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e)
