locals {
  kms_key_arn           = var.kms_key_id != "" ? var.kms_key_id : null
  data_lake_bucket_arns = distinct(var.data_lake_bucket_arns)
}

resource "random_password" "master" {
  length  = var.master_password_length
  special = true
}

resource "aws_redshift_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids
  tags       = var.tags
}

data "aws_iam_policy_document" "redshift_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "redshift_data_access" {
  statement {
    sid    = "AccountVisibility"
    effect = "Allow"
    actions = [
      "s3:ListAllMyBuckets"
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(local.data_lake_bucket_arns) > 0 ? [1] : []
    content {
      sid    = "S3DataLakeAccess"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
      resources = concat(
        local.data_lake_bucket_arns,
        [for arn in local.data_lake_bucket_arns : "${arn}/*"]
      )
    }
  }

  dynamic "statement" {
    for_each = local.kms_key_arn != null ? [local.kms_key_arn] : []
    content {
      sid    = "KMSDataLakeAccess"
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

  statement {
    sid    = "GlueCatalogAccess"
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:CreateTable",
      "glue:UpdateTable"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "data_access" {
  name               = "${var.name}-data-access"
  assume_role_policy = data.aws_iam_policy_document.redshift_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "data_access" {
  role   = aws_iam_role.data_access.id
  policy = data.aws_iam_policy_document.redshift_data_access.json
}

resource "aws_redshift_cluster" "this" {
  cluster_identifier                  = var.name
  database_name                       = var.database_name
  master_username                     = var.master_username
  master_password                     = random_password.master.result
  node_type                           = var.node_type
  number_of_nodes                     = var.number_of_nodes
  port                                = var.port
  cluster_subnet_group_name           = aws_redshift_subnet_group.this.name
  vpc_security_group_ids              = var.vpc_security_group_ids
  automated_snapshot_retention_period = var.snapshot_retention
  preferred_maintenance_window        = var.maintenance_window
  publicly_accessible                 = false
  encrypted                           = true
  skip_final_snapshot                 = false
  tags                                = var.tags
  kms_key_id                          = local.kms_key_arn
  iam_roles                           = [aws_iam_role.data_access.arn]
}

