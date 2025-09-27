output "vpc_id" {
  description = "Identifier of the created VPC."
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets used by workloads."
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets for ingress and managed services."
  value       = module.vpc.public_subnet_ids
}

output "cluster_name" {
  description = "Name of the managed EKS cluster."
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint to access the Kubernetes API server."
  value       = module.eks.cluster_endpoint
}

output "node_group_role_arn" {
  description = "IAM role ARN used by the primary node group."
  value       = module.eks.node_group_role_arn
}
