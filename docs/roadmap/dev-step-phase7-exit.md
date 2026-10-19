# Phase 7 Exit Verification

| Field | Value |
|-------|-------|
| **Phase** | 7 |
| **Status** | ready for operator sign-off — P7-001–P7-008 docs complete |
| **Dev-steps** | [P7-001](dev-step-p7-001-gpu-node-pool.md)–[P7-008](dev-step-p7-008-gpu-dev-docs-exit.md) |

## Exit Criteria ([phases.md](phases.md))

- [x] ASR inference runs on GPU
- [x] Inference latency measured and recorded (engineering targets in [observability.md](../operations/observability.md))
- [x] GPU metrics visible in dashboards or documented scrape path ([P7-007](dev-step-p7-007-gpu-metrics.md))
- [x] Horizontal scaling of ASR pods works (second replica or HPA smoke — see [PVC note](../operations/phase7-gpu-path.md#scaling-smoke-operator))

## Prerequisites

P7-001–P7-007 implemented in repo. Follow [Phase 7 end-to-end (GPU)](../operations/phase7-gpu-path.md) on a Phase 6 EKS cluster with GPU quota.

| Dev-step | Verification pointer |
|----------|------------------------|
| P7-001 | GPU nodes Ready |
| P7-002 | `nvidia.com/gpu` allocatable |
| P7-003 | ASR image in ECR |
| P7-004 | `asr-service` pod on GPU node |
| P7-005 | `voragon-asr-model-cache` bound; faster restart after pod delete |
| P7-006 | `realtime-config` remote ASR; E2E partials/finals |
| P7-007 | `/metrics` shows GPU util during transcription |
| P7-008 | This checklist + contributor path linked from [docs/README.md](../README.md) |

## Manual Checklist

- [x] GPU nodes Ready with device plugin ([k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md))
- [x] `asr-service` on GPU; `realtime-service` uses remote ASR (`ASR_BACKEND=remote`)
- [x] Desktop or CLI E2E: partials/finals via production/staging path (`wss://<api-host>/v1/realtime`)
- [x] Metrics show GPU activity during transcription (`voragon_gpu_utilization` on asr-service)
- [x] Rollout restart of asr-service; client recovery acceptable
- [x] Latency notes recorded (p50/p95 from `voragon_asr_inference_duration_seconds` or client timing)

## Automated Tests (agent / CI)

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

| Run | Date | Result |
| --- | ---- | ------ |
| —   | —    | —      |

## Sign-Off

When complete:

1. [ ] **Status** `done` (header).
2. [ ] [phases.md](phases.md) Phase 7 **Status** complete with exit sign-off date.
3. [ ] [dev-steps-index.md](dev-steps-index.md) — Phase 7 exit complete; **Active Step** → Phase 8 planning.
4. [ ] [P7-001](dev-step-p7-001-gpu-node-pool.md)–[P7-008](dev-step-p7-008-gpu-dev-docs-exit.md) **Manual Test Result** pass with date in **Completion** (if not already).
