# Voragon Desktop

Tauri 2 + React + TypeScript client for the Voragon realtime backend.

## Prerequisites

- [Tauri prerequisites](https://tauri.app/start/prerequisites/) (Rust, platform tooling)
- Node.js and pnpm

## Development

```bash
# Terminal 1 — backend (choose one)
cd ../docker && docker compose up --build   # recommended; see docker/README.md
# Or Kind: kubectl port-forward -n voragon svc/realtime-service 8000:8000 — see ../k8s/README.md
# Or: cd ../backend && source .venv/bin/activate && python -m app.main

# Terminal 2 — desktop
cd desktop
pnpm install
pnpm tauri dev
```

Connect in the app, then **Start transcription**. Global shortcut: **⌘⇧T** (macOS) / **Ctrl+Shift+T** (Windows).

Default backend URL: `ws://localhost:8000/v1/realtime`

## Production (AWS staging)

After [Phase 6](../docs/operations/aws-deployment.md) bring-up (ALB, JWT, optional custom DNS from P6-007):

| Setting | Value |
|---------|--------|
| **Backend URL** | `wss://<api-host>/v1/realtime` — use the ACM-backed hostname (e.g. `api.voragon.example`) or the ALB DNS name during bring-up |
| **Auth token URL** | API Gateway `auth_token_url` from [infra/apigateway](../infra/apigateway/README.md) (`terraform output -raw auth_token_url`) |
| **Mint API key** | `terraform output -raw mint_api_key` in `infra/apigateway` |

The app POSTs to the token URL with `x-api-key`, then connects with query param `access_token` (see [Authentication (Production)](../docs/api/realtime-websocket.md#authentication-production)). Enable JWT on the cluster with [k8s/eks/jwt-auth.example.yaml](../k8s/eks/jwt-auth.example.yaml) before expecting auth to succeed.

**Connect → Start transcription** should yield partials and finals over WSS. Invalid or missing tokens are rejected at connect (4401).

Full operator loop: [aws-deployment.md](../docs/operations/aws-deployment.md) and [Phase 6 exit](../docs/roadmap/dev-step-phase6-exit.md).

## Manual verification

- Phase 3 (desktop): [dev-step-phase3-exit.md](../docs/roadmap/dev-step-phase3-exit.md)
- Phase 4 (Docker backend + desktop): [dev-step-phase4-exit.md](../docs/roadmap/dev-step-phase4-exit.md)
- Phase 5 (Kind backend + desktop): [dev-step-phase5-exit.md](../docs/roadmap/dev-step-phase5-exit.md)

## Tests

```bash
pnpm test
cd src-tauri && cargo test
```
