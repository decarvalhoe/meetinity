locals {
  enabled      = var.enabled
  budget_limit = var.budget_limit
  start_date   = "${formatdate("YYYY-MM-01", timestamp())}_00:00"
}

resource "aws_budgets_budget" "monthly" {
  count = local.enabled && local.budget_limit != null ? 1 : 0

  name              = "platform-spend"
  budget_type       = var.budget_type
  limit_amount      = tostring(local.budget_limit)
  limit_unit        = var.limit_unit
  time_unit         = var.time_unit
  time_period_start = local.start_date

  dynamic "notification" {
    for_each = var.notification_emails

    content {
      comparison_operator = "GREATER_THAN"
      threshold           = var.threshold_percent
      threshold_type      = "PERCENTAGE"
      notification_type   = "ACTUAL"

      subscriber {
        subscription_type = "EMAIL"
        address           = notification.value
      }
    }
  }

  tags = var.tags
}
