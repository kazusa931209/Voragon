# API Gateway — staging JWT auth (P6-005)

HTTP API that mints HS256 JWTs for the realtime WebSocket. WebSocket traffic stays on the [ALB Ingress](../../k8s/eks/alb/README.md); the backend validates the same JWT at connect time.

## Why not API Gateway WebSocket?

The realtime backend is a single long-lived FastAPI WebSocket on `/v1/realtime`. API Gateway WebSocket routes messages per integration (Lambda/HTTP), which does not map to that model without rewriting the service. Phase 6 uses **API Gateway for token issuance** and **ALB for WSS**, with JWT validation on the backend (and the same claims a future `$connect` authorizer would enforce).

## Apply

```bash
cd infra/apigateway
terraform init
terraform apply
```

Note `auth_token_url` and retrieve `mint_api_key`:

```bash
terraform output -raw mint_api_key
```

## Obtain a token

```bash
TOKEN_URL="$(terraform output -raw auth_token_url)"
MINT_KEY="$(terraform output -raw mint_api_key)"
curl -sS -X POST "$TOKEN_URL" \
  -H "x-api-key: $MINT_KEY" \
  -H "content-type: application/json" \
  -d '{}' | jq .
```

Response: `access_token`, `token_type`, `expires_in` (3600 s).

## Connect to WebSocket

Use the ALB hostname from [k8s/eks/alb](../../k8s/eks/alb/README.md):

```bash
ALB_HOST="your-alb.example.com"
TOKEN="$(curl -sS -X POST "$TOKEN_URL" -H "x-api-key: $MINT_KEY" -d '{}' | jq -r .access_token)"
websocat "wss://${ALB_HOST}/v1/realtime?access_token=${TOKEN}"
```

Or `Authorization: Bearer` when the client supports custom headers.

## Enable auth on EKS

1. Read `jwt_secret` from Secrets Manager (`terraform output jwt_secret_arn`).
2. Create a Kubernetes secret and turn on auth — see [k8s/eks/jwt-auth.example.yaml](../../k8s/eks/jwt-auth.example.yaml).
3. Redeploy / roll pods so `JWT_AUTH_REQUIRED=true` and `JWT_SECRET` apply.

## Desktop

Settings: **Auth token URL** (API Gateway `auth_token_url`) and **Mint API key**. **Backend URL** remains the ALB `wss://…/v1/realtime` endpoint; the app fetches a JWT before connect and appends `access_token` to the WebSocket URL.
