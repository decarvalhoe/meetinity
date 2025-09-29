variable "enabled" {
  description = "Whether to enable the AWS Backup plan."
  type        = bool
}

variable "environment" {
  description = "Environment identifier used for naming."
  type        = string
}

variable "vault_name" {
  description = "Optional custom name for the backup vault."
  type        = string
  default     = null
}

variable "plan_name" {
  description = "Optional custom name for the backup plan."
  type        = string
  default     = null
}

variable "schedule_expression" {
  description = "Cron expression defining when backups are created."
  type        = string
  default     = "cron(0 3 * * ? *)"
}

variable "start_window" {
  description = "The amount of time in minutes before a backup job is considered late."
  type        = number
  default     = 60
}

variable "completion_window" {
  description = "The amount of time in minutes AWS Backup attempts a backup before canceling the job."
  type        = number
  default     = 360
}

variable "cold_storage_after" {
  description = "Number of days before moving recovery points to cold storage."
  type        = number
  default     = 0
}

variable "delete_after" {
  description = "Number of days before deleting recovery points."
  type        = number
  default     = 35
}

variable "resource_arns" {
  description = "List of resource ARNs to include in the backup selection."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to created resources."
  type        = map(string)
  default     = {}
}
