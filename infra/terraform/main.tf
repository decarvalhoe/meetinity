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
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
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

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.this.token
  }
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
  cluster_admin_role_name      = var.cluster_admin_role_name
  cluster_admin_principal_arns = var.cluster_admin_principal_arns
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

resource "kubernetes_namespace" "cert_manager" {
  metadata {
    name = "cert-manager"
  }
}

resource "kubernetes_namespace" "ingress" {
  metadata {
    name = "ingress-nginx"
  }
}

locals {
  cluster_issuer_name        = "selfsigned-cluster-issuer"
  ingress_default_tls_secret = var.default_tls_secret_name
}

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "v1.14.4"
  namespace        = kubernetes_namespace.cert_manager.metadata[0].name
  create_namespace = false

  set {
    name  = "installCRDs"
    value = "true"
  }

  depends_on = [module.eks]
}

resource "kubernetes_manifest" "self_signed_cluster_issuer" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = local.cluster_issuer_name
    }
    spec = {
      selfSigned = {}
    }
  }

  depends_on = [helm_release.cert_manager]
}

resource "kubernetes_manifest" "default_tls_certificate" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "Certificate"
    metadata = {
      name      = "default-ingress-tls"
      namespace = kubernetes_namespace.ingress.metadata[0].name
    }
    spec = {
      dnsNames   = var.default_tls_dns_names
      secretName = local.ingress_default_tls_secret
      issuerRef = {
        kind = "ClusterIssuer"
        name = local.cluster_issuer_name
      }
      usages = ["digital signature", "key encipherment"]
    }
  }

  depends_on = [kubernetes_manifest.self_signed_cluster_issuer]
}

resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.10.0"
  namespace  = kubernetes_namespace.ingress.metadata[0].name

  set {
    name  = "controller.service.annotations.service\.beta\.kubernetes\.io/aws-load-balancer-type"
    value = "nlb"
  }

  set {
    name  = "controller.extraArgs.default-ssl-certificate"
    value = "${kubernetes_namespace.ingress.metadata[0].name}/${local.ingress_default_tls_secret}"
  }

  depends_on = [kubernetes_manifest.default_tls_certificate]
}

resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type  = "gp3"
    fsType = "ext4"
  }

  depends_on = [module.eks]
}

output "cluster_auth" {
  description = "Credentials required by kubectl to access the EKS cluster."
  value = {
    endpoint = module.eks.cluster_endpoint
    ca_cert  = module.eks.cluster_certificate_authority_data
  }
  sensitive = true
}
