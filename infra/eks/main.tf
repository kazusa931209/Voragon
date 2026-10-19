locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.17"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i + 2)]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = merge(
    {
      cpu = {
        instance_types = var.node_instance_types
        min_size       = var.node_min_size
        max_size       = var.node_max_size
        desired_size   = var.node_desired_size

        labels = {
          node-type = "cpu"
        }

        # Default node role includes AmazonEC2ContainerRegistryReadOnly (same-account ECR pull).
      }
    },
    var.enable_gpu_node_group ? {
      gpu = {
        instance_types = var.gpu_node_instance_types
        min_size       = var.gpu_node_min_size
        max_size       = var.gpu_node_max_size
        desired_size   = var.gpu_node_desired_size

        labels = {
          node-type = "gpu"
        }

        taints = {
          gpu = {
            key    = "nvidia.com/gpu"
            value  = "true"
            effect = "NO_SCHEDULE"
          }
        }
      }
    } : {}
  )
}
