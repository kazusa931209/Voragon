# ECR: Voragon container images

Terraform creates:

| Repository | Image | Dockerfile |
|------------|-------|------------|
| `voragon/realtime-backend` (P6-001) | Realtime CPU service | [docker/realtime-backend/Dockerfile](../../docker/realtime-backend/Dockerfile) |
| `voragon/asr-inference` (P7-003) | GPU ASR service | [docker/asr-inference/Dockerfile](../../docker/asr-inference/Dockerfile) |

## Prerequisites


| Tool                                                                | Purpose                                  |
| ------------------------------------------------------------------- | ---------------------------------------- |
| [Terraform](https://developer.hashicorp.com/terraform/install) 1.5+ | Apply this module                        |
| AWS CLI                                                             | Credentials and `ecr get-login-password` |
| Docker                                                              | Build and push                           |


Configure AWS credentials (environment, `aws configure`, or SSO). Do not commit secrets or `.tfstate` to git.

Default region: `ap-northeast-1` (override with `-var=aws_region=...` or `TF_VAR_aws_region`).

## Create the repository

From the **repository root**:

```bash
terraform -chdir=infra/ecr init
terraform -chdir=infra/ecr plan
terraform -chdir=infra/ecr apply
```

Note the `repository_url` output:

```bash
terraform -chdir=infra/ecr output -raw repository_url
```



## Build, tag, and push

Run from the **repository root** after `apply`:

```bash
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"
export ECR_URI="$(terraform -chdir=infra/ecr output -raw repository_url)"
export TAG="${TAG:-$(git rev-parse --short HEAD)}"

docker build -f docker/realtime-backend/Dockerfile -t voragon/realtime-backend:local .
docker tag voragon/realtime-backend:local "${ECR_URI}:${TAG}"
docker tag voragon/realtime-backend:local "${ECR_URI}:latest"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${ECR_URI%%/*}"

docker push "${ECR_URI}:${TAG}"
docker push "${ECR_URI}:latest"
```



### Tag convention


| Tag           | Use                                                          |
| ------------- | ------------------------------------------------------------ |
| `local`       | Kind / Docker Compose only — **do not push** to ECR          |
| Git short SHA | Primary deploy tag for EKS (P6-003)                          |
| `latest`      | Optional staging pointer; mutable — prefer SHA for rollbacks |


Verify in ECR:

```bash
REPO_NAME="$(terraform -chdir=infra/ecr output -raw repository_name)"
aws ecr describe-images --region "$AWS_REGION" \
  --repository-name "$REPO_NAME" --image-ids imageTag="$TAG"
```

Pull test (same account, after login):

```bash
docker pull "${ECR_URI}:${TAG}"
```



## Destroy

```bash
terraform -chdir=infra/ecr destroy
```

Delete images first if the repository is non-empty and destroy fails.

## ASR inference (P7-003)

Same `terraform apply` creates `voragon/asr-inference`. Build and push:

```bash
export ECR_URI="$(terraform -chdir=infra/ecr output -raw asr_repository_url)"
docker build -f docker/asr-inference/Dockerfile -t voragon/asr-inference:local .
# tag, login, push — see docker/asr-inference/README.md
```

## Related

- [docker/realtime-backend/README.md](../../docker/realtime-backend/README.md)
- [docker/asr-inference/README.md](../../docker/asr-inference/README.md)
- [docs/operations/aws-deployment.md](../../docs/operations/aws-deployment.md)

