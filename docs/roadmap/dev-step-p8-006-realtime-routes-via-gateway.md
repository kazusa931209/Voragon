# P8-006: Realtime Routes via AI Gateway

| Field | Value |
|-------|-------|
| **ID** | P8-006 |
| **Phase** | 8 |
| **Status** | in-progress |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p8-006-realtime-routes-via-gateway` |

## Spec References

- [AI Gateway](../architecture/ai-gateway.md) — `POST /v1/inference/asr`, capability aliases
- [Backend](../architecture/backend.md) — `ASR_BACKEND`, `ASR_REMOTE_BASE_URL`, `AI_GATEWAY_URL`
- [dev-step-p7-006](dev-step-p7-006-realtime-remote-asr.md) — remote ASR adapter
- [dev-step-p8-005](dev-step-p8-005-fallback-routing.md)

## Scope

One verifiable behavior: **when configured for production/EKS, realtime-service transcribes via the AI Gateway (`POST /v1/inference/asr` with `capability`), not direct asr-service HTTP; WebSocket partial/final behavior unchanged for clients.**

- Env/config to select gateway base URL (e.g. `http://ai-gateway:8080`) and default capability (`asr.default`)
- Remote adapter (or dedicated path) uses gateway request/response shape; health/warmup aligned with gateway `/health` or documented probe
- EKS `realtime-config` updated: remote URL points at ai-gateway Service, not asr-service
- Compose/Kind local paths may stay direct ASR until P8-008 (document which envs switch)

## Out of Scope

- AI Gateway container image (P8-007)
- Kind/EKS ai-gateway Deployment manifests (P8-008)
- Gateway Prometheus metrics (P8-009)
- Desktop or WebSocket protocol changes

## Acceptance Criteria

- [x] pytest covers gateway-backed remote ASR (mock gateway or contract test)
- [x] EKS config documents `ASR_REMOTE_BASE_URL` → ai-gateway; test asserts manifest/env
- [ ] Operator E2E: realtime partials/finals with gateway in path (health + fallback inherited from gateway)

## Manual Test

1. Run ai-gateway + asr-service; point realtime `ASR_REMOTE_BASE_URL` at gateway
2. Desktop or realtime-cli: partials/finals unchanged; backend logs show gateway URL
3. Stop primary ASR backend (with fallback configured on gateway) — transcription still succeeds

## Automated Tests

```bash
cd backend && pytest -q tests/test_remote_asr.py tests/test_eks_remote_realtime_config.py
# extend or add tests for gateway URL / capability payload
```

## Spec Changes

Expected: `docs/architecture/backend.md`, EKS config docs if env names change

---

## Completion

### Summary

- `ASR_REMOTE_VIA_AI_GATEWAY` + `ASR_CAPABILITY` on `RemoteASREngine`; gateway `/health` and inference payload shape.
- EKS `realtime-config`: `ASR_REMOTE_BASE_URL=http://ai-gateway:8080`.

### Spec Changes

- `docs/architecture/backend.md` — remote via gateway env vars
- `k8s/eks/README.md`, `k8s/eks/configmap.yaml`

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_remote_asr.py tests/test_eks_remote_realtime_config.py
```

### Manual Test Result

- [ ] Pass — pending operator E2E with ai-gateway + asr-service

### Commit

- **Hash:** —
- **Message:** —
