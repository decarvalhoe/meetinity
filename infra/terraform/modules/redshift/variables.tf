variable "name" {
  description = "Base name for the Redshift cluster"
  type        = string
}

variable "database_name" {
  description = "Primary database name"
  type        = string
  default     = "analytics"
}

variable "master_username" {
  description = "Master user name for Redshift"
  type        = string
  default     = "analytics_admin"
}

variable "master_password_length" {
  description = "Generated master password length"
  type        = number
  default     = 32
}

variable "node_type" {
  description = "Redshift node type"
  type        = string
  default     = "ra3.xlplus"
}

variable "number_of_nodes" {
  description = "Number of compute nodes"
  type        = number
  default     = 2
}

variable "subnet_ids" {
  description = "List of subnet IDs used by the subnet group"
  type        = list(string)
}

variable "vpc_security_group_ids" {
  description = "Security groups allowed to access the cluster"
  type        = list(string)
  default     = []
}

variable "port" {
  description = "Port exposed by the cluster"
  type        = number
  default     = 5439
}

variable "snapshot_retention" {
  description = "Number of days to retain automated snapshots"
  type        = number
  default     = 7
}

variable "maintenance_window" {
  description = "Weekly maintenance window"
  type        = string
  default     = "sun:05:00-sun:05:30"
}

variable "kms_key_id" {
  description = "Optional KMS key for encryption"
  type        = string
  default     = ""
}

variable "data_lake_bucket_arns" {
  description = "List of S3 bucket ARNs the warehouse can access"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to resources"
  type        = map(string)
  default     = {}
}

