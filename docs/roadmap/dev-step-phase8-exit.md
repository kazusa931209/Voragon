# Phase 8 Exit Verification

| Field | Value |
|-------|-------|
| **Phase** | 8 |
| **Status** | ready for operator sign-off — P8-001–P8-010 docs complete |
| **Dev-steps** | [P8-001](dev-step-p8-001-ai-gateway-scaffold.md)–[P8-010](dev-step-p8-010-ops-docs-phase8-exit.md) |

## Exit Criteria ([phases.md](phases.md))

- [ ] realtime-service calls AI Gateway, not ASR directly (EKS `realtime-config`)
- [ ] Model can be changed via ConfigMap registry without code changes
- [ ] Unhealthy primary model triggers fallback or clear error (gateway health + routing)

## Prerequisites

Phase 7 GPU path complete. Follow [Phase 8 end-to-end (AI Gateway)](../operations/phase8-ai-gateway-path.md).

| Dev-step | Verification pointer |
|----------|------------------------|
| P8-001–P8-005 | Gateway HTTP API + fallback (pytest + local smoke) |
| P8-006 | `ASR_REMOTE_VIA_AI_GATEWAY` on realtime |
| P8-007–P8-008 | ai-gateway image in ECR; pods Ready on EKS |
| P8-009 | `/metrics` on ai-gateway |
| P8-010 | This checklist + contributor path linked from [docs/README.md](../README.md) |

## Manual Checklist

- [ ] `kubectl get pods -n voragon` — `realtime-backend`, `ai-gateway`, `asr-service` Ready
- [ ] From realtime pod: `curl -sf http://ai-gateway:8080/health` and `/v1/models`
- [ ] Desktop or CLI E2E: partials/finals via `wss://<api-host>/v1/realtime`
- [ ] `curl` ai-gateway `/metrics` shows `voragon_gateway_inference_requests_total` during transcription
- [ ] Edit `ai-gateway-config` registry (or routing fallback); rollout; behavior changes without realtime image rebuild
- [ ] Optional: primary ASR unavailable → fallback or 503 with clear client behavior

## Automated Tests (agent / CI)

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Sign-off

When complete: update this checklist, [dev-steps-index.md](dev-steps-index.md), and [phases.md](phases.md) Phase 8 status.
