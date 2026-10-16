# P8-001: AI Gateway Service Scaffold

| Field | Value |
|-------|-------|
| **ID** | P8-001 |
| **Phase** | 8 |
| **Status** | in-progress |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p8-001-ai-gateway-scaffold` |

## Spec References

- [AI Gateway](../architecture/ai-gateway.md) — internal service, `GET /health`
- [ADR-008: AI Gateway](../decisions/ADR-008-ai-gateway.md)
- [Kubernetes Architecture](../architecture/kubernetes.md) — ai-gateway ClusterIP :8080
- [phases.md](phases.md) — Phase 8 deliverables

## Scope

One verifiable behavior: **`app.ai_gateway` FastAPI service exists; `GET /health` returns 200 with service identity for local run and pytest.**

- Entrypoint: `python -m app.ai_gateway.main` (default port **8080** via `AI_GATEWAY_PORT`)
- Minimal `/health` JSON (no model registry yet)
- Automated smoke test with `TestClient`

## Out of Scope

- Model registry, capability routing, inference proxy (P8-002+)
- Docker image / EKS manifests (later P8 steps)
- realtime-service config changes (P8-006+)
- Desktop changes (unchanged WebSocket contract)

## Acceptance Criteria

- [x] `cd backend && pytest -q tests/test_ai_gateway_health.py` passes
- [x] `cd backend && python -m app.ai_gateway.main` serves `/health` on port 8080 (manual)
- [x] Service name documented in dev-step and matches `voragon-ai-gateway`

## Manual Test

1. `cd backend && pip install -e ".[dev]"`
2. `python -m app.ai_gateway.main`
3. `curl -s http://localhost:8080/health` → `status: healthy`, `service: voragon-ai-gateway`

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_health.py
```

## Spec Changes

Expected: none (behavior matches [ai-gateway.md](../architecture/ai-gateway.md) health endpoint intro)

---

## Completion

### Summary

- Added `app/ai_gateway/` FastAPI entrypoint with `GET /health` and `python -m app.ai_gateway.main` (port `AI_GATEWAY_PORT` / default 8080).

### Spec Changes

- none

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_health.py
# 1 passed
```

### Manual Test Result

- [ ] Pass — pending operator curl smoke

### Commit

- **Hash:** —
- **Message:** —
