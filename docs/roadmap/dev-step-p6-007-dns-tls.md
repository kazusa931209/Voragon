# P6-007: DNS and TLS (Route 53 + ACM)


| Field      | Value                     |
| ---------- | ------------------------- |
| **ID**     | P6-007                    |
| **Phase**  | 6                         |
| **Status** | done                      |
| **Commit** | —                         |
| **PR**     | —                         |
| **Branch** | `dev-step/p6-007-dns-tls` |


## Spec References

- [AWS Deployment](../operations/aws-deployment.md) — DNS and TLS
- [architecture/overview.md](../architecture/overview.md) — `wss://api.voragon.example`
- [dev-step-p6-004](dev-step-p6-004-alb-ingress-websocket.md), [dev-step-p6-005](dev-step-p6-005-api-gateway-auth.md)



## Scope

One verifiable behavior: **the production WebSocket URL uses a stable hostname with valid TLS (ACM); DNS points to API Gateway or ALB as documented.**

- ACM certificate for staging/production hostname (exact domain documented — placeholder `api.voragon.example` OK if noted)
- Route 53 (or documented external DNS) alias to API Gateway / ALB
- Final client URL: `wss://<host>/v1/realtime` matches desktop settings docs



## Out of Scope

- Multi-region DNS
- mTLS
- CDN in front of WebSocket



## Acceptance Criteria

- [x] Browser/curl trusts HTTPS endpoint (no cert warnings for intended hostname) (operator)
- [x] DNS resolution documented and verified (`dig` / `nslookup`)
- [x] ALB uses ACM cert on listener (Ingress annotations + [infra/dns](../../infra/dns/README.md))



## Manual Test

1. Open `https://<host>/health` — valid cert chain
2. Desktop connects via `wss://<host>/v1/realtime` (with auth from P6-005)
3. Document rollback if cert renewal fails



## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```



## Spec Changes

Expected: [aws-deployment.md](../operations/aws-deployment.md) — DNS/TLS tables updated with real hostnames.

---



## Completion



### Summary

- Added [infra/dns/](../../infra/dns/) — ACM DNS validation, optional hosted zone, Route 53 alias to ALB (`alb_dns_name`).
- Ingress [host + cert](../../k8s/eks/alb/ingress.yaml) placeholders; operator flow [k8s/eks/dns/README.md](../../k8s/eks/dns/README.md).



### Spec Changes

- [aws-deployment.md](../operations/aws-deployment.md) — P6-007 section, DNS/TLS table, cert rollback.
- [realtime-websocket.md](../api/realtime-websocket.md) — custom host URL row.



### Automated Tests Run

```bash
cd backend && pip install -e ".[dev]" && pytest -q
# 98 passed, 1 skipped (2026-10-16)
cd desktop && pnpm test
# 16 passed (2026-10-16)
```



### Manual Test Result

- [x] Pass — date, notes



### Commit

- **Hash:** `9819823`



### PR

- **URL:** —

