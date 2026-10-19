# P5-004: Health Probes and Rolling Restart

| Field | Value |
|-------|-------|
| **ID** | P5-004 |
| **Phase** | 5 |
| **Status** | done |
| **Commit** | [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e) |
| **PR** | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) |
| **Branch** | `dev-step/p5-004-probes-rolling-restart` |

## Spec References

- [Kubernetes Architecture](../architecture/kubernetes.md) — Health Probes
- [backend/app/main.py](../../backend/app/main.py) — `GET /health`
- [dev-step-p5-002](dev-step-p5-002-local-manifests.md)

## Scope

One verifiable behavior: **Deployment uses HTTP liveness/readiness/startup probes on `/health`; `kubectl rollout restart` replaces the pod without manual delete and the new pod becomes Ready.**

- `startupProbe` tolerant of ASR warmup (~2 min, aligned with Compose `start_period: 120s`)
- `livenessProbe` interval 30s; `readinessProbe` interval 10s
- `RollingUpdate` with `maxUnavailable: 0`, `maxSurge: 1` (1 replica)
- Document WebSocket / single-replica drain limitations

## Out of Scope

- `preStop` graceful drain beyond default termination grace
- Multi-replica sticky sessions

## Acceptance Criteria

- [x] startup/liveness/readiness HTTP probes on `/health` in Deployment
- [x] RollingUpdate strategy `maxUnavailable: 0`, `maxSurge: 1`
- [x] Rollout / WebSocket limitations documented in `k8s/README.md`
- [x] `kubectl rollout restart` verified on live cluster (operator)

## Manual Test

1. Deploy stack (P5-001–P5-003)
2. `kubectl rollout restart deployment/realtime-backend -n voragon`
3. `kubectl rollout status deployment/realtime-backend -n voragon`
4. Port-forward → `curl -f http://localhost:8000/health`

## Automated Tests

```bash
cd backend && pytest -q
```

## Spec Changes

Expected: none (probe paths already in architecture doc).

---

## Completion

### Summary

- Probes and rollout strategy in [`realtime-deployment.yaml`](../../k8s/local/realtime-deployment.yaml) (`startupProbe` failureThreshold 30 × 10s).
- Rollout notes in [`k8s/README.md`](../../k8s/README.md).

### Spec Changes

- None

### Automated Tests Run

```bash
cd backend && pytest -q
# 93 passed, 1 skipped (2026-10-15)
```

### Manual Test Result

- [x] Pass — 2026-10-15 (`rollout restart`, health OK after port-forward)

### Commit

- **Hash:** [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e)
