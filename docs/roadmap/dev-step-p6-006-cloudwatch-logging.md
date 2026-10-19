# P6-006: CloudWatch Logging

| Field | Value |
|-------|-------|
| **ID** | P6-006 |
| **Phase** | 6 |
| **Status** | done |
| **Commit** | [`e5ffb20`](https://github.com/kazusa931209-cmd/Voragon/commit/e5ffb20) |
| **PR** | — |
| **Branch** | `dev-step/p6-006-cloudwatch-logging` |

## Spec References

- [Observability](../operations/observability.md)
- [dev-step-p2-009](dev-step-p2-009-structured-json-logging.md)
- [AWS Deployment](../operations/aws-deployment.md)
- [dev-step-p6-003](dev-step-p6-003-eks-realtime-manifests.md)

## Scope

One verifiable behavior: **structured JSON logs from `realtime-backend` pods appear in CloudWatch Logs with a documented log group and retention.**

- DaemonSet or sidecar pattern (e.g. Fluent Bit / CloudWatch agent) — document choice
- Log group naming convention (e.g. `/voragon/eks/realtime-backend`)
- Correlate with existing JSON log fields from P2-009

## Out of Scope

- Amazon Managed Prometheus / Grafana dashboards (future)
- GPU / ASR service logs (Phase 7)
- Log-based alerting

## Acceptance Criteria

- [x] Pod stdout/stderr shipped to CloudWatch (Fluent Bit DaemonSet + IRSA)
- [x] Operator can find recent logs by pod name or `session_id` field in Logs Insights
- [x] Setup documented in [aws-deployment.md](../operations/aws-deployment.md) or [observability.md](../operations/observability.md)

## Manual Test

1. Deploy logging stack; generate traffic (health + short WebSocket session)
2. CloudWatch Logs console — new events within expected delay
3. Run sample Logs Insights query from docs

## Automated Tests

```bash
cd backend && pytest -q
```

## Spec Changes

Expected: [observability.md](../operations/observability.md) — CloudWatch section status.

---

## Completion

### Summary

- Added [infra/eks/cloudwatch_logging.tf](../../infra/eks/cloudwatch_logging.tf) — log group `/voragon/eks/realtime-backend`, IRSA, Fluent Bit Helm DaemonSet (namespace `voragon`, app `realtime-backend`).
- Operator guide: [k8s/eks/logging/README.md](../../k8s/eks/logging/README.md) with Logs Insights samples.

### Spec Changes

- [observability.md](../operations/observability.md) — CloudWatch Logs (EKS) section.
- [aws-deployment.md](../operations/aws-deployment.md) — P6-006 section.

### Automated Tests Run

```bash
cd backend && pip install -e ".[dev]" && pytest -q
# 98 passed, 1 skipped (2026-10-15)
```

### Manual Test Result

- [x] Pass — 2026-10-15; Fluent Bit → `/voragon/eks/realtime-backend`, Logs Insights per [k8s/eks/logging/README.md](../../k8s/eks/logging/README.md)

### Commit

- **Hash:** [`e5ffb20`](https://github.com/kazusa931209-cmd/Voragon/commit/e5ffb20)

### PR

- **URL:** —
