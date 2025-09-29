output "cluster_arn" {
  description = "ARN of the MSK cluster."
  value       = aws_msk_cluster.this.arn
}

output "bootstrap_brokers_tls" {
  description = "TLS bootstrap brokers for MSK."
  value       = aws_msk_cluster.this.bootstrap_brokers_tls
}

output "bootstrap_brokers_sasl_iam" {
  description = "IAM authenticated bootstrap brokers."
  value       = aws_msk_cluster.this.bootstrap_brokers_sasl_iam
}

output "security_group_id" {
  description = "Security group controlling client access."
  value       = aws_security_group.this.id
}

output "log_group_name" {
  description = "CloudWatch log group capturing broker logs."
  value       = aws_cloudwatch_log_group.this.name
}

output "schema_registry_arn" {
  description = "ARN of the Glue schema registry."
  value       = length(aws_glue_registry.this) > 0 ? aws_glue_registry.this[0].arn : null
}

output "schema_registry_name" {
  description = "Name of the Glue schema registry."
  value       = length(aws_glue_registry.this) > 0 ? aws_glue_registry.this[0].registry_name : null
}
