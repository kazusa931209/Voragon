# Phase 5 Exit Verification


| Field         | Value                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------- |
| **Phase**     | 5                                                                                        |
| **Status**    | done — signed off **2026-10-15** (macOS)                                                 |
| **Dev-steps** | [P5-001](dev-step-p5-001-kind-cluster.md)–[P5-005](dev-step-p5-005-k8s-dev-docs-exit.md) |


## Exit Criteria ([phases.md](phases.md))

- [x] Services deploy and pass health checks on Kind
- [x] Desktop connects via port-forward
- [x] Rolling restart works without manual pod delete



## Prerequisites

See [k8s/README.md](../../k8s/README.md) and [kubernetes-local.md](../operations/kubernetes-local.md).

```bash
# One-time (or after cluster delete)
kind create cluster --name voragon --config k8s/kind/voragon.yaml
docker build -f docker/realtime-backend/Dockerfile -t voragon/realtime-backend:local .
kind load docker-image voragon/realtime-backend:local --name voragon

kubectl apply -f k8s/local/namespace.yaml
kubectl apply -f k8s/local/
kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=300s

kubectl port-forward -n voragon svc/realtime-service 8000:8000
cd desktop && pnpm tauri dev
```



## Manual Checklist

- [x] Follow [k8s/README.md](../../k8s/README.md) from repo root — Kind + kubectl installed
- [x] `curl -f http://localhost:8000/health` after port-forward (healthy after warmup)
- [x] Desktop **Connect** → **Start transcription** → partials/finals
- [x] `kubectl delete pod -n voragon -l app=realtime-backend` → new pod Ready; faster warmup (PVC cache)
- [x] `kubectl rollout restart deployment/realtime-backend -n voragon` → rollout succeeds; port-forward restored → health OK



## Automated Tests (agent / CI)

```bash
cd backend && pytest -q
cd desktop && pnpm test
```


| Run                     | Date       | Result                                 |
| ----------------------- | ---------- | -------------------------------------- |
| pytest + desktop Vitest | 2026-10-15 | 93 passed, 1 skipped; 14 Vitest passed |




## Sign-Off

When complete:

1. [x] **Status** `done` (header).
2. [x] [phases.md](phases.md) Phase 5 **Status** complete with exit sign-off.
3. [x] [dev-steps-index.md](dev-steps-index.md) — Phase 5 exit complete; **Active Step** → Phase 6 planning.
4. [x] [P5-001](dev-step-p5-001-kind-cluster.md)–[P5-005](dev-step-p5-005-k8s-dev-docs-exit.md) **Manual Test Result** pass with date in **Completion**.

