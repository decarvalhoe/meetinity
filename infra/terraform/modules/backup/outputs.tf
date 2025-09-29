output "vault_arn" {
  description = "ARN of the AWS Backup vault."
  value       = try(aws_backup_vault.this[0].arn, null)
}

output "plan_arn" {
  description = "ARN of the AWS Backup plan."
  value       = try(aws_backup_plan.this[0].arn, null)
}

output "selection_id" {
  description = "Identifier of the AWS Backup selection."
  value       = try(aws_backup_selection.this[0].id, null)
}
