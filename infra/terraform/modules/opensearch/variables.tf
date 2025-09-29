variable "name" {
  description = "Base name for the search domain"
  type        = string
}

variable "engine_version" {
  description = "OpenSearch/Elasticsearch engine version"
  type        = string
  default     = "OpenSearch_2.11"
}

variable "instance_type" {
  description = "Instance type for data nodes"
  type        = string
  default     = "t3.medium.search"
}

variable "instance_count" {
  description = "Number of data nodes"
  type        = number
  default     = 2
}

variable "zone_awareness_count" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}

variable "ebs_volume_size" {
  description = "EBS volume size in GiB"
  type        = number
  default     = 100
}

variable "ebs_volume_type" {
  description = "EBS volume type"
  type        = string
  default     = "gp3"
}

variable "subnet_ids" {
  description = "Private subnet identifiers"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC identifier"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the search endpoint"
  type        = list(string)
  default     = []
}

variable "allowed_security_group_ids" {
  description = "Security groups allowed to connect to the domain"
  type        = list(string)
  default     = []
}

variable "additional_security_group_ids" {
  description = "Additional security groups to attach"
  type        = list(string)
  default     = []
}

variable "enforce_https" {
  description = "Whether HTTPS is required"
  type        = bool
  default     = true
}

variable "tls_security_policy" {
  description = "TLS policy for the endpoint"
  type        = string
  default     = "Policy-Min-TLS-1-2-2019-07"
}

variable "node_to_node_encryption" {
  description = "Enable node to node encryption"
  type        = bool
  default     = true
}

variable "enable_fine_grained_access" {
  description = "Enable fine grained access control"
  type        = bool
  default     = true
}

variable "enable_internal_user_db" {
  description = "Enable the internal user database"
  type        = bool
  default     = true
}

variable "master_user_name" {
  description = "Master user for fine grained access"
  type        = string
  default     = "meetinity-search"
}

variable "master_user_password" {
  description = "Password for the master user"
  type        = string
  sensitive   = true
}

variable "search_logs_arn" {
  description = "CloudWatch log group ARN for slow logs"
  type        = string
  default     = ""
}

variable "kms_key_id" {
  description = "Optional KMS key ID for encryption"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
