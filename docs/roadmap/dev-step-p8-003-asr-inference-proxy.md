# P8-003: AI Gateway ASR Inference Proxy

| Field | Value |
|-------|-------|
| **ID** | P8-003 |
| **Phase** | 8 |
| **Status** | done |
| **Commit** | `bd4d9d2` |
| **PR** | — |
| **Branch** | `dev-step/p8-003-asr-inference-proxy` |

## Spec References

- [AI Gateway](../architecture/ai-gateway.md) — `POST /v1/inference/asr`, inference flow
- [dev-step-p8-002](dev-step-p8-002-model-registry.md)
- [P7-006 ASR HTTP API](../roadmap/dev-step-p7-006-realtime-remote-asr.md) — upstream `kind` + `audio_base64`

## Scope

One verifiable behavior: **`POST /v1/inference/asr` resolves `capability` via the registry and forwards to the model endpoint (asr-service contract); response includes resolved `model` and `latency_ms`.**

- Gateway request: `capability`, `audio` (base64 PCM), `language`, `segment_id`, `is_final`
- Upstream: existing `AsrInferenceRequest` (`kind`, `audio_base64`, …)
- Shared `httpx.AsyncClient` on app lifespan
- Map upstream 502/503 to gateway HTTP errors

## Out of Scope

- Active backend health gating (P8-004)
- Fallback routing (P8-005)
- realtime-service env switch (P8-006)

## Acceptance Criteria

- [x] pytest covers proxy success, unknown capability, upstream 503
- [x] Default registry routes `asr.default` to mock upstream in tests
- [x] Response includes `model`, `segment_id`, `is_final`, `latency_ms`

## Manual Test

1. Run mock or real `asr-service` on 8081; run ai-gateway on 8080
2. `curl -X POST http://localhost:8080/v1/inference/asr` with JSON body per [ai-gateway.md](../architecture/ai-gateway.md)

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_asr_proxy.py
```

## Spec Changes

Expected: none

---

## Completion

### Summary

- `POST /v1/inference/asr` resolves capabilities and proxies to asr-service HTTP API; maps `audio` → `audio_base64`, `is_final` → `kind`.
- Shared upstream `httpx.AsyncClient` on gateway lifespan (`AI_GATEWAY_UPSTREAM_TIMEOUT_S`).

### Spec Changes

- none

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_asr_proxy.py
```

### Manual Test Result

- [ ] Pass — pending operator curl against real asr-service

### Commit

- **Hash:** —
- **Message:** —
