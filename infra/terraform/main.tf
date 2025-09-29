terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.this.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.this.token
  }
}

data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_id
}

locals {
  default_tags = merge({
    Environment = var.environment,
    Project     = "meetinity"
  }, var.tags)
  payment_service_webhooks    = var.payment_service_webhooks
  payment_service_vault_paths = var.payment_service_vault_paths
  data_lake_bucket_name = var.data_lake_config.enabled ? coalesce(try(var.data_lake_config.bucket_name, null), "${var.environment}-${var.data_lake_config.name}") : null
  data_lake_raw_path    = var.data_lake_config.enabled ? coalesce(try(var.data_lake_config.crawler_s3_target_path, null), "s3://${local.data_lake_bucket_name}/raw/") : null
  kafka_allowed_security_group_ids = var.kafka_config.enabled ? distinct(concat(var.kafka_config.allowed_security_group_ids, [
    module.eks.node_security_group_id,
    module.eks.cluster_security_group_id,
  ])) : []
}

module "vpc" {
  source = "./modules/vpc"

  name                 = var.network_name
  cidr_block           = var.vpc_cidr_block
  az_count             = var.availability_zone_count
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  enable_nat_gateway   = var.enable_nat_gateway
  tags                 = local.default_tags
}

module "eks" {
  source = "./modules/eks"

  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_group_config  = var.node_group_config
  cluster_admin_role_name      = var.cluster_admin_role_name
  cluster_admin_principal_arns = var.cluster_admin_principal_arns
  tags               = local.default_tags
}

module "database" {
  source = "./modules/rds"

  name                         = "${var.environment}-${var.database_config.name}"
  engine_version               = var.database_config.engine_version
  db_name                      = var.database_config.db_name
  master_username              = var.database_config.master_username
  instance_class               = var.database_config.instance_class
  instance_count               = var.database_config.instance_count
  subnet_ids                   = module.vpc.private_subnet_ids
  vpc_id                       = module.vpc.vpc_id
  allowed_cidr_blocks          = var.database_config.allowed_cidr_blocks
  allowed_security_group_ids   = distinct(concat(var.database_config.allowed_security_group_ids, [
    module.eks.node_security_group_id,
    module.eks.cluster_security_group_id,
  ]))
  backup_retention_period      = var.database_config.backup_retention_period
  preferred_backup_window      = var.database_config.preferred_backup_window
  preferred_maintenance_window = var.database_config.preferred_maintenance_window
  kms_key_id                   = try(var.database_config.kms_key_id, null)
  performance_insights_enabled = var.database_config.performance_insights_enabled
  tags                         = local.default_tags
}

module "redis" {
  source = "./modules/elasticache"

  name                       = "${var.environment}-${var.redis_config.name}"
  engine_version             = var.redis_config.engine_version
  node_type                  = var.redis_config.node_type
  num_cache_clusters         = var.redis_config.num_cache_clusters
  subnet_ids                 = module.vpc.private_subnet_ids
  vpc_id                     = module.vpc.vpc_id
  port                       = var.redis_config.port
  parameter_group_family     = var.redis_config.parameter_group_family
  allowed_cidr_blocks        = var.redis_config.allowed_cidr_blocks
  allowed_security_group_ids = distinct(concat(var.redis_config.allowed_security_group_ids, [
    module.eks.node_security_group_id,
    module.eks.cluster_security_group_id,
  ]))
  maintenance_window         = var.redis_config.maintenance_window
  snapshot_retention_limit   = var.redis_config.snapshot_retention_limit
  apply_immediately          = var.redis_config.apply_immediately
  transit_encryption_enabled = var.redis_config.transit_encryption_enabled
  at_rest_encryption_enabled = var.redis_config.at_rest_encryption_enabled
  auto_minor_version_upgrade = var.redis_config.auto_minor_version_upgrade
  tags                       = local.default_tags
}

module "kafka" {
  count = var.kafka_config.enabled ? 1 : 0

  source = "./modules/msk"

