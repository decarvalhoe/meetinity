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

output "search_domain_endpoint" {
  description = "HTTPS endpoint for the managed search cluster."
  value       = module.search.domain_endpoint
}

output "search_domain_arn" {
  description = "ARN of the managed search cluster."
  value       = module.search.domain_arn
}

output "search_security_group_id" {
  description = "Security group guarding the search domain."
  value       = module.search.security_group_id
}

output "kafka_bootstrap_brokers" {
  description = "Bootstrap brokers for the managed Kafka cluster (TLS)."
  value       = length(module.kafka) > 0 ? module.kafka[0].bootstrap_brokers_tls : null
}

output "kafka_security_group_id" {
  description = "Security group ID allowing Kafka client access."
  value       = length(module.kafka) > 0 ? module.kafka[0].security_group_id : null
}

output "kafka_schema_registry_arn" {
  description = "Glue schema registry ARN backing Kafka topics."
  value       = length(module.kafka) > 0 ? module.kafka[0].schema_registry_arn : null
}

output "kafka_log_group_name" {
  description = "CloudWatch log group capturing Kafka broker logs."
  value       = length(module.kafka) > 0 ? module.kafka[0].log_group_name : null
}

output "analytics_warehouse_endpoint" {
  description = "Endpoint of the analytics data warehouse."
  value       = length(module.analytics_warehouse) > 0 ? module.analytics_warehouse[0].endpoint : null
}

output "analytics_warehouse_port" {
  description = "Port exposed by the analytics data warehouse."
  value       = length(module.analytics_warehouse) > 0 ? module.analytics_warehouse[0].port : null
}

output "analytics_warehouse_database" {
  description = "Default database name configured for the analytics warehouse."
  value       = length(module.analytics_warehouse) > 0 ? module.analytics_warehouse[0].database_name : null
}

output "analytics_warehouse_data_access_role_arn" {
  description = "IAM role ARN the warehouse assumes for data lake access."
  value       = length(module.analytics_warehouse) > 0 ? module.analytics_warehouse[0].data_access_role_arn : null
}

output "data_lake_bucket_name" {
  description = "Name of the S3 bucket backing the analytics data lake."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].bucket_name : null
}

output "data_lake_bucket_arn" {
  description = "ARN of the S3 bucket backing the analytics data lake."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].bucket_arn : null
}

output "data_lake_glue_database" {
  description = "Glue Data Catalog database that indexes raw lake data."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].glue_database_name : null
}

output "data_lake_glue_crawler" {
  description = "Glue crawler responsible for discovering data lake schemas."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].glue_crawler_name : null
}

output "data_lake_glue_role_arn" {
  description = "IAM role ARN assumed by Glue for data lake ingestion."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].glue_role_arn : null
}

output "data_lake_athena_workgroup" {
  description = "Athena workgroup configured for querying the data lake."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].athena_workgroup_name : null
}

output "data_lake_athena_role_arn" {
  description = "IAM role ARN used by Athena for data lake queries."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].athena_role_arn : null
}

output "data_lake_kms_key_arn" {
  description = "KMS key securing the data lake if encryption is customer managed."
  value       = length(module.data_lake) > 0 ? module.data_lake[0].kms_key_arn : null
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

output "payment_service_webhook_targets" {
  description = "Configured webhook targets for the payment service."
  value       = local.payment_service_webhooks
}

output "payment_service_vault_paths" {
  description = "Vault paths used by External Secrets for payment provider credentials."
  value       = local.payment_service_vault_paths
}
