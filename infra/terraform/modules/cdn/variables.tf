variable "enabled" {
  description = "Whether to provision the static assets CDN."
  type        = bool
}

variable "environment" {
  description = "Environment name used to derive resource names."
  type        = string
}

variable "bucket_name" {
  description = "Optional custom name for the S3 bucket storing static assets."
  type        = string
  default     = null
}

variable "domain_names" {
  description = "Optional list of DNS aliases for the CloudFront distribution."
  type        = list(string)
  default     = []
}

variable "price_class" {
  description = "CloudFront price class controlling the edge locations used."
  type        = string
  default     = "PriceClass_100"
}

variable "default_ttl" {
  description = "Default TTL for cached objects in seconds."
  type        = number
  default     = 3600
}

variable "max_ttl" {
  description = "Maximum TTL for cached objects in seconds."
  type        = number
  default     = 86400
}

variable "min_ttl" {
  description = "Minimum TTL for cached objects in seconds."
  type        = number
  default     = 0
}

variable "compress_objects" {
  description = "Whether to enable CloudFront compression for cached objects."
  type        = bool
  default     = true
}

variable "acm_certificate_arn" {
  description = "Optional ACM certificate ARN for custom HTTPS domains."
  type        = string
  default     = null
}

variable "logging_bucket" {
  description = "Optional S3 bucket where CloudFront access logs will be delivered."
  type        = string
  default     = null
}

variable "minimum_protocol_version" {
  description = "Minimum supported TLS protocol version for viewer connections."
  type        = string
  default     = "TLSv1.2_2021"
}

variable "tags" {
  description = "Tags applied to created resources."
  type        = map(string)
  default     = {}
}
