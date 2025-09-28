variable "aws_region" {
  description = "AWS region where resources will be created."
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, staging, prod)."
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to created resources."
  type        = map(string)
  default     = {}
}

variable "network_name" {
  description = "Base name used for VPC resources."
  type        = string
  default     = "meetinity-network"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zone_count" {
  description = "Number of availability zones to span."
  type        = number
  default     = 3
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets."
  type        = list(string)
  default     = [
    "10.0.0.0/19",
    "10.0.32.0/19",
    "10.0.64.0/19"
  ]
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets."
  type        = list(string)
  default     = [
    "10.0.96.0/20",
    "10.0.112.0/20",
    "10.0.128.0/20"
  ]
}

variable "enable_nat_gateway" {
  description = "Whether to provision a managed NAT gateway for outbound traffic from private subnets."
  type        = bool
  default     = true
}

variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
  default     = "meetinity-eks"
}

variable "kubernetes_version" {
  description = "Desired Kubernetes version for the cluster."
  type        = string
  default     = "1.29"
}

variable "node_group_config" {
  description = "Configuration map for managed node groups."
  type = object({
    desired_size = number
    max_size     = number
    min_size     = number
    instance_types = list(string)
    disk_size      = number
  })
  default = {
    desired_size   = 3
    max_size       = 6
    min_size       = 2
    instance_types = ["t3.large"]
    disk_size      = 50
  }
}

variable "cluster_admin_role_name" {
  description = "Friendly name for the IAM role mapped to Kubernetes cluster-admin."
  type        = string
  default     = "meetinity-eks-admin"
}

variable "cluster_admin_principal_arns" {
  description = "IAM principal ARNs allowed to assume the cluster-admin role in addition to the account root."
  type        = list(string)
  default     = []
}

variable "default_tls_dns_names" {
  description = "DNS names included in the default ingress TLS certificate."
  type        = list(string)
  default     = ["meetinity.local"]
}

variable "default_tls_secret_name" {
  description = "Name of the Kubernetes secret storing the default ingress TLS certificate."
  type        = string
  default     = "meetinity-ingress-tls"
}
