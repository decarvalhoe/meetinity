locals {
  enabled         = var.enabled
  bucket_base     = var.bucket_name != null ? var.bucket_name : "${var.environment}-static-assets"
  origin_id       = "s3-static-assets"
  viewer_protocol = "redirect-to-https"
}

resource "random_id" "bucket_suffix" {
  count       = local.enabled && var.bucket_name == null ? 1 : 0
  byte_length = 4
}

locals {
  bucket_name = local.enabled ? (var.bucket_name != null ? var.bucket_name : "${local.bucket_base}-${lower(random_id.bucket_suffix[0].hex)}") : null
}

resource "aws_s3_bucket" "static_assets" {
  count  = local.enabled ? 1 : 0
  bucket = local.bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "static_assets" {
  count  = local.enabled ? 1 : 0
  bucket = aws_s3_bucket.static_assets[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  count  = local.enabled ? 1 : 0
  bucket = aws_s3_bucket.static_assets[0].bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "static_assets" {
  count                   = local.enabled ? 1 : 0
  bucket                  = aws_s3_bucket.static_assets[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_identity" "this" {
  count   = local.enabled ? 1 : 0
  comment = "Access identity for ${local.bucket_name}"
}

data "aws_iam_policy_document" "static_assets" {
  count = local.enabled ? 1 : 0

  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.static_assets[0].arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.this[0].iam_arn]
    }
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.static_assets[0].arn]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.this[0].iam_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "static_assets" {
  count  = local.enabled ? 1 : 0
  bucket = aws_s3_bucket.static_assets[0].id
  policy = data.aws_iam_policy_document.static_assets[0].json
}

resource "aws_cloudfront_distribution" "static_assets" {
  count               = local.enabled ? 1 : 0
  enabled             = true
  comment             = "Static assets distribution for ${var.environment}"
  price_class         = var.price_class
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  tags                = var.tags

  origin {
    domain_name = aws_s3_bucket.static_assets[0].bucket_regional_domain_name
    origin_id   = local.origin_id

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.this[0].cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = local.origin_id
    viewer_protocol_policy = local.viewer_protocol
    compress               = var.compress_objects

    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    min_ttl         = var.min_ttl
    default_ttl     = var.default_ttl
    max_ttl         = var.max_ttl
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn            = var.acm_certificate_arn
    cloudfront_default_certificate = var.acm_certificate_arn == null
    minimum_protocol_version       = var.acm_certificate_arn == null ? "TLSv1" : var.minimum_protocol_version
    ssl_support_method             = var.acm_certificate_arn == null ? null : "sni-only"
  }

  aliases = var.domain_names

  dynamic "logging_config" {
    for_each = var.logging_bucket != null ? [var.logging_bucket] : []

    content {
      include_cookies = false
      bucket          = logging_config.value
      prefix          = "cloudfront/${var.environment}"
    }
  }
}
