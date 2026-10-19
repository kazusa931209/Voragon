# P7-007: GPU Utilization Metrics

| Field | Value |
|-------|-------|
| **ID** | P7-007 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-007-gpu-metrics` |

## Spec References

- [Observability](../operations/observability.md)
- [dev-step-p2-008](dev-step-p2-008-prometheus-metrics.md)
- [dev-step-p7-004](dev-step-p7-004-asr-service-deploy.md)

## Scope

One verifiable behavior: **GPU utilization (and ASR inference latency signals) are scrapeable via Prometheus text exposition or documented CloudWatch/DCGM path.**

- Documented metric names for GPU util and inference duration (backend or sidecar)
- EKS: ServiceMonitor or `/metrics` on asr-service if in-process
- Minimum: operator can confirm non-zero GPU metric during active transcription

## Out of Scope

- Full Grafana dashboards
- HPA on GPU metrics (optional doc note only)

## Acceptance Criteria

- [x] Metrics documented in observability.md
- [x] `curl`/Prometheus scrape shows GPU-related series during load (operator)
- [x] pytest for any new metric registration in backend/asr service

## Manual Test

1. Run transcription session on GPU path
2. Scrape metrics endpoint or CloudWatch agent path per docs
3. Confirm utilization or inference histogram updates

## Automated Tests

```bash
cd backend && pytest -q
```

## Spec Changes

Expected: [observability.md](../operations/observability.md).

---

## Completion

### Summary

- `GET /metrics` on `asr-service` — GPU util/memory (NVML), inference duration, errors, queue depth, model load time.
- `app/observability/gpu_collector.py`, inference route instrumentation, Prometheus scrape annotations on EKS Service.

### Spec Changes

- [observability.md](../operations/observability.md), [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md), [docker/asr-inference/Dockerfile](../../docker/asr-inference/Dockerfile).

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_asr_service_metrics.py
# 3 passed
cd backend && pytest -q
# full suite green at sign-off
```

### Manual Test Result

- [x] Pass — 2026-10-16; non-zero `voragon_gpu_utilization` during GPU transcription scrape

### Commit

- **Hash:** `4713b3b`

### PR

- **URL:** —
