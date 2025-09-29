resource "random_password" "master" {
  length  = var.master_password_length
  special = true
}

resource "aws_redshift_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids
  tags       = var.tags
}

resource "aws_redshift_cluster" "this" {
  cluster_identifier                  = var.name
  database_name                       = var.database_name
  master_username                     = var.master_username
  master_password                     = random_password.master.result
  node_type                           = var.node_type
  number_of_nodes                     = var.number_of_nodes
  port                                = var.port
  cluster_subnet_group_name           = aws_redshift_subnet_group.this.name
  vpc_security_group_ids              = var.vpc_security_group_ids
  automated_snapshot_retention_period = var.snapshot_retention
  preferred_maintenance_window        = var.maintenance_window
  publicly_accessible                 = false
  encrypted                           = true
  skip_final_snapshot                 = false
  tags                                = var.tags
  kms_key_id                          = var.kms_key_id != "" ? var.kms_key_id : null
}
