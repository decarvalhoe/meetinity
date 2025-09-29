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

output "cluster_admin_role_arn" {
  description = "IAM role ARN that administrators must assume for kubectl access."
  value       = module.eks.cluster_admin_role_arn
}

output "ebs_csi_role_arn" {
  description = "IAM role ARN associated with the EBS CSI controller service account."
  value       = module.eks.ebs_csi_role_arn
}

output "database_endpoint" {
  description = "Writer endpoint for the managed PostgreSQL cluster."
  value       = module.database.endpoint
}

output "database_reader_endpoint" {
  description = "Reader endpoint for the managed PostgreSQL cluster."
  value       = module.database.reader_endpoint
}

output "database_port" {
  description = "Port exposed by the PostgreSQL service."
  value       = module.database.port
}

output "database_name" {
  description = "Default database created in the PostgreSQL cluster."
  value       = module.database.database_name
}

output "database_username" {
  description = "Master username configured for PostgreSQL."
  value       = module.database.username
}

output "database_password" {
  description = "Master password generated for PostgreSQL."
  value       = module.database.password
  sensitive   = true
}

output "redis_primary_endpoint" {
  description = "Primary endpoint for the Redis replication group."
  value       = module.redis.primary_endpoint
}

output "redis_reader_endpoint" {
  description = "Reader endpoint for the Redis replication group."
  value       = module.redis.reader_endpoint
}

output "redis_port" {
  description = "Port exposed by the Redis service."
  value       = module.redis.port
}

output "redis_auth_token" {
  description = "Authentication token for Redis."
  value       = module.redis.auth_token
  sensitive   = true
}

output "static_assets_bucket_name" {
  description = "Name of the S3 bucket hosting static assets."
  value       = module.static_assets.bucket_name
}

output "static_assets_cdn_domain" {
  description = "Domain name of the CloudFront distribution serving static assets."
  value       = module.static_assets.distribution_domain_name
}

output "static_assets_distribution_id" {
  description = "Identifier of the CloudFront distribution serving static assets."
  value       = module.static_assets.distribution_id
}

output "shared_alb_dns_name" {
  description = "DNS name of the shared Application Load Balancer."
  value       = module.load_balancers.alb_dns_name
}

output "shared_nlb_dns_name" {
  description = "DNS name of the shared Network Load Balancer."
  value       = module.load_balancers.nlb_dns_name
}

output "aws_backup_vault_arn" {
  description = "ARN of the AWS Backup vault protecting stateful services."
  value       = module.backup.vault_arn
}

output "cost_budget_arn" {
  description = "ARN of the AWS Budgets resource tracking monthly spend."
  value       = module.cost_monitoring.budget_arn
}