  name                             = "${var.environment}-${var.kafka_config.name}"
  kafka_version                    = var.kafka_config.kafka_version
  number_of_broker_nodes           = var.kafka_config.number_of_broker_nodes
  broker_instance_type             = var.kafka_config.broker_instance_type
  ebs_volume_size                  = var.kafka_config.ebs_volume_size
  subnet_ids                       = module.vpc.private_subnet_ids
  vpc_id                           = module.vpc.vpc_id
  client_ingress_cidrs             = var.kafka_config.allowed_cidr_blocks
  client_ingress_security_group_ids = local.kafka_allowed_security_group_ids
  configuration_overrides          = try(var.kafka_config.configuration_overrides, {})
  enhanced_monitoring              = try(var.kafka_config.enhanced_monitoring, "PER_TOPIC_PER_PARTITION")
  broker_log_group_retention       = try(var.kafka_config.log_retention_in_days, 14)
  schema_registry                  = try(var.kafka_config.schema_registry, {
    enabled       = true
    name          = "registry"
    description   = null
    compatibility = "BACKWARD"
  })
  tags                             = local.default_tags
}

module "search" {
  source = "./modules/opensearch"

  name                         = "${var.environment}-${var.search_domain_config.name}"
  engine_version               = var.search_domain_config.engine_version
  instance_type                = var.search_domain_config.instance_type
  instance_count               = var.search_domain_config.instance_count
  zone_awareness_count         = var.search_domain_config.zone_awareness_count
  ebs_volume_size              = var.search_domain_config.ebs_volume_size
  ebs_volume_type              = var.search_domain_config.ebs_volume_type
  subnet_ids                   = module.vpc.private_subnet_ids
  vpc_id                       = module.vpc.vpc_id
  allowed_cidr_blocks          = var.search_domain_config.allowed_cidr_blocks
  allowed_security_group_ids   = distinct(concat(var.search_domain_config.allowed_security_group_ids, [
    module.eks.node_security_group_id,
    module.eks.cluster_security_group_id,
  ]))
  additional_security_group_ids = var.search_domain_config.additional_security_group_ids
  enforce_https                = var.search_domain_config.enforce_https
  tls_security_policy          = var.search_domain_config.tls_security_policy
  node_to_node_encryption      = var.search_domain_config.node_to_node_encryption
  enable_fine_grained_access   = var.search_domain_config.enable_fine_grained_access
  enable_internal_user_db      = var.search_domain_config.enable_internal_user_db
  master_user_name             = var.search_domain_config.master_user_name
  master_user_password         = var.search_domain_config.master_user_password
  search_logs_arn              = var.search_domain_config.search_logs_arn
  kms_key_id                   = try(var.search_domain_config.kms_key_id, null)
  tags                         = local.default_tags
}

module "data_lake" {
  source = "./modules/data_lake"

  count = var.data_lake_config.enabled ? 1 : 0

  name                               = "${var.environment}-${var.data_lake_config.name}"
  bucket_name                        = try(var.data_lake_config.bucket_name, null)
  force_destroy                      = try(var.data_lake_config.force_destroy, false)
  versioning_enabled                 = try(var.data_lake_config.versioning_enabled, true)
  create_kms_key                     = try(var.data_lake_config.create_kms_key, true)
  kms_key_arn                        = try(var.data_lake_config.kms_key_arn, null)
  glue_database_name                 = var.data_lake_config.glue_database_name
  crawler_name                       = var.data_lake_config.crawler_name
  crawler_role_name                  = try(var.data_lake_config.crawler_role_name, null)
  crawler_schedule                   = try(var.data_lake_config.crawler_schedule, null)
  crawler_s3_target_path             = local.data_lake_raw_path
  athena_workgroup_name              = var.data_lake_config.athena_workgroup_name
  athena_output_prefix               = try(var.data_lake_config.athena_output_prefix, "athena/results/")
  athena_enforce_bucket_owner_full_control = try(var.data_lake_config.athena_enforce_bucket_owner_full_control, true)
  tags                               = local.default_tags
}

module "analytics_warehouse" {
  source = "./modules/redshift"

