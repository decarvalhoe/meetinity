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

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS control plane."
  value       = module.eks.cluster_security_group_id
}

output "node_security_group_id" {
  description = "Security group ID used by the managed node group."
  value       = module.eks.node_security_group_id
}

output "node_group_role_arn" {
  description = "IAM role ARN for the default node group."
  value       = module.eks.eks_managed_node_groups["default"].iam_role_arn
}

output "cluster_admin_role_arn" {
  description = "IAM role ARN that maps to Kubernetes cluster-admin permissions."
  value       = aws_iam_role.cluster_admin.arn
}

output "ebs_csi_role_arn" {
  description = "IAM role ARN associated with the EBS CSI driver service account."
  value       = aws_iam_role.ebs_csi.arn
}

output "ebs_csi_addon_id" {
  description = "Identifier of the aws-ebs-csi-driver managed add-on."
  value       = aws_eks_addon.ebs_csi.id
}
