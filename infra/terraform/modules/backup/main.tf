locals {
  enabled            = var.enabled
  vault_name         = local.enabled ? coalesce(var.vault_name, "${var.environment}-backup-vault") : null
  plan_name          = local.enabled ? coalesce(var.plan_name, "${var.environment}-daily-backup") : null
  selection_name     = local.enabled ? "${var.environment}-backup-selection" : null
  lifecycle_required = var.cold_storage_after > 0 || var.delete_after > 0
}

resource "aws_backup_vault" "this" {
  count = local.enabled ? 1 : 0

  name        = local.vault_name
  kms_key_arn = null
  tags        = merge(var.tags, { Name = local.vault_name })
}

resource "aws_backup_plan" "this" {
  count = local.enabled ? 1 : 0

  name = local.plan_name

  rule {
    rule_name         = "${local.plan_name}-rule"
    target_vault_name = aws_backup_vault.this[0].name
    schedule          = var.schedule_expression
    start_window      = var.start_window
    completion_window = var.completion_window

    dynamic "lifecycle" {
      for_each = local.lifecycle_required ? [1] : []

      content {
        cold_storage_after = var.cold_storage_after > 0 ? var.cold_storage_after : null
        delete_after       = var.delete_after > 0 ? var.delete_after : null
      }
    }
  }

  tags = merge(var.tags, { Name = local.plan_name })
}

resource "aws_iam_role" "backup" {
  count = local.enabled ? 1 : 0

  name = "${var.environment}-aws-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "backup.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  count      = local.enabled ? 1 : 0
  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore" {
  count      = local.enabled ? 1 : 0
  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

locals {
  filtered_resource_arns = [for arn in var.resource_arns : arn if arn != null && arn != ""]
}

resource "aws_backup_selection" "this" {
  count = local.enabled && length(local.filtered_resource_arns) > 0 ? 1 : 0

  iam_role_arn = aws_iam_role.backup[0].arn
  name         = local.selection_name
  plan_id      = aws_backup_plan.this[0].id
  resources    = local.filtered_resource_arns
}
