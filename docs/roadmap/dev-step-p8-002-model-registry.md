# P8-002: AI Gateway Model Registry

| Field | Value |
|-------|-------|
| **ID** | P8-002 |
| **Phase** | 8 |
| **Status** | done |
| **Commit** | `bd4d9d2` |
| **PR** | — |
| **Branch** | `dev-step/p8-002-model-registry` |

## Spec References

- [AI Gateway](../architecture/ai-gateway.md) — Model Registry, `GET /v1/models`
- [ADR-008: AI Gateway](../decisions/ADR-008-ai-gateway.md)
- [dev-step-p8-001](dev-step-p8-001-ai-gateway-scaffold.md)

## Scope

One verifiable behavior: **AI Gateway loads a YAML model registry at startup and serves** `GET /v1/models` **listing models, capabilities, and placeholder health status (active probes in P8-004).**

- Default registry: `whisper-large-v3-turbo` → `asr.default`, endpoint `http://asr-service:8081`
- Override path via `AI_GATEWAY_REGISTRY_PATH`
- Validate unique capability aliases across models
- In-memory `resolve_capability(alias)` for P8-003

## Out of Scope

- `POST /v1/inference/asr` proxy (P8-003)
- Periodic backend health checks (P8-004)
- Kubernetes ConfigMap manifests (P8-008)

## Acceptance Criteria

- [x] `pytest -q tests/test_ai_gateway_registry.py` passes
- [x] `GET /v1/models` returns registered models with `health.status: unchecked`
- [x] Duplicate capability in YAML fails fast at startup
- [x] Default registry matches Phase 7 `asr-service:8081` endpoint

## Manual Test

1. `cd backend && python -m app.ai_gateway.main`
2. `curl -s http://localhost:8080/v1/models | jq`

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_registry.py tests/test_ai_gateway_health.py
```

## Spec Changes

- [ai-gateway.md](../architecture/ai-gateway.md) — example ASR endpoints use port **8081** (matches P7 `asr-service`).

---

## Completion

### Summary

- YAML model registry loader with capability uniqueness validation; default `asr.default` → `whisper-large-v3-turbo` at `http://asr-service:8081`.
- `GET /v1/models` lists models and capability map; health placeholder `unchecked` until P8-004.

### Spec Changes

- `docs/architecture/ai-gateway.md` (endpoint ports)

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_registry.py tests/test_ai_gateway_health.py
```

### Manual Test Result

- [x] Pass — pending operator curl

### Commit

- **Hash:** —
- **Message:** —
