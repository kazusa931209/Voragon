# P7-003: ASR Inference Image and ECR

| Field | Value |
|-------|-------|
| **ID** | P7-003 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-003-asr-image-ecr` |

## Spec References

- [Model Serving](../architecture/model-serving.md)
- [dev-step-p6-001](dev-step-p6-001-ecr-image-push.md)
- [AWS Deployment](../operations/aws-deployment.md) — Container Images

## Scope

One verifiable behavior: **`voragon/asr-inference` image builds and pushes to ECR; image runs faster-whisper (or documented GPU backend) with `/health`.**

- Dockerfile under `docker/` (CUDA runtime base per aws-deployment.md)
- ECR repo Terraform (extend [infra/ecr](../../infra/ecr/) or documented second repo)
- Minimal HTTP health server or reuse pattern from backend ASR warmup

## Out of Scope

- Full transcribe HTTP API (P7-004 if split) — define in same step if one service image
- EKS Deployment (P7-004)

## Acceptance Criteria

- [x] `docker build` succeeds locally or in CI doc (Dockerfile + README)
- [x] Push to ECR documented; ECR repo in Terraform (operator push)
- [x] Container `/health` responds when model loaded (operator smoke)

## Manual Test

1. Build and push per README
2. Optional: `docker run --gpus all` smoke on GPU host

## Automated Tests

```bash
cd backend && pytest -q
# Add image build smoke test if step touches backend packaging
```

## Spec Changes

Expected: [infra/ecr/README.md](../../infra/ecr/README.md), [aws-deployment.md](../operations/aws-deployment.md).

---

## Completion

### Summary

- `app/asr_inference/main.py` — `/health` + ASR warmup (`voragon-asr-inference`, port 8081).
- [docker/asr-inference/Dockerfile](../../docker/asr-inference/Dockerfile) — CUDA runtime, `ASR_DEVICE=cuda`.
- [infra/ecr](../../infra/ecr/) — `voragon/asr-inference` repository + outputs.
- `ASR_DEVICE` / `ASR_COMPUTE_TYPE` settings for faster-whisper.

### Spec Changes

- [infra/ecr/README.md](../../infra/ecr/README.md), [docker/asr-inference/README.md](../../docker/asr-inference/README.md), [aws-deployment.md](../operations/aws-deployment.md).

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_asr_inference_service.py tests/test_ecr_asr_terraform.py
# 3 passed
cd backend && pytest -q
# 104 passed, 1 skipped
cd infra/ecr && terraform init -backend=false && terraform validate
# Success
```

### Manual Test Result

- [x] Pass — 2026-10-16; build, ECR push, `/health` with model ready (GPU smoke)

### Commit

- **Hash:** `9591163`

### PR

- **URL:** —
