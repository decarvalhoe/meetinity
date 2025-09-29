locals {
  alb_enabled = try(var.alb_config.enabled, false)
  nlb_enabled = try(var.nlb_config.enabled, false)

  alb_name = local.alb_enabled ? coalesce(try(var.alb_config.name, null), "${var.environment}-shared-alb") : null
  nlb_name = local.nlb_enabled ? coalesce(try(var.nlb_config.name, null), "${var.environment}-shared-nlb") : null

  alb_subnets = local.alb_enabled ? coalesce(try(var.alb_config.subnets, []), var.public_subnet_ids) : []
  nlb_subnets = local.nlb_enabled ? coalesce(try(var.nlb_config.subnets, []), var.private_subnet_ids) : []

  alb_http_port  = try(var.alb_config.http_port, 80)
  alb_https_port = try(var.alb_config.https_port, 443)

  alb_cert_arn    = try(var.alb_config.certificate_arn, null)
  alb_health_path = try(var.alb_config.health_check_path, "/healthz")

  nlb_tcp_port = try(var.nlb_config.tcp_port, 443)
}

resource "aws_security_group" "alb" {
  count  = local.alb_enabled ? 1 : 0
  name   = "${local.alb_name}-sg"
  vpc_id = var.vpc_id
  tags   = merge(var.tags, { Name = "${local.alb_name}-sg" })

  ingress {
    description = "Allow HTTP"
    from_port   = local.alb_http_port
    to_port     = local.alb_http_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = local.alb_cert_arn != null ? [1] : []

    content {
      description = "Allow HTTPS"
      from_port   = local.alb_https_port
      to_port     = local.alb_https_port
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "alb" {
  count                      = local.alb_enabled ? 1 : 0
  name                       = substr(local.alb_name, 0, 32)
  load_balancer_type         = "application"
  security_groups            = concat(local.alb_enabled ? [aws_security_group.alb[0].id] : [], try(var.alb_config.security_group_ids, []))
  subnets                    = local.alb_subnets
  idle_timeout               = try(var.alb_config.idle_timeout, 60)
  internal                   = try(var.alb_config.internal, false)
  enable_deletion_protection = false
  tags                       = merge(var.tags, { Name = local.alb_name })
}

resource "aws_lb_target_group" "alb_http" {
  count    = local.alb_enabled ? 1 : 0
  name     = substr("${local.alb_name}-tg", 0, 32)
  port     = local.alb_http_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    path                = local.alb_health_path
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = "200-399"
  }

  tags = merge(var.tags, { Name = "${local.alb_name}-tg" })
}

resource "aws_lb_listener" "alb_http" {
  count             = local.alb_enabled ? 1 : 0
  load_balancer_arn = aws_lb.alb[0].arn
  port              = local.alb_http_port
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = local.alb_cert_arn != null ? [1] : []

    content {
      type = "redirect"
      redirect {
        status_code = "HTTP_301"
        port        = tostring(local.alb_https_port)
        protocol    = "HTTPS"
      }
    }
  }

  dynamic "default_action" {
    for_each = local.alb_cert_arn == null ? [1] : []

    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.alb_http[0].arn
    }
  }
}

resource "aws_lb_listener" "alb_https" {
  count             = local.alb_enabled && local.alb_cert_arn != null ? 1 : 0
  load_balancer_arn = aws_lb.alb[0].arn
  port              = local.alb_https_port
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = local.alb_cert_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alb_http[0].arn
  }
}

resource "aws_lb" "nlb" {
  count                      = local.nlb_enabled ? 1 : 0
  name                       = substr(local.nlb_name, 0, 32)
  load_balancer_type         = "network"
  internal                   = try(var.nlb_config.internal, true)
  subnets                    = local.nlb_subnets
  enable_deletion_protection = false
  enable_cross_zone_load_balancing = try(var.nlb_config.cross_zone, true)
  tags = merge(var.tags, { Name = local.nlb_name })
}

resource "aws_lb_target_group" "nlb_tcp" {
  count    = local.nlb_enabled ? 1 : 0
  name     = substr("${local.nlb_name}-tg", 0, 32)
  port     = local.nlb_tcp_port
  protocol = "TCP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    protocol            = try(var.nlb_config.health_check_protocol, "TCP")
    port                = try(var.nlb_config.health_check_port, "traffic-port")
    interval            = try(var.nlb_config.health_check_interval, 30)
    healthy_threshold   = try(var.nlb_config.healthy_threshold, 3)
    unhealthy_threshold = try(var.nlb_config.unhealthy_threshold, 3)
  }

  tags = merge(var.tags, { Name = "${local.nlb_name}-tg" })
}

resource "aws_lb_listener" "nlb_tcp" {
  count             = local.nlb_enabled ? 1 : 0
  load_balancer_arn = aws_lb.nlb[0].arn
  port              = local.nlb_tcp_port
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nlb_tcp[0].arn
  }
}
