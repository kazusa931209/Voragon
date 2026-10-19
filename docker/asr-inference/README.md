# ASR inference image (P7-003)

GPU container for standalone ASR on EKS (`asr-service`). Built from the same Python package as the realtime backend, entrypoint `app.asr_inference.main`.

## Build (repo root)

```bash
docker build -f docker/asr-inference/Dockerfile -t voragon/asr-inference:local .
```

## Local smoke (mock, no GPU)

```bash
docker run --rm -e ASR_BACKEND=mock -p 8081:8081 voragon/asr-inference:local
curl -s http://localhost:8081/health | jq .
```

## Local smoke (GPU)

Requires NVIDIA Container Toolkit:

```bash
docker run --rm --gpus all -p 8081:8081 voragon/asr-inference:local
curl -s http://localhost:8081/health | jq .
```

First start downloads Whisper weights; `asr.ready` becomes true after warmup.

## Push to ECR

After [infra/ecr](../../infra/ecr/README.md) `apply` (ASR repository):

```bash
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export ECR_URI="$(terraform -chdir=infra/ecr output -raw asr_repository_url)"
export TAG="${TAG:-$(git rev-parse --short HEAD)}"

docker tag voragon/asr-inference:local "${ECR_URI}:${TAG}"
docker tag voragon/asr-inference:local "${ECR_URI}:latest"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${ECR_URI%%/*}"

docker push "${ECR_URI}:${TAG}"
docker push "${ECR_URI}:latest"
```

## Related

- [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md)
- [dev-step-p7-003](../../docs/roadmap/dev-step-p7-003-asr-image-ecr.md)
