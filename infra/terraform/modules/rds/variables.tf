variable "name" {
  description = "Base name used for the RDS cluster and related resources."
  type        = string
}

variable "engine" {
  description = "Database engine to use for the cluster."
  type        = string
  default     = "aurora-postgresql"
}

variable "engine_version" {
  description = "Version of the database engine."
  type        = string
  default     = "15.4"
}

variable "db_name" {
  description = "Initial database name."
  type        = string
  default     = "app"
}

variable "master_username" {
  description = "Master username for the database cluster."
  type        = string
  default     = "app_admin"
}

variable "instance_class" {
  description = "Instance class for the writer and reader instances."
  type        = string
  default     = "db.r6g.large"
}

variable "instance_count" {
  description = "Number of cluster instances to provision."
  type        = number
  default     = 2
}

variable "subnet_ids" {
  description = "Private subnet identifiers to use for the subnet group."
  type        = list(string)
}

variable "vpc_id" {
  description = "Identifier of the VPC that will host the cluster."
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks that are allowed to reach the database."
  type        = list(string)
  default     = []
}

variable "allowed_security_group_ids" {
  description = "Security groups that are allowed ingress to the database."
  type        = list(string)
  default     = []
}

variable "backup_retention_period" {
  description = "Number of days to retain automated backups."
  type        = number
  default     = 7
}

variable "preferred_backup_window" {
  description = "Daily time range in UTC for performing backups."
  type        = string
  default     = "03:00-04:00"
}

variable "preferred_maintenance_window" {
  description = "Weekly time range in UTC for system maintenance."
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "kms_key_id" {
  description = "Optional KMS key identifier used to encrypt storage."
  type        = string
  default     = null
}

variable "performance_insights_enabled" {
  description = "Whether to enable Performance Insights."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to all created resources."
  type        = map(string)
  default     = {}
}
