locals {
  name                     = replace(lower(var.name), "_", "-")
  parameter_group_family   = "aurora-postgresql${split(var.engine_version, ".")[0]}"
}

resource "random_password" "master" {
  length  = 32
  special = false
}

resource "aws_security_group" "this" {
  name        = "${local.name}-sg"
  description = "Security group for ${local.name} RDS cluster"
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
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = [each.value]
}

resource "aws_security_group_rule" "sg_ingress" {
  for_each = toset(var.allowed_security_group_ids)

  type                     = "ingress"
  security_group_id        = aws_security_group.this.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = each.value
}

resource "aws_db_subnet_group" "this" {
  name       = "${local.name}-subnet"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name = "${local.name}-subnet"
  })
}

resource "aws_rds_cluster_parameter_group" "this" {
  name        = "${local.name}-pg"
  family      = local.parameter_group_family
  description = "Parameter group for ${local.name}"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  tags = merge(var.tags, {
    Name = "${local.name}-pg"
  })
}
resource "aws_rds_cluster" "this" {
  cluster_identifier              = local.name
  engine                          = var.engine
  engine_version                  = var.engine_version
  database_name                   = var.db_name
  master_username                 = var.master_username
  master_password                 = random_password.master.result
  db_subnet_group_name            = aws_db_subnet_group.this.name
  vpc_security_group_ids          = [aws_security_group.this.id]
  backup_retention_period         = var.backup_retention_period
  preferred_backup_window         = var.preferred_backup_window
  preferred_maintenance_window    = var.preferred_maintenance_window
  deletion_protection             = true
  storage_encrypted               = true
  kms_key_id                      = var.kms_key_id
  copy_tags_to_snapshot           = true
  apply_immediately               = false
  allow_major_version_upgrade     = false
  iam_database_authentication_enabled = true
  performance_insights_enabled    = var.performance_insights_enabled
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.this.name

  tags = merge(var.tags, {
    Name = local.name
  })
}

resource "aws_rds_cluster_instance" "this" {
  count              = var.instance_count
  identifier         = "${local.name}-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.this.id
  instance_class     = var.instance_class
  engine             = aws_rds_cluster.this.engine
  engine_version     = aws_rds_cluster.this.engine_version
  publicly_accessible = false
  apply_immediately   = false
  promotion_tier      = count.index == 0 ? 1 : 2

  tags = merge(var.tags, {
    Name = "${local.name}-${count.index + 1}"
  })
}
