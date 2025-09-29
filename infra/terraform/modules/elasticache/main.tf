locals {
  name = replace(lower(var.name), "_", "-")
}

resource "random_password" "auth" {
  length  = 32
  special = false
}

resource "aws_security_group" "this" {
  name        = "${local.name}-sg"
  description = "Security group for ${local.name} Redis cluster"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-sg"
  })
}

resource "aws_security_group_rule" "cidr_ingress" {
  for_each = toset(var.allowed_cidr_blocks)

  type              = "ingress"
  security_group_id = aws_security_group.this.id
  from_port         = var.port
  to_port           = var.port
  protocol          = "tcp"
  cidr_blocks       = [each.value]
}

resource "aws_security_group_rule" "sg_ingress" {
  for_each = toset(var.allowed_security_group_ids)

  type                     = "ingress"
  security_group_id        = aws_security_group.this.id
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = each.value
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${local.name}-subnet"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name = "${local.name}-subnet"
  })
}

resource "aws_elasticache_parameter_group" "this" {
  name        = "${local.name}-pg"
  family      = var.parameter_group_family
  description = "Parameter group for ${local.name}"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  tags = merge(var.tags, {
    Name = "${local.name}-pg"
  })
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id          = local.name
  description                   = "Highly available Redis for ${local.name}"
  engine                        = "redis"
  engine_version                = var.engine_version
  node_type                     = var.node_type
  port                          = var.port
  number_cache_clusters         = var.num_cache_clusters
  multi_az_enabled              = true
  automatic_failover_enabled    = true
  transit_encryption_enabled    = var.transit_encryption_enabled
  at_rest_encryption_enabled    = var.at_rest_encryption_enabled
  auth_token                    = random_password.auth.result
  security_group_ids            = [aws_security_group.this.id]
  subnet_group_name             = aws_elasticache_subnet_group.this.name
  parameter_group_name          = aws_elasticache_parameter_group.this.name
  maintenance_window            = var.maintenance_window
  snapshot_retention_limit      = var.snapshot_retention_limit
  apply_immediately             = var.apply_immediately
  auto_minor_version_upgrade    = var.auto_minor_version_upgrade

  tags = merge(var.tags, {
    Name = local.name
  })
}
