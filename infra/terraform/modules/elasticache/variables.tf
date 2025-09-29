variable "name" {
  description = "Base name for the ElastiCache replication group and related resources."
  type        = string
}

variable "engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "node_type" {
  description = "Node instance type for the replication group."
  type        = string
  default     = "cache.r6g.large"
}

variable "num_cache_clusters" {
  description = "Number of cache nodes to create in the replication group."
  type        = number
  default     = 2
}

variable "subnet_ids" {
  description = "Private subnet identifiers used by the cache subnet group."
  type        = list(string)
}

variable "vpc_id" {
  description = "Identifier of the VPC that hosts the cache cluster."
  type        = string
}

variable "port" {
  description = "Port exposed by the Redis cluster."
  type        = number
  default     = 6379
}

variable "parameter_group_family" {
  description = "Parameter group family for Redis."
  type        = string
  default     = "redis7"
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the Redis cluster."
  type        = list(string)
  default     = []
}

variable "allowed_security_group_ids" {
  description = "Security groups allowed to reach the Redis cluster."
  type        = list(string)
  default     = []
}

variable "maintenance_window" {
  description = "Weekly time range in UTC for maintenance operations."
  type        = string
  default     = "sun:05:00-sun:06:00"
}

variable "snapshot_retention_limit" {
  description = "Number of days to retain automatic snapshots."
  type        = number
  default     = 7
}

variable "apply_immediately" {
  description = "Whether modifications should be applied immediately."
  type        = bool
  default     = false
}

variable "transit_encryption_enabled" {
  description = "Enable in-transit encryption."
  type        = bool
  default     = true
}

variable "at_rest_encryption_enabled" {
  description = "Enable at-rest encryption."
  type        = bool
  default     = true
}

variable "auto_minor_version_upgrade" {
  description = "Automatically upgrade to minor engine versions."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to all created resources."
  type        = map(string)
  default     = {}
}
