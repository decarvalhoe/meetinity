output "cluster_id" {
  description = "EKS cluster identifier."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data."
  value       = module.eks.cluster_certificate_authority_data
}

output "node_group_role_arn" {
  description = "IAM role ARN for the default node group."
  value       = module.eks.eks_managed_node_groups["default"].iam_role_arn
}
