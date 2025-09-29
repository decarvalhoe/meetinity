variable "vpc_id" {
  description = "Identifier of the VPC where load balancers will be created."
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs available for load balancers."
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs available for internal load balancers."
  type        = list(string)
}

variable "environment" {
  description = "Environment name used for tagging and naming."
  type        = string
}

variable "alb_config" {
  description = "Configuration for the shared Application Load Balancer."
  type = object({
    enabled            = bool
    name               = optional(string)
    internal           = optional(bool, false)
    idle_timeout       = optional(number, 60)
    certificate_arn    = optional(string)
    subnets            = optional(list(string))
    security_group_ids = optional(list(string), [])
    http_port          = optional(number, 80)
    https_port         = optional(number, 443)
    health_check_path  = optional(string, "/healthz")
  })
  default = {
    enabled = false
  }
}

variable "nlb_config" {
  description = "Configuration for the shared Network Load Balancer."
  type = object({
    enabled                = bool
    name                   = optional(string)
    internal               = optional(bool, true)
    cross_zone             = optional(bool, true)
    subnets                = optional(list(string))
    tcp_port               = optional(number, 443)
    health_check_protocol  = optional(string, "TCP")
    health_check_port      = optional(number)
    health_check_interval  = optional(number, 30)
    healthy_threshold      = optional(number, 3)
    unhealthy_threshold    = optional(number, 3)
  })
  default = {
    enabled = false
  }
}

variable "tags" {
  description = "Tags applied to created resources."
  type        = map(string)
  default     = {}
}
