output "alb_arn" {
  description = "ARN of the shared Application Load Balancer."
  value       = try(aws_lb.alb[0].arn, null)
}

output "alb_dns_name" {
  description = "DNS name of the shared Application Load Balancer."
  value       = try(aws_lb.alb[0].dns_name, null)
}

output "alb_target_group_arn" {
  description = "ARN of the ALB target group forwarding HTTP traffic."
  value       = try(aws_lb_target_group.alb_http[0].arn, null)
}

output "nlb_arn" {
  description = "ARN of the shared Network Load Balancer."
  value       = try(aws_lb.nlb[0].arn, null)
}

output "nlb_dns_name" {
  description = "DNS name of the shared Network Load Balancer."
  value       = try(aws_lb.nlb[0].dns_name, null)
}

output "nlb_target_group_arn" {
  description = "ARN of the NLB target group forwarding TCP traffic."
  value       = try(aws_lb_target_group.nlb_tcp[0].arn, null)
}
