# Local Kubernetes (Kind)

Run the **same** `realtime-backend` image as [Docker Compose](../docker/README.md), on a local [Kind](https://kind.sigs.k8s.io/) cluster. The desktop app stays on the host; use **port-forward** for `ws://localhost:8000/v1/realtime`.

**Phase 5 MVP:** one Deployment with in-process ASR (no `asr-service` sidecar). See [kubernetes-local.md](../docs/operations/kubernetes-local.md).

## Prerequisites

| Tool | Purpose |
|------|---------|
| Docker | Kind node runtime + image build |
| [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) | Local cluster |
| kubectl | Apply manifests, port-forward |

Stop Docker Compose or anything else bound to host port **8000** before port-forwarding.

## 1. Create cluster

From the **repository root**:

```bash
kind create cluster --name voragon --config k8s/kind/voragon.yaml
kubectl cluster-info --context kind-voragon
```

## 2. Build and load image

Build context is the repo root (same as [docker/realtime-backend/README.md](../docker/realtime-backend/README.md)):

```bash
docker build -f docker/realtime-backend/Dockerfile -t voragon/realtime-backend:local .
kind load docker-image voragon/realtime-backend:local --name voragon
```

After changing backend code or the Dockerfile, rebuild and reload the image, then restart the Deployment:

```bash
kubectl rollout restart deployment/realtime-backend -n voragon
```

## 3. Deploy manifests

```bash
kubectl apply -f k8s/local/namespace.yaml
kubectl apply -f k8s/local/
```

Wait for ASR warmup (first run may download models into the PVC; allow **2–3 minutes**):

```bash
kubectl wait -n voragon --for=condition=ready pod -l app=realtime-backend --timeout=300s
kubectl get pods,svc,pvc -n voragon
```

## 4. Port-forward and health check

In a dedicated terminal:

```bash
kubectl port-forward -n voragon svc/realtime-service 8000:8000
```

In another terminal:

```bash
curl -f http://localhost:8000/health
```

WebSocket URL for the desktop: `ws://localhost:8000/v1/realtime`.

## 5. Desktop E2E

```bash
cd desktop && pnpm tauri dev
```

Connect → Start transcription → speak → partials/finals.

## Model cache (PVC)

Manifest `k8s/local/pvc.yaml` provisions `voragon-model-cache` (10Gi, Kind default `standard` storage class). Hugging Face and Torch caches use `/var/lib/voragon/model-cache` (see `configmap.yaml`).

Deleting the pod reattaches the same PVC:

```bash
kubectl delete pod -n voragon -l app=realtime-backend
```

Wipe the cache: delete the PVC (requires deleting the Deployment first if bound).

## Rolling restart

Probes use `GET /health` on port 8000 (startup probe allows ~5 min for first ASR load).

```bash
kubectl rollout restart deployment/realtime-backend -n voragon
kubectl rollout status deployment/realtime-backend -n voragon
```

With **1 replica**, active WebSocket sessions are dropped during rollout; the desktop should reconnect (new session). Multi-replica sticky routing is Phase 6+.

## Teardown

```bash
kind delete cluster --name voragon
```

## Layout

```
k8s/
├── README.md           # this file
├── kind/
│   └── voragon.yaml    # single-node cluster
└── local/
    ├── namespace.yaml
    ├── configmap.yaml
    ├── pvc.yaml
    ├── realtime-deployment.yaml
    └── realtime-service.yaml
```

## When to use Kind vs Compose

| Use | Path |
|-----|------|
| Fast daily desktop dev | `cd docker && docker compose up` |
| Validate K8s manifests, probes, rollout | Kind + this README |

## AWS EKS (Phase 6)

Staging/production manifests live under [k8s/eks/](eks/README.md) (ECR image via Kustomize). Cluster: [infra/eks/README.md](../infra/eks/README.md).

| | Kind (`k8s/local/`) | EKS (`k8s/eks/`) |
|--|---------------------|------------------|
| Image | `voragon/realtime-backend:local` + `kind load` | ECR URI + tag ([infra/ecr](../infra/ecr/README.md)) |
| Pull policy | `IfNotPresent` | `Always` |
| PVC class | Kind `standard` | `gp2` |

## Related docs

- [Local Kubernetes (Kind)](../docs/operations/kubernetes-local.md)
- [Local development](../docs/operations/local-development.md)
- [Phase 5 exit checklist](../docs/roadmap/dev-step-phase5-exit.md)
