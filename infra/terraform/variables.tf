variable "aws_region" {
  description = "AWS region where resources will be created."
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, staging, prod)."
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to created resources."
  type        = map(string)
  default     = {}
}

variable "network_name" {
  description = "Base name used for VPC resources."
  type        = string
  default     = "meetinity-network"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zone_count" {
  description = "Number of availability zones to span."
  type        = number
  default     = 3
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets."
  type        = list(string)
  default     = [
    "10.0.0.0/19",
    "10.0.32.0/19",
    "10.0.64.0/19"
  ]
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets."
  type        = list(string)
  default     = [
    "10.0.96.0/20",
    "10.0.112.0/20",
    "10.0.128.0/20"
  ]
}

variable "enable_nat_gateway" {
  description = "Whether to provision a managed NAT gateway for outbound traffic from private subnets."
  type        = bool
  default     = true
}

variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
  default     = "meetinity-eks"
}

variable "kubernetes_version" {
  description = "Desired Kubernetes version for the cluster."
  type        = string
  default     = "1.29"
}

variable "node_group_config" {
  description = "Configuration map for managed node groups."
  type = object({
    desired_size = number
    max_size     = number
    min_size     = number
    instance_types = list(string)
    disk_size      = number
  })
  default = {
    desired_size   = 3
    max_size       = 6
    min_size       = 2
    instance_types = ["t3.large"]
    disk_size      = 50
  }
}

variable "cluster_admin_role_name" {
  description = "Friendly name for the IAM role mapped to Kubernetes cluster-admin."
  type        = string
  default     = "meetinity-eks-admin"
}

variable "cluster_admin_principal_arns" {
  description = "IAM principal ARNs allowed to assume the cluster-admin role in addition to the account root."
  type        = list(string)
  default     = []
}

variable "default_tls_dns_names" {
  description = "DNS names included in the default ingress TLS certificate."
  type        = list(string)
  default     = ["meetinity.local"]
}

variable "default_tls_secret_name" {
  description = "Name of the Kubernetes secret storing the default ingress TLS certificate."
  type        = string
  default     = "meetinity-ingress-tls"
}

variable "database_config" {
  description = "Configuration for the managed PostgreSQL cluster."
  type = object({
    name                         = string
    engine_version               = string
    db_name                      = string
    master_username              = string
    instance_class               = string
    instance_count               = number
    backup_retention_period      = number
    preferred_backup_window      = string
    preferred_maintenance_window = string
    allowed_cidr_blocks          = list(string)
    allowed_security_group_ids   = list(string)
    kms_key_id                   = optional(string)
    performance_insights_enabled = bool
  })
  default = {
    name                         = "postgres"
    engine_version               = "15.4"
    db_name                      = "meetinity"
    master_username              = "meetinity_app"
    instance_class               = "db.r6g.large"
    instance_count               = 2
    backup_retention_period      = 7
    preferred_backup_window      = "03:00-04:00"
    preferred_maintenance_window = "sun:04:00-sun:05:00"
    allowed_cidr_blocks          = []
    allowed_security_group_ids   = []
    kms_key_id                   = null
    performance_insights_enabled = true
  }
}

variable "redis_config" {
  description = "Configuration for the managed Redis cluster."
  type = object({
    name                       = string
    engine_version             = string
    node_type                  = string
    num_cache_clusters         = number
    port                       = number
    parameter_group_family     = string
    allowed_cidr_blocks        = list(string)
    allowed_security_group_ids = list(string)
    maintenance_window         = string
    snapshot_retention_limit   = number
    apply_immediately          = bool
    transit_encryption_enabled = bool
    at_rest_encryption_enabled = bool
    auto_minor_version_upgrade = bool
  })
  default = {
    name                       = "redis"
    engine_version             = "7.1"
    node_type                  = "cache.r6g.large"
    num_cache_clusters         = 2
    port                       = 6379
    parameter_group_family     = "redis7"
    allowed_cidr_blocks        = []
    allowed_security_group_ids = []
    maintenance_window         = "sun:05:00-sun:06:00"
    snapshot_retention_limit   = 7
    apply_immediately          = false
    transit_encryption_enabled = true
    at_rest_encryption_enabled = true
    auto_minor_version_upgrade = true
  }
}

