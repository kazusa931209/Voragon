# P7-002: NVIDIA Device Plugin

| Field | Value |
|-------|-------|
| **ID** | P7-002 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-002-nvidia-device-plugin` |

## Spec References

- [ADR-010](../decisions/ADR-010-gpu-node-pool.md)
- [dev-step-p7-001](dev-step-p7-001-gpu-node-pool.md)

## Scope

One verifiable behavior: **GPU nodes advertise `nvidia.com/gpu` allocatable capacity after device plugin install.**

- Helm or Terraform install of [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) on EKS GPU nodes
- Document verify commands in ops README

## Out of Scope

- ASR container (P7-003)
- DCGM / metrics (P7-007)

## Acceptance Criteria

- [x] Terraform/Helm installs NVIDIA device plugin when GPU node group enabled
- [x] Plugin pods Running on GPU nodes (operator)
- [x] `kubectl describe node <gpu-node>` shows `nvidia.com/gpu` allocatable ≥ 1 (operator)

## Manual Test

1. Apply plugin after P7-001
2. `kubectl get pods -A | grep nvidia`
3. Describe GPU node capacity/allocatable

## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Spec Changes

Expected: [infra/eks/README.md](../../infra/eks/README.md) or new `k8s/eks/gpu/README.md`.

---

## Completion

### Summary

- [infra/eks/nvidia_device_plugin.tf](../../infra/eks/nvidia_device_plugin.tf) — Helm chart `nvidia-device-plugin` v0.17.1; schedules on `node-type=gpu` with GPU taint toleration.
- [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md) — verify commands.

### Spec Changes

- [infra/eks/README.md](../../infra/eks/README.md), [aws-deployment.md](../operations/aws-deployment.md) Phase 7 step 2.

### Automated Tests Run

```bash
cd infra/eks && terraform fmt && terraform init -backend=false && terraform validate
cd backend && pytest -q tests/test_eks_gpu_terraform.py
# 3 passed
cd backend && pytest -q
# 101 passed, 1 skipped
cd desktop && pnpm test
# 16 passed
```

### Manual Test Result

- [x] Pass — 2026-10-16; device plugin Running on GPU nodes; allocatable nvidia.com/gpu ≥ 1

### Commit

- **Hash:** `56822cb`

### PR

- **URL:** —
