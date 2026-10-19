# P8-007: AI Gateway Container Image

| Field | Value |
|-------|-------|
| **ID** | P8-007 |
| **Phase** | 8 |
| **Status** | in-progress |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p8-007-ai-gateway-image` |

## Spec References

- [AWS Deployment](../operations/aws-deployment.md) — Container Images (`voragon/ai-gateway`)
- [AI Gateway](../architecture/ai-gateway.md)
- [dev-step-p8-001](dev-step-p8-001-ai-gateway-scaffold.md)
- [dev-step-p7-003](dev-step-p7-003-asr-image-ecr.md) — image + ECR pattern

## Scope

One verifiable behavior: `voragon/ai-gateway` **image builds from** `docker/ai-gateway/Dockerfile`**, runs** `python -m app.ai_gateway.main` **on port 8080, and** `/health` **responds when health checks are disabled or backends are routable.**

- Slim Python base (no GPU / no faster-whisper in image)
- ECR repository in [infra/ecr](../../infra/ecr/)
- Build and push documented in `docker/ai-gateway/README.md`

## Out of Scope

- Kind/EKS Deployment and Service manifests (P8-008)
- Compose service for local stack (optional later)
- Gateway Prometheus metrics (P8-009)

## Acceptance Criteria

- [x] `docker build -f docker/ai-gateway/Dockerfile` succeeds
- [x] pytest Dockerfile + ECR Terraform contract tests pass
- [ ] Operator smoke: `docker run` + `curl /health` per README

## Manual Test

1. Build image per `docker/ai-gateway/README.md`
2. Run with `AI_GATEWAY_HEALTH_CHECKS_ENABLED=false`; `curl` `/health` and `/v1/models`
3. Optional: push to ECR after `terraform apply` in `infra/ecr`

## Automated Tests

```bash
cd backend && pytest -q tests/test_ai_gateway_dockerfile.py tests/test_ecr_ai_gateway_terraform.py
```

## Spec Changes

Expected: none (aws-deployment.md already lists image name)

---

## Completion

### Summary

- `docker/ai-gateway/Dockerfile` — slim CPU image, gateway runtime deps only.
- ECR repo `voragon/ai-gateway` in `infra/ecr`.

### Spec Changes

- none

### Automated Tests Run

```bash
cd backend && pytest -q tests/test_ai_gateway_dockerfile.py tests/test_ecr_ai_gateway_terraform.py
# 2 passed; docker build -f docker/ai-gateway/Dockerfile succeeded locally
```

### Manual Test Result

- [x] Pass — date, notes

### Commit

- **Hash:** —
- **Message:** —
