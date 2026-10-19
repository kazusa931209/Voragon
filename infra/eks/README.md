# EKS: staging cluster (P6-002 CPU, P7-001 GPU)

Terraform provisions a **staging** EKS cluster with a **CPU managed node group** (`m6i.large` by default), an optional **GPU managed node group** (`g5.xlarge`, P7-001), VPC (2 AZs, NAT), and subnet tags for ALB Ingress (P6-004).

**Default cluster name:** `voragon-staging`  
**Default region:** `ap-northeast-1` (same as [infra/ecr](../ecr/README.md))

## Prerequisites

| Tool | Purpose |
|------|---------|
| Terraform 1.5+ | Apply this module |
| AWS CLI | Credentials, `update-kubeconfig` |
| kubectl | Verify nodes |
| [P6-001 ECR](../ecr/README.md) | Image to pull in optional smoke test |

Worker nodes use the EKS-managed node IAM role, which includes **`AmazonEC2ContainerRegistryReadOnly`** for pulling images from ECR in the same account/region.

## Create the cluster

From the **repository root**:

```bash
terraform -chdir=infra/eks init
terraform -chdir=infra/eks plan
terraform -chdir=infra/eks apply
```

Configure kubectl:

```bash
aws eks update-kubeconfig --region ap-northeast-1 --name voragon-staging
# or: $(terraform -chdir=infra/eks output -raw configure_kubectl)

kubectl get nodes -o wide
```

All nodes should be **Ready**.

## GPU node pool (P7-001)

Adds a second managed node group for Phase 7 ASR on GPU ([ADR-010](../../docs/decisions/ADR-010-gpu-node-pool.md)):

| Setting | Default |
|---------|---------|
| Instance | `g5.xlarge` |
| Label | `node-type=gpu` |
| Taint | `nvidia.com/gpu=true:NoSchedule` |
| Count | desired 1, min 0, max 2 |

CPU nodes are labeled `node-type=cpu`. Existing `realtime-backend` pods (no GPU toleration) stay on CPU nodes.

**Quota:** Request **G** instance vCPU limit for `g5.xlarge` in your region before apply. Disable the pool without removing CPU cluster:

```bash
terraform -chdir=infra/eks apply -var="enable_gpu_node_group=false"
```

Verify after apply:

```bash
kubectl get nodes -L node-type --show-labels
kubectl describe node -l node-type=gpu | grep -A2 Taints
```

## NVIDIA device plugin (P7-002)

When `enable_gpu_node_group` is true, the same Terraform apply installs the [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) (Helm `0.17.1` by default) into `kube-system`. The DaemonSet tolerates `nvidia.com/gpu` taints and runs only on nodes labeled `node-type=gpu`.

```bash
terraform -chdir=infra/eks apply
kubectl get pods -n kube-system -l app.kubernetes.io/name=nvidia-device-plugin
kubectl describe node -l node-type=gpu | grep -E 'nvidia.com/gpu|Taints'
```

Expect **allocatable** `nvidia.com/gpu: 1` (or more) on each Ready GPU node. More detail: [k8s/eks/gpu/README.md](../../k8s/eks/gpu/README.md).

## AWS Load Balancer Controller (P6-004)

The same Terraform apply installs the [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) (Helm chart in `kube-system`) with IRSA. Re-run apply after upgrading the module if the cluster already existed:

```bash
terraform -chdir=infra/eks apply
kubectl get deployment -n kube-system aws-load-balancer-controller
```

Then apply the Ingress: [k8s/eks/alb/README.md](../../k8s/eks/alb/README.md).

## CloudWatch logging (P6-006)

The same Terraform apply creates log group `/voragon/eks/realtime-backend` and installs **Fluent Bit** (DaemonSet, IRSA) to ship `voragon` / `realtime-backend` container logs.

```bash
terraform -chdir=infra/eks apply
kubectl get daemonset -n amazon-cloudwatch fluent-bit
```

Verify in AWS console and sample queries: [k8s/eks/logging/README.md](../../k8s/eks/logging/README.md).

## Optional: ECR pull smoke test

After [pushing an image to ECR](../ecr/README.md):

```bash
export AWS_REGION=ap-northeast-1
export ECR_URI="$(terraform -chdir=infra/ecr output -raw repository_url)"
export TAG="${TAG:-test}"

kubectl run ecr-pull-smoke --restart=Never --image="${ECR_URI}:${TAG}" --command -- sleep 30
kubectl wait --for=condition=Ready pod/ecr-pull-smoke --timeout=120s
kubectl delete pod ecr-pull-smoke
```

If the pod becomes Ready, the node pulled the image from ECR successfully.

## Sizing (staging defaults)

| Setting | Default |
|---------|---------|
| Kubernetes | 1.31 |
| CPU nodes | 1 × `m6i.large` (min 1, max 3) |
| GPU nodes | 1 × `g5.xlarge` when enabled (min 0, max 2) — **~$1/hr+** when running |
| NAT | Single NAT gateway (cost saving) |

Override with `-var` or `TF_VAR_*` (e.g. `node_desired_size`, `enable_gpu_node_group`, `gpu_node_desired_size`).

## Destroy

```bash
terraform -chdir=infra/eks destroy
```

Remove load balancers and node groups first if destroy fails.

## Related

- [infra/ecr/README.md](../ecr/README.md)
- [docs/operations/aws-deployment.md](../../docs/operations/aws-deployment.md)
