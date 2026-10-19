# P6-008: AWS Dev Docs and Phase 6 Exit Prep

| Field | Value |
|-------|-------|
| **ID** | P6-008 |
| **Phase** | 6 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p6-008-aws-dev-docs-exit` |

## Spec References

- [phases.md](phases.md) — Phase 6 exit criteria
- [local-development.md](../operations/local-development.md)
- [aws-deployment.md](../operations/aws-deployment.md)
- [desktop/README.md](../../desktop/README.md)
- [dev-step-phase6-exit.md](dev-step-phase6-exit.md)

## Scope

One verifiable behavior: **documentation describes the full AWS staging/prod loop; [dev-step-phase6-exit.md](dev-step-phase6-exit.md) checklist is complete and cross-linked from index and ops docs.**

- Contributor path: ECR → EKS → deploy → ALB → API Gateway → desktop E2E
- Kind vs EKS vs Compose comparison updated
- [phases.md](phases.md) Phase 6 status when signed off
- [architecture/kubernetes.md](../architecture/kubernetes.md) — note Phase 6 CPU-only realtime on EKS (GPU in Phase 7)

## Out of Scope

- Phase 7 GPU dev-steps
- Cost automation / FinOps tooling

## Acceptance Criteria

- [x] [aws-deployment.md](../operations/aws-deployment.md) status reflects implemented Phase 6 path
- [x] [dev-step-phase6-exit.md](dev-step-phase6-exit.md) manual checklist ready for operator sign-off
- [x] [dev-steps-index.md](dev-steps-index.md) and [local-development.md](../operations/local-development.md) link EKS path
- [x] Desktop production connect documented (URL + auth)

## Manual Test

1. Follow aws-deployment contributor path from clean clone (AWS creds assumed)
2. Complete [dev-step-phase6-exit.md](dev-step-phase6-exit.md) checklist
3. Confirm docs README / roadmap links resolve

## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Spec Changes

Expected: [aws-deployment.md](../operations/aws-deployment.md), [local-development.md](../operations/local-development.md), [phases.md](phases.md), [docs/README.md](../README.md).

---

## Completion

### Summary

- [aws-deployment.md](../operations/aws-deployment.md) — Phase 6 status + ordered **Contributor path** table (ECR → desktop E2E).
- [local-development.md](../operations/local-development.md) — AWS EKS section, Compose vs Kind vs EKS table, EKS links.
- [desktop/README.md](../../desktop/README.md) — **Production (AWS staging)** settings (WSS URL, token URL, mint key).
- [kubernetes.md](../architecture/kubernetes.md) — Phase 6 CPU in-process ASR note vs Phase 7–8 diagram.
- [docs/README.md](../README.md) — ops index, Phase 6 exit link, implementation status.
- [phases.md](phases.md) — Phase 6 implemented, pending exit sign-off; recommended next steps.
- [dev-step-phase6-exit.md](dev-step-phase6-exit.md) — `ready` status, contributor-path prerequisites, operator checklist.

### Spec Changes

- Listed files above (no API contract changes).

### Automated Tests Run

```bash
cd backend && pytest -q
# 98 passed, 1 skipped (2026-10-16)
cd desktop && pnpm test
# 16 passed (2026-10-16)
```

### Manual Test Result

- [x] Pass — 2026-10-16; contributor path, cross-links, desktop production settings verified

### Commit

- **Hash:** `7bdfa5c`

### PR

- **URL:** —
