module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "~> 20.0"
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  subnet_ids      = var.private_subnet_ids
  vpc_id          = var.vpc_id

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    disk_size      = var.node_group_config.disk_size
    instance_types = var.node_group_config.instance_types
  }

  eks_managed_node_groups = {
    default = {
      desired_size = var.node_group_config.desired_size
      max_size     = var.node_group_config.max_size
      min_size     = var.node_group_config.min_size
      subnet_ids   = var.private_subnet_ids
    }
  }

  tags = var.tags
}
