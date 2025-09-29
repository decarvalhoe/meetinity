output "endpoint" {
  description = "Writer endpoint for the PostgreSQL cluster."
  value       = aws_rds_cluster.this.endpoint
}

output "reader_endpoint" {
  description = "Reader endpoint for the PostgreSQL cluster."
  value       = aws_rds_cluster.this.reader_endpoint
}

output "port" {
  description = "Port exposed by the PostgreSQL cluster."
  value       = aws_rds_cluster.this.port
}

output "database_name" {
  description = "Default database name."
  value       = aws_rds_cluster.this.database_name
}

output "username" {
  description = "Master username of the cluster."
  value       = aws_rds_cluster.this.master_username
}

output "password" {
  description = "Generated master password for the cluster."
  value       = random_password.master.result
  sensitive   = true
}

output "security_group_id" {
  description = "Security group protecting the database cluster."
  value       = aws_security_group.this.id
}
