# AI Gateway image (P8-007)

CPU container for the Phase 8 AI Gateway on EKS (`ai-gateway` Service). Entrypoint: `app.ai_gateway.main` (port **8080**).

## Build (repo root)

```bash
docker build -f docker/ai-gateway/Dockerfile -t voragon/ai-gateway:local .
```

## Local smoke

Disable backend health probes when no `asr-service` is reachable:

```bash
docker run --rm \
  -e AI_GATEWAY_HEALTH_CHECKS_ENABLED=false \
  -p 8080:8080 \
  voragon/ai-gateway:local

curl -s http://localhost:8080/health | jq .
curl -s http://localhost:8080/v1/models | jq .
```

With a mock or real ASR upstream, mount a custom registry:

```bash
docker run --rm \
  -e AI_GATEWAY_HEALTH_CHECKS_ENABLED=false \
  -e AI_GATEWAY_REGISTRY_PATH=/config/registry.yaml \
  -v "$(pwd)/backend/app/ai_gateway/default_registry.yaml:/config/registry.yaml:ro" \
  -p 8080:8080 \
  voragon/ai-gateway:local
```

## Push to ECR

After [infra/ecr](../../infra/ecr/README.md) `apply` (AI Gateway repository):

```bash
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export ECR_URI="$(terraform -chdir=infra/ecr output -raw ai_gateway_repository_url)"
export TAG="${TAG:-$(git rev-parse --short HEAD)}"

docker tag voragon/ai-gateway:local "${ECR_URI}:${TAG}"
docker tag voragon/ai-gateway:local "${ECR_URI}:latest"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${ECR_URI%%/*}"

docker push "${ECR_URI}:${TAG}"
docker push "${ECR_URI}:latest"
```

## Related

- [dev-step-p8-007](../../docs/roadmap/dev-step-p8-007-ai-gateway-image.md)
- [AI Gateway architecture](../../docs/architecture/ai-gateway.md)
