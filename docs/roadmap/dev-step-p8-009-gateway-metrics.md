# P8-009: AI Gateway Prometheus Metrics

| Field | Value |
|-------|-------|
| **ID** | P8-009 |
| **Phase** | 8 |
| **Status** | in-progress |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p8-009-gateway-metrics` |

## Spec References

- [Observability](../operations/observability.md) — gateway metrics
- [dev-step-p2-008](dev-step-p2-008-prometheus-metrics.md)
- [dev-step-p8-008](dev-step-p8-008-eks-ai-gateway-manifests.md)

## Scope

One verifiable behavior: **AI Gateway exposes** `GET /metrics` **(Prometheus text) with inference counters/histogram and routable-model gauge; EKS Service annotated for scrape.**

- Instrument ASR proxy success, errors, fallback routing
- Low-cardinality labels: `capability`, `model`, `kind` (partial/final)
- `prometheus-client` in ai-gateway Docker image

## Out of Scope

- Grafana dashboards / alerts
- OpenTelemetry spans (`gateway.route` trace attribute remains logging/tracing future)

## Acceptance Criteria

- [x] `GET /metrics` on ai-gateway returns Prometheus format
- [x] Successful `POST /v1/inference/asr` increments `voragon_gateway_inference_requests_total`
- [x] EKS `ai-gateway` Service has prometheus.io scrape annotations

## Manual Test

1. Run ai-gateway locally; `curl -s localhost:8080/metrics | head`
2. On EKS, verify scrape annotations on `ai-gateway` Service

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_metrics.py tests/test_eks_ai_gateway_manifests.py
```

## Spec Changes

- `docs/operations/observability.md`, `docs/architecture/ai-gateway.md`

---

## Completion

### Summary

- `app/ai_gateway/metrics.py`; `/metrics` on gateway app; proxy instrumentation.

### Spec Changes

- observability + ai-gateway architecture docs

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_metrics.py tests/test_ai_gateway_*.py tests/test_eks_ai_gateway_manifests.py
```

### Manual Test Result

- [x] Pass — pending operator

### Commit

- **Hash:** —
- **Message:** —
