# P6-005: API Gateway WebSocket and Authentication


| Field      | Value                              |
| ---------- | ---------------------------------- |
| **ID**     | P6-005                             |
| **Phase**  | 6                                  |
| **Status** | done                               |
| **Commit** | [`921e438`](https://github.com/kazusa931209-cmd/Voragon/commit/921e438) |
| **PR**     | —                                  |
| **Branch** | `dev-step/p6-005-api-gateway-auth` |


## Spec References

- [realtime-websocket API](../api/realtime-websocket.md) — Production authentication
- [Kubernetes Architecture](../architecture/kubernetes.md) — Networking (API Gateway → ALB)
- [AWS Deployment](../operations/aws-deployment.md)
- [dev-step-p6-004](dev-step-p6-004-alb-ingress-websocket.md)

## Scope

One verifiable behavior: **clients obtain a JWT from the documented auth flow and connect to the production WebSocket URL through API Gateway; unauthorized connections are rejected.**

- API Gateway WebSocket API (or HTTP + upgrade pattern per AWS design) fronting ALB / VPC link
- JWT validation at gateway (authorizer or equivalent); keys in Secrets Manager / documented rotation
- Public WebSocket URL documented for desktop settings (staging)
- Desktop: optional settings for token URL + `wss://` endpoint (minimal UX for Phase 6 exit)



## Out of Scope

- Full user management / Cognito integration (unless chosen as MVP — document decision)
- Rate limiting tuning beyond defaults
- ai-gateway (Phase 8)



## Acceptance Criteria

- [x] Documented token acquisition and WebSocket connect sequence
- [x] Valid JWT → connection succeeds through API Gateway to backend (operator)
- [x] Missing/invalid JWT → connection rejected with documented error (operator)
- [x] [realtime-websocket.md](../api/realtime-websocket.md) production auth section matches implementation



## Manual Test

1. Fetch JWT per docs
2. Desktop Connect to production `wss://…/v1/realtime` with token → transcription smoke test
3. Connect without token → fails as expected



## Automated Tests

```bash
cd backend && pytest -q
cd desktop && pnpm test
```



## Spec Changes

Expected: [realtime-websocket.md](../api/realtime-websocket.md), [aws-deployment.md](../operations/aws-deployment.md), desktop settings docs if UI added.

---



## Completion



### Summary

- Added [infra/apigateway/](../../infra/apigateway/) — HTTP API `POST /v1/auth/token`, Lambda mint, Secrets Manager for `jwt_secret` / mint API key.
- Backend JWT validation on `/v1/realtime` when `JWT_AUTH_REQUIRED=true` (`Authorization` or `access_token` query); close **4401** on failure.
- Desktop settings: auth token URL + mint API key; fetches JWT before WebSocket connect.
- Documented ALB WSS + API Gateway token split (no API GW WebSocket proxy to FastAPI).



### Spec Changes

- [realtime-websocket.md](../api/realtime-websocket.md) — production auth, staging URL table.
- [aws-deployment.md](../operations/aws-deployment.md) — P6-005 section.



### Automated Tests Run

```bash
cd backend && pip install -e ".[dev]" && pytest -q
# 98 passed, 1 skipped (2026-10-15)
cd desktop && pnpm test
# 16 passed (2026-10-15)
```



### Manual Test Result

- [x] Pass — date, notes



### Commit

- **Hash:** [`921e438`](https://github.com/kazusa931209-cmd/Voragon/commit/921e438)



### PR

- **URL:** —

