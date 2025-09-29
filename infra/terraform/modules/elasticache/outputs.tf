output "primary_endpoint" {
  description = "Primary endpoint address of the Redis replication group."
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint" {
  description = "Reader endpoint address of the Redis replication group."
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "Port used to access Redis."
  value       = aws_elasticache_replication_group.this.port
}

output "auth_token" {
  description = "Authentication token for Redis."
  value       = random_password.auth.result
  sensitive   = true
}

output "security_group_id" {
  description = "Security group identifier associated with the Redis cluster."
  value       = aws_security_group.this.id
}
