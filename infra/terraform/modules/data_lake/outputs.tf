output "bucket_name" {
  description = "Name of the S3 bucket backing the data lake"
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket backing the data lake"
  value       = aws_s3_bucket.this.arn
}

output "glue_database_name" {
  description = "Name of the Glue Data Catalog database"
  value       = aws_glue_catalog_database.this.name
}

output "glue_crawler_name" {
  description = "Name of the Glue crawler"
  value       = aws_glue_crawler.this.name
}

output "glue_role_arn" {
  description = "IAM role ARN used by the Glue crawler"
  value       = aws_iam_role.glue.arn
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.this.name
}

output "athena_role_arn" {
  description = "IAM role ARN granting Athena data access"
  value       = aws_iam_role.athena.arn
}

output "kms_key_arn" {
  description = "ARN of the KMS key securing the data lake"
  value       = local.kms_key_arn
}

