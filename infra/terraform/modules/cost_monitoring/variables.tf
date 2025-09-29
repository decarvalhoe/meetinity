variable "enabled" {
  description = "Whether to enable cost monitoring resources."
  type        = bool
}

variable "budget_limit" {
  description = "Monthly cost budget limit in the billing currency."
  type        = number
  default     = null
}

variable "time_unit" {
  description = "Time unit for the AWS Budget (e.g. MONTHLY, QUARTERLY)."
  type        = string
  default     = "MONTHLY"
}

variable "budget_type" {
  description = "Type of budget to create (e.g. COST, USAGE)."
  type        = string
  default     = "COST"
}

variable "limit_unit" {
  description = "Currency unit used for the budget limit."
  type        = string
  default     = "USD"
}

variable "threshold_percent" {
  description = "Percentage of the budget that triggers notifications."
  type        = number
  default     = 80
}

variable "notification_emails" {
  description = "List of email addresses to notify when the threshold is reached."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to cost monitoring resources."
  type        = map(string)
  default     = {}
}
