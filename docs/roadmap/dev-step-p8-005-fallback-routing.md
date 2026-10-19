# P8-005: AI Gateway Fallback Routing

| Field | Value |
|-------|-------|
| **ID** | P8-005 |
| **Phase** | 8 |
| **Status** | in-progress |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p8-005-fallback-routing` |

## Spec References

- [AI Gateway](../architecture/ai-gateway.md) — Fallback policy
- [dev-step-p8-004](dev-step-p8-004-backend-health-checks.md)

## Scope

One verifiable behavior: **when the primary model for a capability is not routable, `POST /v1/inference/asr` tries configured fallback model(s); 503 only if all candidates fail.**

- Registry `routing` section: `primary` + ordered `fallback` model ids per capability
- Default registry unchanged (single model; auto routing from capabilities)
- Response `model` reflects the backend that served the request

## Out of Scope

- realtime-service env switch (P8-006)
- Cross-capability fallback (e.g. `asr.fast` for `asr.default`)

## Acceptance Criteria

- [x] pytest: primary unhealthy + fallback healthy → 200 via fallback model id
- [x] pytest: primary and fallback unhealthy → 503
- [x] Invalid routing references fail at registry load

## Manual Test

1. Registry with primary + fallback endpoints; stop primary pod — inference still succeeds via fallback

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_fallback.py
```

## Spec Changes

- [ai-gateway.md](../architecture/ai-gateway.md) — document `routing` block

---

## Completion

### Summary

- Registry `routing` block with ordered `fallback` model ids; proxy tries chain when primary not routable or returns 503.
- Auto-generated routing when YAML omits `routing` (primary-only).

### Spec Changes

- `docs/architecture/ai-gateway.md` — `routing` example

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_fallback.py tests/test_ai_gateway_*.py
```

### Manual Test Result

- [ ] Pass — pending operator

### Commit

- **Hash:** —
- **Message:** —
