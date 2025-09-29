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

## Payment Service Operations

The payment service relies on External Secrets to hydrate provider credentials and on API Gateway routes for Stripe and PayPal
webhooks.

**Secret reconciliation**

1. Confirm Vault paths exported in the Terraform output `payment_service_vault_paths` match the desired secret structure.
2. Verify the ExternalSecret `payment-service-secrets` is healthy:
   ```bash
   kubectl get externalsecret payment-service-secrets -n payments -o yaml
   ```
3. To force a refresh after rotating credentials, annotate the ExternalSecret:
   ```bash
   kubectl annotate externalsecret payment-service-secrets external-secrets.io/refresh-trigger=$(date +%s) -n payments --overwrite
   ```
4. Restart the deployment to pick up the new environment variables:
   ```bash
   kubectl rollout restart deploy/payment-service -n payments
   ```

**Webhook verification**

1. Retrieve the expected callback URLs from the Terraform output `payment_service_webhook_targets`.
2. In Stripe/PayPal dashboards, ensure the webhook endpoints are subscribed to invoice, subscription, and refund events.
3. Run the CI contract tests manually when needed:
   ```bash
   pytest tests/contracts -k payment --maxfail=1 -vv
   ```
4. For sandbox validation, execute the service tests directly:
   ```bash
   pushd services/payment-service
   pytest -m "not slow" -vv
   popd
   ```

**Incident recovery**

- Use the audit log stream (`payment-service` logger in the central log system) to confirm whether requests reached the service.
- Replay failed refunds by POSTing to `/payments/refunds` with the previously stored payload. The audit log contains correlation
  IDs in case of provider timeouts.
- Coordinate with finance for manual adjustments when the provider rejects a request due to idempotency conflicts.

## Analytics Warehouse Operations

The Terraform stack provisions an optional Amazon Redshift cluster through the
`analytics_warehouse` module. When `analytics_warehouse_config.enabled` is set
to `true`, the module creates a multi-node RA3 cluster inside the private
subnets and exposes the connection metadata via the Terraform outputs
`analytics_warehouse_endpoint`, `analytics_warehouse_port`, and
`analytics_warehouse_database`.

**Retention policy**

- Automated snapshots are retained for `analytics_warehouse_config.snapshot_retention`
  days (default: 7). Adjust this value in environment `.tfvars` to meet audit
  requirements.
- The analytics service keeps raw ingestion records for 90 days and persists
  long-lived KPI snapshots inside the warehouse tables.

**Backfill procedure**

1. Trigger a backfill via the analytics service:
   ```bash
   curl -X POST "https://api.<env>.meetinity.com/api/analytics/reports/refresh" \
     -H "Authorization: Bearer <service-token>" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2024-01-01T00:00:00Z", "end_date": "2024-01-31T23:59:59Z", "force_recompute": true}'
   ```
2. Monitor the Redshift load with CloudWatch metrics `WorkloadManagement/WLMQueueLength`
   and the Prometheus gauge `analytics_warehouse_last_success_epoch` exposed by
   the analytics service (`/metrics`).
3. If a historical replay is required, restore the latest automated snapshot in
   Redshift to a temporary cluster, export the required tables, and ingest them
   via the `/ingest/batch` endpoint.
4. Update the Grafana analytics dashboard to validate KPI deltas after the
   backfill (see `infra/monitoring/grafana`).

## Runbook Updates

- Re-run `infra/scripts/deploy.sh <env>` after modifying any of the above modules to ensure outputs and Kubernetes secrets stay in sync.
- Store validated recovery steps and test results alongside this document to maintain an auditable history.
