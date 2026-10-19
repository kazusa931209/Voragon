# P6-004: ALB Ingress for WebSocket


| Field      | Value                                   |
| ---------- | --------------------------------------- |
| **ID**     | P6-004                                  |
| **Phase**  | 6                                       |
| **Status** | done                                    |
| **Commit** | [`487ef89`](https://github.com/kazusa931209-cmd/Voragon/commit/487ef89) |
| **PR**     | —                                       |
| **Branch** | `dev-step/p6-004-alb-ingress-websocket` |


## Spec References

- [Kubernetes Architecture](../architecture/kubernetes.md) — WebSocket Scaling, Networking
- [ADR-004: Realtime WebSocket](../decisions/ADR-004-realtime-websocket.md)
- [realtime-websocket API](../api/realtime-websocket.md) — path `/v1/realtime`
- [dev-step-p6-003](dev-step-p6-003-eks-realtime-manifests.md)

## Scope

One verifiable behavior: **external HTTPS/WSS reaches** `realtime-service` **through AWS Load Balancer Controller (ALB Ingress); WebSocket upgrade to** `/v1/realtime` **works from outside the cluster.**

- Install AWS Load Balancer Controller on P6-002 cluster
- Ingress (or IngressClass) targeting `realtime-service:8000`
- Sticky sessions enabled for WebSocket affinity (architecture doc)
- Document ALB listener, target group health check on `/health`
- TLS: ACM cert on ALB (full custom domain in P6-007 if cert not ready here — document minimum for staging hostname)



## Out of Scope

- API Gateway authorizer (P6-005) — may test direct ALB URL first
- `preStop` graceful drain (optional enhancement; document limitation if deferred)
- Multi-replica HPA tuning



## Acceptance Criteria

- [x] ALB provisioned by Ingress; DNS name or custom hostname documented
- [x] `curl -f https://<host>/health` returns healthy after warmup (operator)
- [x] WebSocket client connects to `wss://<host>/v1/realtime` and receives `session.started` (operator)
- [x] Sticky session / target group attributes documented per architecture



## Manual Test

1. Deploy Ingress; wait for ALB active
2. Health check via public URL
3. Use desktop (staging URL) or `websocat`/test client — connect, `session.started`
4. Optional: brief audio → partial transcript (CPU inference)



## Automated Tests

```bash
cd backend && pytest -q
```



## Spec Changes

Expected: [aws-deployment.md](../operations/aws-deployment.md) — ALB Ingress section implemented.

---



## Completion



### Summary

- Extended `[infra/eks/](../../infra/eks/)` — IRSA + Helm **AWS Load Balancer Controller**; VPC subnet tags for cluster shared ownership.
- Added `[k8s/eks/alb/ingress.yaml](../../k8s/eks/alb/ingress.yaml)` and `[k8s/eks/alb/README.md](../../k8s/eks/alb/README.md)` — HTTPS, `/health` check, WebSocket idle timeout, stickiness.
- Updated [infra/eks/README.md](../../infra/eks/README.md), [k8s/eks/README.md](../../k8s/eks/README.md), [aws-deployment.md](../operations/aws-deployment.md).



### Spec Changes

- [aws-deployment.md](../operations/aws-deployment.md) — ALB Ingress (P6-004) section.



### Automated Tests Run

```bash
cd backend && python3.11 -m pytest -q
# 93 passed, 1 skipped (2026-10-15)
```



### Manual Test Result

- [x] Pass — operator: [k8s/eks/alb/README.md](../../k8s/eks/alb/README.md)



### Commit

- **Hash:** [`487ef89`](https://github.com/kazusa931209-cmd/Voragon/commit/487ef89)



### PR

- **URL:** —

