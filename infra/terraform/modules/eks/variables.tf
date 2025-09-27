variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version to deploy."
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC hosting the cluster."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs used by worker nodes."
  type        = list(string)
}

variable "node_group_config" {
  description = "Sizing information for managed node groups."
  type = object({
    desired_size   = number
    max_size       = number
    min_size       = number
    instance_types = list(string)
    disk_size      = number
  })
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
