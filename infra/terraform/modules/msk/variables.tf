variable "name" {
  description = "Base name for the MSK cluster."
  type        = string
}

variable "kafka_version" {
  description = "Kafka version for the MSK cluster."
  type        = string
}

variable "number_of_broker_nodes" {
  description = "Number of broker nodes in the MSK cluster."
  type        = number
}

variable "broker_instance_type" {
  description = "Instance type for MSK brokers."
  type        = string
}

variable "ebs_volume_size" {
  description = "EBS volume size in GiB for each broker."
  type        = number
}

variable "subnet_ids" {
  description = "Subnet IDs for broker nodes."
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC identifier that hosts the cluster."
  type        = string
}

variable "client_ingress_cidrs" {
  description = "CIDR blocks permitted to access the brokers."
  type        = list(string)
  default     = []
}

variable "client_ingress_security_group_ids" {
  description = "Security group IDs granted broker access."
  type        = list(string)
  default     = []
}

variable "configuration_overrides" {
  description = "Additional broker properties applied via an MSK configuration."
  type        = map(string)
  default     = {}
}

variable "enhanced_monitoring" {
  description = "MSK enhanced monitoring level."
  type        = string
  default     = "PER_TOPIC_PER_PARTITION"
}

variable "broker_log_group_retention" {
  description = "Retention for broker CloudWatch logs in days."
  type        = number
  default     = 14
}

variable "schema_registry" {
  description = "Glue schema registry settings."
  type = object({
    enabled       = bool
    name          = string
    description   = optional(string)
    compatibility = optional(string)
  })
  default = {
    enabled       = true
    name          = "registry"
    description   = null
    compatibility = "BACKWARD"
  }
}

variable "tags" {
  description = "Tags applied to created resources."
  type        = map(string)
  default     = {}
}
