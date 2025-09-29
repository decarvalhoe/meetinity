# Cloud Operations Playbook

This document captures the operational procedures for the managed AWS infrastructure supporting Meetinity. It complements the infrastructure-as-code definition located in `infra/terraform` and outlines how the new CDN, load balancers, backup policies, and cost controls are run in production.

## Static Assets CDN

The Terraform stack provisions an S3 bucket secured behind an Amazon CloudFront distribution. When enabled via the `static_assets` variable set, the module creates:

- A private S3 bucket dedicated to immutable static assets.
- A CloudFront distribution with HTTPS enforced, compression enabled, and an optional ACM certificate for custom domains.
- Access controls that restrict origin access to the CloudFront identity.

**Operational guidance:**

1. Upload immutable front-end bundles or media assets to the bucket output in `static_assets_bucket_name`.
2. Invalidate cached objects after deployments with:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id $(terraform output -raw static_assets_distribution_id) \
     --paths '/*'
   ```
3. Integrate the distribution hostname (`static_assets_cdn_domain`) with DNS by creating the appropriate CNAME/ALIAS records.
4. Enable access logs by providing a logging bucket in `static_assets.logging_bucket`.

## Shared Load Balancers

Two shared load balancers are created to front workloads that sit outside Kubernetes ingress controllers:

- **Application Load Balancer (ALB):** Internet-facing by default, with HTTP → HTTPS redirection when an ACM certificate is provided. Traffic is forwarded to an IP-based target group for integration with services running on EKS or EC2. The DNS name is exported as `shared_alb_dns_name`.
- **Network Load Balancer (NLB):** Internal by default, exposing a TCP listener for latency-sensitive services (e.g. gRPC or MQTT). The DNS name is exported as `shared_nlb_dns_name`.

**Operational guidance:**

- Register Kubernetes services through the AWS Load Balancer Controller or attach IP targets manually to the published target group ARNs when required.
- Update security policies for the ALB by adding rules to the security group (`${environment}-shared-alb-sg`).
- Use the DNS names directly in Route 53 records or private DNS zones.

## Backup and Recovery

AWS Backup is configured to orchestrate daily snapshots for the Aurora PostgreSQL cluster and any additional ARNs passed in `backup_config.additional_resource_arns`.

**Daily job:**

- Scheduled with the expression `cron(0 3 * * ? *)` (03:00 UTC).
- Snapshots are retained for 35 days by default; adjust with `backup_config.delete_after`.

**Disaster recovery procedure:**

1. Identify the most recent healthy recovery point in the AWS Backup console for the `aws_backup_vault_arn` output.
2. Start a restore job targeting a new cluster or the existing cluster after isolating workloads.
3. Once restored, update connection strings in Kubernetes secrets using `infra/scripts/deploy.sh` to repoint to the new endpoint.
4. Run application smoke tests and, when stable, decommission the compromised cluster.

Document any restore activities in the incident log and review retention requirements quarterly.

## Cost Monitoring

Cost governance leverages AWS Budgets. When `cost_monitoring.enabled` is true, Terraform creates a monthly budget with notification emails defined in `cost_monitoring.notification_emails`.

**Operational guidance:**

- Subscribe finance and platform leads to the budget notifications.
- Review cost and usage trends weekly in AWS Cost Explorer, applying the same cost allocation tags defined in Terraform (`Environment`, `Project`).
- Adjust the monthly limit (`cost_monitoring.budget_limit`) in environment-specific `.tfvars` files as the footprint grows.
- Track anomalies from Cost Explorer within the same budget view to correlate spikes with deployments.

## Runbook Updates

- Re-run `infra/scripts/deploy.sh <env>` after modifying any of the above modules to ensure outputs and Kubernetes secrets stay in sync.
- Store validated recovery steps and test results alongside this document to maintain an auditable history.
