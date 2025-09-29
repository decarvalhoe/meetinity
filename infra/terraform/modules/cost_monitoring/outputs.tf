output "budget_arn" {
  description = "ARN of the AWS Budget used for cost monitoring."
  value       = try(aws_budgets_budget.monthly[0].arn, null)
}
