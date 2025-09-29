locals {
  kms_key_arn    = coalesce(var.kms_key_arn, try(aws_kms_key.this[0].arn, null))
  bucket_name    = coalesce(var.bucket_name, "${var.name}-lake")
  glue_role_name = coalesce(var.crawler_role_name, "${var.name}-glue-crawler")
  crawler_target = coalesce(var.crawler_s3_target_path, "s3://${local.bucket_name}/raw/")
}

resource "aws_kms_key" "this" {
  count                   = var.create_kms_key && var.kms_key_arn == null ? 1 : 0
  description             = "KMS key for ${var.name} data lake"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = var.tags
}

resource "aws_kms_alias" "this" {
  count         = length(aws_kms_key.this)
  name          = "alias/${var.name}-data-lake"
  target_key_id = aws_kms_key.this[0].key_id
}

resource "aws_s3_bucket" "this" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy
  tags          = var.tags
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = local.kms_key_arn != null ? "aws:kms" : "AES256"
      kms_master_key_id = local.kms_key_arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowSecureTransportOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.this.arn,
          "${aws_s3_bucket.this.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_glue_catalog_database" "this" {
  name = var.glue_database_name
  tags = var.tags
}

data "aws_iam_policy_document" "glue_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "glue_access" {
  statement {
    sid    = "S3Access"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.this.arn,
      "${aws_s3_bucket.this.arn}/*",
    ]
  }

  statement {
    sid    = "GlueCatalog"
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetTable",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:DeleteTable",
      "glue:GetPartitions",
      "glue:CreatePartition",
      "glue:UpdatePartition",
      "glue:DeletePartition",
    ]
    resources = [
      aws_glue_catalog_database.this.arn,
      "${aws_glue_catalog_database.this.arn}/*",
    ]
  }

  dynamic "statement" {
    for_each = local.kms_key_arn != null ? [local.kms_key_arn] : []
    content {
      sid    = "KMSAccess"
      effect = "Allow"
      actions = [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ]
      resources = [statement.value]
    }
  }
}

resource "aws_iam_role" "glue" {
  name               = local.glue_role_name
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "glue" {
  role   = aws_iam_role.glue.id
  policy = data.aws_iam_policy_document.glue_access.json
}

resource "aws_glue_crawler" "this" {
  name          = var.crawler_name
  database_name = aws_glue_catalog_database.this.name
  role          = aws_iam_role.glue.arn
  tags          = var.tags

  s3_target {
    path = local.crawler_target
  }

  dynamic "schedule" {
    for_each = var.crawler_schedule != null ? [var.crawler_schedule] : []
    content {
      schedule_expression = schedule.value
    }
  }
}

data "aws_iam_policy_document" "athena_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["athena.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "athena_access" {
  statement {
    sid    = "AthenaQueryAccess"
    effect = "Allow"
    actions = [
      "athena:StartQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StopQueryExecution",
      "athena:GetQueryResultsStream",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "GlueReadAccess"
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions",
    ]
    resources = [
      aws_glue_catalog_database.this.arn,
      "${aws_glue_catalog_database.this.arn}/*",
    ]
  }

  statement {
    sid    = "S3QueryAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      aws_s3_bucket.this.arn,
      "${aws_s3_bucket.this.arn}/*",
    ]
  }

  dynamic "statement" {
    for_each = local.kms_key_arn != null ? [local.kms_key_arn] : []
    content {
      sid    = "KMSAccess"
      effect = "Allow"
      actions = [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ]
      resources = [statement.value]
    }
  }
}

resource "aws_iam_role" "athena" {
  name               = "${var.name}-athena-access"
  assume_role_policy = data.aws_iam_policy_document.athena_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "athena" {
  role   = aws_iam_role.athena.id
  policy = data.aws_iam_policy_document.athena_access.json
}

resource "aws_athena_workgroup" "this" {
  name = var.athena_workgroup_name

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.this.bucket}/${var.athena_output_prefix}"

      dynamic "encryption_configuration" {
        for_each = local.kms_key_arn != null ? [local.kms_key_arn] : []
        content {
          encryption_option = "SSE_KMS"
          kms_key_arn        = encryption_configuration.value
        }
      }

      dynamic "acl_configuration" {
        for_each = var.athena_enforce_bucket_owner_full_control ? [1] : []
        content {
          s3_acl_option = "BUCKET_OWNER_FULL_CONTROL"
        }
      }
    }
  }

  force_destroy = true
  state         = "ENABLED"
  tags          = var.tags
}

