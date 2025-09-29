output "cluster_identifier" {
  value       = aws_redshift_cluster.this.id
  description = "Identifier for the Redshift cluster"
}

output "endpoint" {
  value       = aws_redshift_cluster.this.endpoint
  description = "Cluster endpoint hostname"
}

output "port" {
  value       = aws_redshift_cluster.this.port
  description = "Port exposed by the cluster"
}

output "database_name" {
  value       = aws_redshift_cluster.this.database_name
  description = "Default database name"
}

output "master_username" {
  value       = aws_redshift_cluster.this.master_username
  description = "Master username"
}

output "master_password" {
  value       = random_password.master.result
  description = "Generated master password"
  sensitive   = true
}
