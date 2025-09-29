output "domain_endpoint" {
  value       = aws_opensearch_domain.this.endpoint
  description = "HTTPS endpoint of the search domain"
}

output "security_group_id" {
  value       = aws_security_group.this.id
  description = "Security group protecting the domain"
}

output "domain_arn" {
  value       = aws_opensearch_domain.this.arn
  description = "ARN of the search domain"
}