  count                      = var.analytics_warehouse_config.enabled ? 1 : 0
  name                       = "${var.environment}-${var.analytics_warehouse_config.name}"
  database_name              = var.analytics_warehouse_config.database_name
  master_username            = var.analytics_warehouse_config.master_username
  node_type                  = var.analytics_warehouse_config.node_type
  number_of_nodes            = var.analytics_warehouse_config.number_of_nodes
  port                       = var.analytics_warehouse_config.port
  snapshot_retention         = var.analytics_warehouse_config.snapshot_retention
  maintenance_window         = var.analytics_warehouse_config.maintenance_window
  subnet_ids                 = module.vpc.private_subnet_ids
  vpc_security_group_ids     = distinct(concat(var.analytics_warehouse_config.allowed_security_group_ids, [
    module.eks.node_security_group_id,
    module.eks.cluster_security_group_id,
  ]))
  kms_key_id                 = try(var.analytics_warehouse_config.kms_key_id, null)
  data_lake_bucket_arns      = distinct(concat(try(var.analytics_warehouse_config.data_lake_bucket_arns, []), length(module.data_lake) > 0 ? [module.data_lake[0].bucket_arn] : []))
  tags                       = local.default_tags
}

module "static_assets" {
  source = "./modules/cdn"

  enabled                 = try(var.static_assets.enabled, false)
  environment             = var.environment
  bucket_name             = try(var.static_assets.bucket_name, null)
  domain_names            = try(var.static_assets.domain_names, [])
  price_class             = try(var.static_assets.price_class, "PriceClass_100")
  default_ttl             = try(var.static_assets.default_ttl_seconds, 3600)
  max_ttl                 = try(var.static_assets.max_ttl_seconds, 86400)
  min_ttl                 = try(var.static_assets.min_ttl_seconds, 0)
  compress_objects        = try(var.static_assets.compress, true)
  acm_certificate_arn     = try(var.static_assets.acm_certificate_arn, null)
  logging_bucket          = try(var.static_assets.logging_bucket, null)
  minimum_protocol_version = try(var.static_assets.minimum_protocol, "TLSv1.2_2021")
  tags                    = local.default_tags
}

module "load_balancers" {
  source = "./modules/load_balancers"

  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  environment        = var.environment
  alb_config         = var.alb_config
  nlb_config         = var.nlb_config
  tags               = local.default_tags
}

module "backup" {
  source = "./modules/backup"

  enabled            = try(var.backup_config.enabled, false)
  environment        = var.environment
  vault_name         = try(var.backup_config.vault_name, null)
  plan_name          = try(var.backup_config.plan_name, null)
  schedule_expression = try(var.backup_config.schedule_expression, "cron(0 3 * * ? *)")
  start_window        = try(var.backup_config.start_window_minutes, 60)
  completion_window   = try(var.backup_config.completion_window, 360)
  cold_storage_after  = try(var.backup_config.cold_storage_after, 0)
  delete_after        = try(var.backup_config.delete_after, 35)
  resource_arns = compact(concat([
    module.database.cluster_arn,
  ], try(var.backup_config.additional_resource_arns, [])))
  tags = local.default_tags
}

module "cost_monitoring" {
  source = "./modules/cost_monitoring"

  enabled             = try(var.cost_monitoring.enabled, false)
  budget_limit        = try(var.cost_monitoring.budget_limit, null)
  budget_type         = try(var.cost_monitoring.budget_type, "COST")
  time_unit           = try(var.cost_monitoring.time_unit, "MONTHLY")
  limit_unit          = try(var.cost_monitoring.limit_unit, "USD")
  threshold_percent   = try(var.cost_monitoring.threshold_percent, 80)
  notification_emails = try(var.cost_monitoring.notification_emails, [])
  tags                = local.default_tags
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

resource "kubernetes_namespace" "security" {
  metadata {
    name = "security"
  }
}

resource "kubernetes_namespace" "cert_manager" {
  metadata {
    name = "cert-manager"
  }
}

resource "kubernetes_namespace" "ingress" {
  metadata {
    name = "ingress-nginx"
  }
}

locals {
  cluster_issuer_name        = "selfsigned-cluster-issuer"
  ingress_default_tls_secret = var.default_tls_secret_name
  ingress_service_tag        = "${kubernetes_namespace.ingress.metadata[0].name}/ingress-nginx-controller"
  waf_name_override          = trimspace(try(var.waf_config.name, ""))
  waf_name                   = local.waf_name_override != "" ? local.waf_name_override : "${var.environment}-ingress-waf"
  waf_scope                  = try(var.waf_config.scope, "REGIONAL")
  waf_rate_limit             = var.waf_config.rate_limit
  waf_sampled_requests       = try(var.waf_config.sampled_requests_enabled, true)
  waf_enabled                = try(var.waf_config.enabled, false)
  shield_enabled             = try(var.shield_protection.enabled, false)
}

data "aws_lb" "ingress_controller" {
  tags = {
    "kubernetes.io/service-name" = local.ingress_service_tag
  }

  depends_on = [helm_release.ingress_nginx]
}

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "v1.14.4"
  namespace        = kubernetes_namespace.cert_manager.metadata[0].name
  create_namespace = false

