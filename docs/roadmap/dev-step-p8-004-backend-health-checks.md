# P8-004: AI Gateway Backend Health Checks

| Field | Value |
|-------|-------|
| **ID** | P8-004 |
| **Phase** | 8 |
| **Status** | in-progress |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p8-004-backend-health-checks` |

## Spec References

- [AI Gateway](../architecture/ai-gateway.md) — Health Checking, `GET /v1/models`, routing exclusion
- [dev-step-p8-003](dev-step-p8-003-asr-inference-proxy.md)

## Scope

One verifiable behavior: **AI Gateway periodically probes model backends (`GET /health`), tracks healthy/unhealthy state, reflects it on `GET /v1/models`, blocks inference when unhealthy, and degrades gateway `/health` when no model is routable.**

- Thresholds: 3 consecutive failures → unhealthy; 2 consecutive successes → healthy (cold start: 1 success if never failed)
- Configurable interval/timeout via env; background loop + probe on startup
- `AI_GATEWAY_HEALTH_CHECKS_ENABLED=false` disables probes (local tests)

## Out of Scope

- Fallback to alternate models (P8-005)
- K8s manifest probe split (P8-008)

## Acceptance Criteria

- [x] Unit tests for health state thresholds
- [x] Integration test: mock asr-service → `GET /v1/models` shows `healthy`
- [x] Integration test: unhealthy backend → `POST /v1/inference/asr` returns 503 before upstream POST
- [x] Gateway `/health` returns 503 when all models unhealthy (readiness-style)

## Manual Test

1. Run ai-gateway + asr-service; `curl /v1/models` shows `healthy`
2. Stop asr-service; after ~90s (3×30s) model marked unhealthy; inference 503

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_health_checks.py tests/test_ai_gateway_asr_proxy.py tests/test_ai_gateway_registry.py
```

## Spec Changes

Expected: none

---

## Completion

### Summary

- Background probes to each ASR backend `GET /health`; state on `GET /v1/models`; inference gated when unhealthy.
- Env: `AI_GATEWAY_HEALTH_CHECKS_*` (disable with `AI_GATEWAY_HEALTH_CHECKS_ENABLED=false` for tests).

### Spec Changes

- none

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_health_checks.py tests/test_ai_gateway_asr_proxy.py tests/test_ai_gateway_registry.py tests/test_ai_gateway_health.py
```

### Manual Test Result

- [ ] Pass — pending operator stop/start asr-service

### Commit

- **Hash:** —
- **Message:** —
