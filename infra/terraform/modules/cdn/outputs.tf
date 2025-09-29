output "bucket_name" {
  description = "Name of the S3 bucket storing static assets."
  value       = try(aws_s3_bucket.static_assets[0].bucket, null)
}

output "distribution_id" {
  description = "Identifier of the CloudFront distribution."
  value       = try(aws_cloudfront_distribution.static_assets[0].id, null)
}

output "distribution_domain_name" {
  description = "Domain name assigned to the CloudFront distribution."
  value       = try(aws_cloudfront_distribution.static_assets[0].domain_name, null)
}
