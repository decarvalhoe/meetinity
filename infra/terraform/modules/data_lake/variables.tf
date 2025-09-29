variable "name" {
  description = "Base name applied to data lake resources"
  type        = string
}

variable "bucket_name" {
  description = "Optional explicit bucket name for the data lake"
  type        = string
  default     = null
}

variable "force_destroy" {
  description = "Whether to allow Terraform to delete the bucket with objects"
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable object versioning on the data lake bucket"
  type        = bool
  default     = true
}

variable "create_kms_key" {
  description = "Create a dedicated KMS key for the data lake when kms_key_arn is not provided"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "Existing KMS key ARN used to encrypt S3 and Athena outputs"
  type        = string
  default     = null
}

variable "glue_database_name" {
  description = "Name of the Glue Data Catalog database"
  type        = string
}

variable "crawler_name" {
  description = "Name assigned to the Glue crawler"
  type        = string
}

variable "crawler_role_name" {
  description = "IAM role name assumed by the Glue crawler"
  type        = string
  default     = null
}

variable "crawler_schedule" {
  description = "Optional schedule expression for the Glue crawler"
  type        = string
  default     = null
}

variable "crawler_s3_target_path" {
  description = "S3 path crawled for new datasets"
  type        = string
  default     = null
}

variable "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  type        = string
}

variable "athena_output_prefix" {
  description = "Prefix within the bucket where Athena query results are stored"
  type        = string
  default     = "athena/results/"
}

variable "athena_enforce_bucket_owner_full_control" {
  description = "Whether Athena should enforce BUCKET_OWNER_FULL_CONTROL ACLs on query results"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Map of tags applied to all resources"
  type        = map(string)
  default     = {}
}

