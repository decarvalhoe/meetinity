locals {
  name = replace(lower(var.name), "_", "-")
}

resource "aws_security_group" "this" {
  name        = "${local.name}-clients"
  description = "Client access to ${local.name} MSK cluster"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.name}-clients"
  })
}

resource "aws_security_group_rule" "client_cidr_ingress" {
  for_each = toset(var.client_ingress_cidrs)

  description       = "Client access from CIDR ${each.value}"
  type              = "ingress"
  security_group_id = aws_security_group.this.id
  from_port         = 9094
  to_port           = 9094
  protocol          = "tcp"
  cidr_blocks       = [each.value]
}

resource "aws_security_group_rule" "client_sg_ingress" {
  for_each = toset(var.client_ingress_security_group_ids)

  description              = "Client access from security group ${each.value}"
  type                     = "ingress"
  security_group_id        = aws_security_group.this.id
  from_port                = 9094
  to_port                  = 9094
  protocol                 = "tcp"
  source_security_group_id = each.value
}

resource "aws_security_group_rule" "broker_intra" {
  description              = "Intra-cluster communication"
  type                     = "ingress"
  security_group_id        = aws_security_group.this.id
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.this.id
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/msk/${local.name}"
  retention_in_days = var.broker_log_group_retention

  tags = merge(var.tags, {
    Name = "${local.name}-logs"
  })
}

resource "aws_msk_configuration" "this" {
  count = length(var.configuration_overrides) > 0 ? 1 : 0

  name           = "${local.name}-config"
  kafka_versions = [var.kafka_version]
  description    = "Broker configuration for ${local.name}"
  server_properties = join(
    "\n",
    [for key, value in sort(var.configuration_overrides) : "${key}=${value}"]
  )

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(var.tags, {
    Name = "${local.name}-config"
  })
}

resource "aws_msk_cluster" "this" {
  cluster_name           = local.name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.number_of_broker_nodes
  enhanced_monitoring    = var.enhanced_monitoring

  broker_node_group_info {
    client_subnets = var.subnet_ids
    instance_type  = var.broker_instance_type
    security_groups = [
      aws_security_group.this.id,
    ]

    storage_info {
      ebs_storage_info {
        volume_size = var.ebs_volume_size
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.this.name
      }
    }
  }

  dynamic "configuration_info" {
    for_each = length(var.configuration_overrides) > 0 ? [1] : []
    content {
      arn      = aws_msk_configuration.this[0].arn
      revision = aws_msk_configuration.this[0].latest_revision
    }
  }

  tags = merge(var.tags, {
    Name = local.name
  })
}

resource "aws_glue_registry" "this" {
  count = var.schema_registry.enabled ? 1 : 0

  registry_name = "${local.name}-${var.schema_registry.name}"
  description   = coalesce(var.schema_registry.description, "Schema registry for ${local.name}")

  tags = merge(var.tags, {
    Name = "${local.name}-${var.schema_registry.name}"
  })
}

resource "aws_glue_schema" "compatibility_anchor" {
  count = var.schema_registry.enabled && var.schema_registry.compatibility != null ? 1 : 0

  schema_name   = "${local.name}-${var.schema_registry.name}-compat"
  data_format   = "AVRO"
  compatibility = var.schema_registry.compatibility
  registry_name = aws_glue_registry.this[0].registry_name
  schema_definition = jsonencode({
    type   = "record"
    name   = "${replace(var.schema_registry.name, "-", "_")}_compat"
    fields = []
  })
}