  set {
    name  = "installCRDs"
    value = "true"
  }

  depends_on = [module.eks]
}

resource "kubernetes_manifest" "self_signed_cluster_issuer" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name = local.cluster_issuer_name
    }
    spec = {
      selfSigned = {}
    }
  }

  depends_on = [helm_release.cert_manager]
}

resource "kubernetes_manifest" "default_tls_certificate" {
  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "Certificate"
    metadata = {
      name      = "default-ingress-tls"
      namespace = kubernetes_namespace.ingress.metadata[0].name
    }
    spec = {
      dnsNames   = var.default_tls_dns_names
      secretName = local.ingress_default_tls_secret
      issuerRef = {
        kind = "ClusterIssuer"
        name = local.cluster_issuer_name
      }
      usages = ["digital signature", "key encipherment"]
    }
  }

  depends_on = [kubernetes_manifest.self_signed_cluster_issuer]
}

resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.10.0"
  namespace  = kubernetes_namespace.ingress.metadata[0].name

  set {
    name  = "controller.service.annotations.service\.beta\.kubernetes\.io/aws-load-balancer-type"
    value = "nlb"
  }

  set {
    name  = "controller.extraArgs.default-ssl-certificate"
    value = "${kubernetes_namespace.ingress.metadata[0].name}/${local.ingress_default_tls_secret}"
  }

  depends_on = [kubernetes_manifest.default_tls_certificate]
}

resource "aws_wafv2_web_acl" "ingress" {
  count = local.waf_enabled ? 1 : 0

  name        = local.waf_name
  description = "Ingress protection for the Meetinity edge."
  scope       = local.waf_scope

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${replace(local.waf_name, "-", "_")}-default"
    sampled_requests_enabled   = local.waf_sampled_requests
  }

  rule {
    name     = "RateLimit"
    priority = 0

    action {
      block {}
    }

    statement {
      rate_based_statement {
        aggregate_key_type = "IP"
        limit              = local.waf_rate_limit
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${replace(local.waf_name, "-", "_")}-ratelimit"
      sampled_requests_enabled   = local.waf_sampled_requests
    }
  }

  dynamic "rule" {
    for_each = try(var.waf_config.managed_rule_groups, [])

    content {
      name     = rule.value.name
      priority = rule.value.priority

      statement {
        managed_rule_group_statement {
          name        = rule.value.name
          vendor_name = try(rule.value.vendor, "AWS")
          version     = try(rule.value.version, null)
        }
      }

      override_action {
        none {}
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = regexreplace("${replace(local.waf_name, "-", "_")}-${lower(rule.value.name)}", "[^A-Za-z0-9_-]", "-")
        sampled_requests_enabled   = local.waf_sampled_requests
      }
    }
  }

  tags = local.default_tags
}

resource "aws_wafv2_web_acl_association" "ingress" {
  count = local.waf_enabled ? 1 : 0

  resource_arn = data.aws_lb.ingress_controller.arn
  web_acl_arn  = aws_wafv2_web_acl.ingress[0].arn
}

resource "aws_shield_protection" "ingress" {
  count = local.shield_enabled ? 1 : 0

  name         = "${var.environment}-ingress"
  resource_arn = data.aws_lb.ingress_controller.arn

  health_check_ids = try(var.shield_protection.health_check_ids, [])
}

resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type  = "gp3"
    fsType = "ext4"
  }

  depends_on = [module.eks]
}

output "cluster_auth" {
  description = "Credentials required by kubectl to access the EKS cluster."
  value = {
    endpoint = module.eks.cluster_endpoint
    ca_cert  = module.eks.cluster_certificate_authority_data
  }
  sensitive = true
}
