terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.this.token
}

data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_id
}

locals {
  default_tags = merge({
    Environment = var.environment,
    Project     = "meetinity"
  }, var.tags)
}

module "vpc" {
  source = "./modules/vpc"

  name                 = var.network_name
  cidr_block           = var.vpc_cidr_block
  az_count             = var.availability_zone_count
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  enable_nat_gateway   = var.enable_nat_gateway
  tags                 = local.default_tags
}

module "eks" {
  source = "./modules/eks"

  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_group_config  = var.node_group_config
  tags               = local.default_tags
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

resource "kubernetes_namespace" "security" {
  metadata {
    name = "security"
  }
}

output "cluster_auth" {
  description = "Credentials required by kubectl to access the EKS cluster."
  value = {
    endpoint = module.eks.cluster_endpoint
    ca_cert  = module.eks.cluster_certificate_authority_data
  }
  sensitive = true
}
