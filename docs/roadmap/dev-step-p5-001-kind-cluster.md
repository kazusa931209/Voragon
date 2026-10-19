# P5-001: Kind Cluster and Image Load

| Field | Value |
|-------|-------|
| **ID** | P5-001 |
| **Phase** | 5 |
| **Status** | done |
| **Commit** | [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e) |
| **PR** | [#17](https://github.com/kazusa931209-cmd/Voragon/pull/17) |
| **Branch** | `dev-step/p5-001-kind-cluster` |

## Spec References

- [Local Kubernetes (Kind)](../operations/kubernetes-local.md)
- [Kubernetes Architecture](../architecture/kubernetes.md) — MVP Kind section
- [docker/realtime-backend/README.md](../../docker/realtime-backend/README.md)
- [dev-step-p4-001](dev-step-p4-001-backend-dockerfile.md)

## Scope

One verifiable behavior: **a local Kind cluster named `voragon` can be created from repo config, and the P4 realtime-backend image is built and loaded onto cluster nodes for `IfNotPresent` pulls.**

- `k8s/kind/voragon.yaml` — single-node Kind cluster
- `k8s/README.md` — create, build, load, verify, delete commands
- Reuse image tag `voragon/realtime-backend:local` (same as Docker Compose)

## Out of Scope

- Deployment / Service / ConfigMap / PVC (P5-002–P5-003)
- Helm, CI Kind jobs
- `asr-service` sidecar manifests

## Acceptance Criteria

- [x] Documented create/delete cluster flow (`kind delete cluster --name voragon`)
- [x] `kind load docker-image voragon/realtime-backend:local --name voragon` documented after repo-root build
- [x] `kubectl cluster-info --context kind-voragon` documented
- [x] [kubernetes-local.md](../operations/kubernetes-local.md) uses repo-root Dockerfile path (not `./backend`)

## Manual Test

1. From repo root: `kind create cluster --name voragon --config k8s/kind/voragon.yaml`
2. `docker build -f docker/realtime-backend/Dockerfile -t voragon/realtime-backend:local .`
3. `kind load docker-image voragon/realtime-backend:local --name voragon`
4. `kubectl cluster-info --context kind-voragon`
5. Optional: `kind delete cluster --name voragon`

## Automated Tests

```bash
cd backend && pytest -q
```

## Spec Changes

Expected: [kubernetes-local.md](../operations/kubernetes-local.md) setup paths and status.

---

## Completion

### Summary

- Added [`k8s/kind/voragon.yaml`](../../k8s/kind/voragon.yaml) (single control-plane node).
- Added [`k8s/README.md`](../../k8s/README.md) with create, build, load, delete, and cross-links.
- Updated [kubernetes-local.md](../operations/kubernetes-local.md) status and repo-root build commands.

### Spec Changes

- [kubernetes-local.md](../operations/kubernetes-local.md) — implemented status, single-pod architecture, setup commands.

### Automated Tests Run

```bash
cd backend && pytest -q
# 93 passed, 1 skipped (2026-10-15)
```

### Manual Test Result

- [x] Pass — 2026-10-15 (Kind create, image build/load, `kubectl cluster-info`)

### Commit

- **Hash:** [`8ce4b3e`](https://github.com/kazusa931209-cmd/Voragon/commit/8ce4b3e)

### PR

- **URL:** —
