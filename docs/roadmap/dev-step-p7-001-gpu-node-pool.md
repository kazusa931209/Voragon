# P7-001: EKS GPU Node Pool

| Field | Value |
|-------|-------|
| **ID** | P7-001 |
| **Phase** | 7 |
| **Status** | done |
| **Commit** | — |
| **PR** | — |
| **Branch** | `dev-step/p7-001-gpu-node-pool` |

## Spec References

- [ADR-010: GPU Node Pool](../decisions/ADR-010-gpu-node-pool.md)
- [Kubernetes Architecture](../architecture/kubernetes.md) — GPU Node Pool
- [AWS Deployment](../operations/aws-deployment.md) — Phase 7
- [dev-step-p6-002](dev-step-p6-002-eks-cluster-cpu.md)

## Scope

One verifiable behavior: **staging EKS has a managed GPU node group (e.g. g5.xlarge) with GPU taint and `node-type=gpu` label; nodes reach Ready.**

- Extend [infra/eks](../../infra/eks/) Terraform (second `eks_managed_node_groups` entry)
- Taint: `nvidia.com/gpu=true:NoSchedule` (per ADR-010)
- Document min/desired/max sizing and cost note in [infra/eks/README.md](../../infra/eks/README.md)

## Out of Scope

- NVIDIA device plugin (P7-002)
- ASR workloads (P7-004+)

## Acceptance Criteria

- [x] Terraform defines GPU managed node group (`enable_gpu_node_group`, taint, labels)
- [x] `terraform apply` creates GPU node group on existing P6-002 cluster (operator)
- [x] `kubectl get nodes -l node-type=gpu` shows Ready (operator)
- [x] GPU nodes have documented taint; CPU realtime pods stay on CPU pool (operator smoke)

## Manual Test

1. `terraform -chdir=infra/eks apply` with GPU variables enabled
2. `kubectl get nodes -L node-type -o wide`
3. Confirm CPU `realtime-backend` pods unchanged on CPU nodes

## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```

## Spec Changes

Expected: [infra/eks/README.md](../../infra/eks/README.md), [aws-deployment.md](../operations/aws-deployment.md) Phase 7 step 1.

---

## Completion

### Summary

- [infra/eks](../../infra/eks/) — optional `gpu` managed node group (`g5.xlarge`), label `node-type=gpu`, taint `nvidia.com/gpu=true:NoSchedule`; CPU nodes labeled `node-type=cpu`.
- Contract tests: `backend/tests/test_eks_gpu_terraform.py`.

### Spec Changes

- [infra/eks/README.md](../../infra/eks/README.md), [aws-deployment.md](../operations/aws-deployment.md) Phase 7 step 1.

### Automated Tests Run

```bash
cd infra/eks && terraform fmt && terraform init -backend=false && terraform validate
# Success! The configuration is valid.
cd backend && pytest -q
# 100 passed, 1 skipped (after P7-001 tests)
```

### Manual Test Result

- [x] Pass — 2026-10-16; GPU nodes Ready with taint; realtime-backend on CPU nodes

### Commit

- **Hash:** `05a082d`

### PR

- **URL:** —
