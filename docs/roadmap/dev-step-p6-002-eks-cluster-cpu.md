# P6-002: EKS Cluster and CPU Node Group


| Field      | Value                             |
| ---------- | --------------------------------- |
| **ID**     | P6-002                            |
| **Phase**  | 6                                 |
| **Status** | done                              |
| **Commit** | [`43ca4c9`](https://github.com/kazusa931209-cmd/Voragon/commit/43ca4c9) |
| **PR**     | —                                 |
| **Branch** | `dev-step/p6-002-eks-cluster-cpu` |


## Spec References

- [ADR-009: Kubernetes / EKS](../decisions/ADR-009-kubernetes-eks.md)
- [AWS Deployment](../operations/aws-deployment.md) — Prerequisites, Phase 6 steps
- [Kubernetes Architecture](../architecture/kubernetes.md) — CPU Node Pool
- [dev-step-p6-001](dev-step-p6-001-ecr-image-push.md)

## Scope

One verifiable behavior: **a non-production or staging EKS cluster exists with a CPU node group;** `kubectl` **access works and nodes are Ready.**

- VPC/subnets (new or documented reuse) suitable for EKS + ALB (P6-004)
- Managed node group on CPU instance type (e.g. `m6i.large` per aws-deployment.md)
- Document cluster name, region, and kubeconfig context
- ECR pull permissions for worker nodes (IAM / `AmazonEC2ContainerRegistryReadOnly` or scoped policy)



## Out of Scope

- GPU node pool (Phase 7)
- Application Deployments (P6-003)
- ALB Ingress Controller install (P6-004)



## Acceptance Criteria

- [x] Cluster and CPU node group created via documented IaC or eksctl commands
- [x] `kubectl get nodes` shows Ready CPU nodes (operator)
- [x] Worker IAM allows pulling images from P6-001 ECR repo
- [x] Cluster version and sizing noted in ops docs



## Manual Test

1. Apply/create cluster per docs
2. `kubectl get nodes -o wide` — all Ready
3. From a node or test pod: confirm ECR pull of P6-001 image (optional smoke Job)



## Automated Tests

```bash
cd backend && pytest -q
```



## Spec Changes

Expected: [aws-deployment.md](../operations/aws-deployment.md) — EKS cluster section with implemented commands/paths.

---



## Completion



### Summary

- Added `[infra/eks/](../../infra/eks/)` — VPC (2 AZ, single NAT) + EKS managed node group (`m6i.large`, default 1 node) via `terraform-aws-modules/vpc` and `terraform-aws-modules/eks`.
- Added `[infra/eks/README.md](../../infra/eks/README.md)` — apply, `update-kubeconfig`, node check, optional ECR pull smoke pod.
- Updated [aws-deployment.md](../operations/aws-deployment.md), [infra/README.md](../../infra/README.md).



### Spec Changes

- [aws-deployment.md](../operations/aws-deployment.md) — EKS (P6-002) section and deployment step 2.



### Automated Tests Run

```bash
cd backend && python3.11 -m pytest -q
# 93 passed, 1 skipped (2026-10-15)
```



### Manual Test Result

- [x] Pass — operator: `terraform apply`, `kubectl get nodes`, optional ECR smoke ([infra/eks/README.md](../../infra/eks/README.md))



### Commit

- **Hash:** [`43ca4c9`](https://github.com/kazusa931209-cmd/Voragon/commit/43ca4c9)



### PR

- **URL:** —

