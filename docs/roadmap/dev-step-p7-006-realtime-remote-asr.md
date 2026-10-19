# P7-006: Realtime Backend Remote ASR

| Field | Value |
|-------|-------|
| **ID** | P7-006 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-006-realtime-remote-asr` |

## Spec References

- [Backend Architecture](../architecture/backend.md)
- [Model Serving](../architecture/model-serving.md) — ASREngine abstraction
- [dev-step-p7-004](dev-step-p7-004-asr-service-deploy.md)
- [Realtime WebSocket](../api/realtime-websocket.md)

## Scope

One verifiable behavior: **realtime-service transcribes via HTTP (or gRPC) to in-cluster `asr-service` when `ASR_BACKEND=remote` (or documented env); WebSocket partial/final behavior unchanged for clients.**

- Remote ASR adapter implementing existing engine interface
- asr-service transcribe API (minimal: partial + final segments, health)
- EKS ConfigMap/env for service URL; CPU realtime Deployment updated
- Local dev: optional mock remote URL for pytest

## Out of Scope

- AI Gateway routing (Phase 8)
- Desktop changes (same WebSocket contract)

## Acceptance Criteria

- [x] pytest covers remote adapter (mock server or contract tests)
- [x] EKS: realtime pods call asr-service; desktop E2E partials/finals on GPU path (operator)
- [x] `ASR_BACKEND` in-process still works for Compose/Kind (regression)

## Manual Test

1. Deploy P7-004 + P7-006 manifests
2. Desktop or `realtime_cli` against ALB — transcripts flow
3. Scale asr-service to 0 → degraded health / clear errors per API spec

## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Spec Changes

Expected: [backend.md](../architecture/backend.md), [realtime-websocket.md](../api/realtime-websocket.md) if error codes added, [k8s/eks](../../k8s/eks/).

---

## Completion

### Summary

- `app/asr/remote.py` — `RemoteASREngine` (`ASR_BACKEND=remote`) calling `POST /v1/inference/asr`.
- `app/asr/inference_routes.py` on `asr-service` — partial/final transcription over HTTP.
- `k8s/eks/configmap.yaml` — `ASR_BACKEND=remote`, `ASR_REMOTE_BASE_URL=http://asr-service:8081`.

### Spec Changes

- [backend.md](../architecture/backend.md), [k8s/eks/README.md](../../k8s/eks/README.md), [backend/.env.example](../../backend/.env.example).

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_remote_asr.py tests/test_eks_remote_realtime_config.py
# 6 passed
cd backend && pytest -q
# 115 passed, 1 skipped
```

### Manual Test Result

- [x] Pass — 2026-10-16; remote ASR E2E, degraded when asr-service scaled to 0

### Commit

- **Hash:** `ee43b41`

### PR

- **URL:** —