variable "analytics_warehouse_config" {
  description = "Configuration for the analytics data warehouse cluster."
  type = object({
    enabled                    = bool
    name                       = string
    database_name              = string
    master_username            = string
    node_type                  = string
    number_of_nodes            = number
    port                       = number
    snapshot_retention         = number
    maintenance_window         = string
    allowed_security_group_ids = list(string)
    kms_key_id                 = optional(string)
  })
  default = {
    enabled                    = true
    name                       = "analytics-warehouse"
    database_name              = "analytics"
    master_username            = "analytics_admin"
    node_type                  = "ra3.xlplus"
    number_of_nodes            = 2
    port                       = 5439
    snapshot_retention         = 7
    maintenance_window         = "sun:05:00-sun:05:30"
    allowed_security_group_ids = []
    kms_key_id                 = null
  }
}

variable "waf_config" {
  description = "Configuration for the AWS WAF web ACL protecting the ingress load balancer."
  type = object({
    enabled             = bool
    name                = optional(string)
    scope               = optional(string)
    rate_limit          = number
    managed_rule_groups = optional(list(object({
      name     = string
      priority = number
      vendor   = optional(string)
      version  = optional(string)
    })), [])
    sampled_requests_enabled = optional(bool)
  })
  default = {
    enabled    = true
    rate_limit = 2000
    managed_rule_groups = [
      {
        name     = "AWSManagedRulesCommonRuleSet"
        priority = 1
        vendor   = "AWS"
      },
      {
        name     = "AWSManagedRulesKnownBadInputsRuleSet"
        priority = 2
        vendor   = "AWS"
      }
    ]
  }
}

variable "shield_protection" {
  description = "Configuration for AWS Shield Advanced protection applied to the ingress load balancer."
  type = object({
    enabled          = bool
    health_check_ids = optional(list(string), [])
  })
  default = {
    enabled          = true
    health_check_ids = []
  }
}

variable "static_assets" {
  description = "Configuration for the static assets CDN."
  type = object({
    enabled               = bool
    bucket_name           = optional(string)
    domain_names          = optional(list(string), [])
    price_class           = optional(string, "PriceClass_100")
    default_ttl_seconds   = optional(number, 3600)
    max_ttl_seconds       = optional(number, 86400)
    min_ttl_seconds       = optional(number, 0)
    compress              = optional(bool, true)
    acm_certificate_arn   = optional(string)
    logging_bucket        = optional(string)
    minimum_protocol      = optional(string, "TLSv1.2_2021")
  })
  default = {
    enabled = false
  }
}

variable "alb_config" {
  description = "Shared Application Load Balancer configuration."
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
  description = "Shared Network Load Balancer configuration."
  type = object({
    enabled               = bool
    name                  = optional(string)
    internal              = optional(bool, true)
    cross_zone            = optional(bool, true)
    subnets               = optional(list(string))
    tcp_port              = optional(number, 443)
    health_check_protocol = optional(string, "TCP")
    health_check_port     = optional(number)
    health_check_interval = optional(number, 30)
    healthy_threshold     = optional(number, 3)
    unhealthy_threshold   = optional(number, 3)
  })
  default = {
    enabled = false
  }
}

variable "backup_config" {
  description = "Configuration for the AWS Backup plan."
  type = object({
    enabled                = bool
    vault_name             = optional(string)
    plan_name              = optional(string)
    schedule_expression    = optional(string, "cron(0 3 * * ? *)")
    start_window_minutes   = optional(number, 60)
    completion_window      = optional(number, 360)
    cold_storage_after     = optional(number, 0)
    delete_after           = optional(number, 35)
    additional_resource_arns = optional(list(string), [])
  })
  default = {
    enabled = false
  }
}

variable "cost_monitoring" {
  description = "Configuration for AWS cost monitoring."
  type = object({
    enabled             = bool
    budget_limit        = optional(number)
    budget_type         = optional(string, "COST")
    time_unit           = optional(string, "MONTHLY")
    limit_unit          = optional(string, "USD")
    threshold_percent   = optional(number, 80)
    notification_emails = optional(list(string), [])
  })
  default = {
    enabled = false
  }
}
