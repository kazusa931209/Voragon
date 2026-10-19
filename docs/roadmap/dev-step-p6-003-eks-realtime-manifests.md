# P6-003: EKS Realtime Manifests and Deploy


| Field      | Value                                    |
| ---------- | ---------------------------------------- |
| **ID**     | P6-003                                   |
| **Phase**  | 6                                        |
| **Status** | done                                     |
| **Commit** | [`658bdf8`](https://github.com/kazusa931209-cmd/Voragon/commit/658bdf8) |
| **PR**     | —                                        |
| **Branch** | `dev-step/p6-003-eks-realtime-manifests` |


## Spec References

- [Kubernetes Architecture](../architecture/kubernetes.md) — Deployments, Health Probes
- [k8s/local/](../../k8s/local/) — Kind parity reference
- [dev-step-p5-002](dev-step-p5-002-local-manifests.md), [dev-step-p5-003](dev-step-p5-003-model-cache-pvc.md), [dev-step-p5-004](dev-step-p5-004-probes-rolling-restart.md)
- [dev-step-p6-001](dev-step-p6-001-ecr-image-push.md), [dev-step-p6-002](dev-step-p6-002-eks-cluster-cpu.md)



## Scope

One verifiable behavior: `kubectl apply` **of EKS manifests deploys** `realtime-backend` **using the ECR image; pods reach Ready and in-cluster** `/health` **succeeds.**

- Manifests under `k8s/eks/` (or documented path): namespace, configmap, deployment, service, storage for model cache (EBS / PVC class appropriate for EKS)
- Deployment `image` points at ECR URI from P6-001; probes aligned with Kind (startup/liveness/readiness on `/health`)
- Initial replica count: 1 for first E2E; document path to 2 replicas before ALB (P6-004)
- **In-process ASR** only (same as Phase 5); no `asr-service` sidecar



## Out of Scope

- Internet-facing Ingress (P6-004)
- API Gateway / JWT (P6-005)
- HPA (optional follow-up within Phase 6 if not in P6-004 scope)



## Acceptance Criteria

- [x] EKS manifests committed and documented
- [x] Pod Ready after ASR warmup on EKS (operator)
- [x] `kubectl exec` or port-forward → `curl -f http://localhost:8000/health` succeeds (operator)
- [x] Model cache survives pod restart (PVC or equivalent) (operator)



## Manual Test

1. P6-002 cluster + P6-001 image tag referenced in Deployment
2. `kubectl apply -f k8s/eks/` (exact paths per README)
3. `kubectl wait` for Ready; port-forward Service → `/health`
4. Delete pod; confirm replacement Ready and faster warmup when cache populated



## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```



## Spec Changes

Expected: [kubernetes-local.md](../operations/kubernetes-local.md) or new EKS ops doc — Kind vs EKS manifest table; [architecture/kubernetes.md](../architecture/kubernetes.md) if EKS path differs from Kind.

---



## Completion



### Summary

- Added `[k8s/eks/](../../k8s/eks/)` — namespace, configmap, PVC (`gp2`), deployment (ECR image via Kustomize), service; probes aligned with Kind.
- Added `[k8s/eks/README.md](../../k8s/eks/README.md)` — `kustomize edit set image`, `kubectl apply -k`, health and PVC restart checks.
- Updated [k8s/README.md](../../k8s/README.md), [kubernetes-local.md](../operations/kubernetes-local.md), [aws-deployment.md](../operations/aws-deployment.md).



### Spec Changes

- [kubernetes-local.md](../operations/kubernetes-local.md) — Kind vs EKS manifest table.
- [aws-deployment.md](../operations/aws-deployment.md) — P6-003 section and step 3.



### Automated Tests Run

```bash
cd backend && python3.11 -m pytest -q   # 93 passed, 1 skipped (2026-10-15)
cd desktop && pnpm test                 # 14 passed (2026-10-15)
```



### Manual Test Result

- [x] Pass — operator: [k8s/eks/README.md](../../k8s/eks/README.md)



### Commit

- **Hash:** [`658bdf8`](https://github.com/kazusa931209-cmd/Voragon/commit/658bdf8)



### PR

- **URL:** —

