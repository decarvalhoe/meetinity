locals {
  name = replace(lower(var.name), "_", "-")
}

resource "aws_security_group" "this" {
  name        = "${local.name}-os"
  description = "Security group for ${local.name} search domain"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-os"
  })
}

resource "aws_security_group_rule" "cidr_ingress" {
  for_each = toset(var.allowed_cidr_blocks)

  type              = "ingress"
  security_group_id = aws_security_group.this.id
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = [each.value]
}

resource "aws_security_group_rule" "sg_ingress" {
  for_each = toset(var.allowed_security_group_ids)

  type                     = "ingress"
  security_group_id        = aws_security_group.this.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = each.value
}

resource "aws_opensearch_domain" "this" {
  domain_name    = local.name
  engine_version = var.engine_version

  cluster_config {
    instance_type  = var.instance_type
    instance_count = var.instance_count
    zone_awareness {
      availability_zone_count = var.zone_awareness_count
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.ebs_volume_size
    volume_type = var.ebs_volume_type
  }

  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = concat([aws_security_group.this.id], var.additional_security_group_ids)
  }

  encrypt_at_rest {
    enabled = true
    kms_key_id = var.kms_key_id
  }

  node_to_node_encryption {
    enabled = var.node_to_node_encryption
  }

  domain_endpoint_options {
    enforce_https       = var.enforce_https
    tls_security_policy = var.tls_security_policy
  }

  advanced_security_options {
    enabled                        = var.enable_fine_grained_access
    internal_user_database_enabled = var.enable_internal_user_db

    master_user_options {
      master_user_name     = var.master_user_name
      master_user_password = var.master_user_password
    }
  }

  log_publishing_options {
    cloudwatch_log_group_arn = var.search_logs_arn
    log_type                 = "INDEX_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = var.search_logs_arn
    log_type                 = "SEARCH_SLOW_LOGS"
  }

  tags = merge(var.tags, {
    Name = local.name
  })
}

