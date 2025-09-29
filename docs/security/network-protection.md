# Network Edge Protection

This environment provisions dedicated edge defenses for the Meetinity platform so that volumetric and application-layer attacks can be absorbed before they reach the workloads that run in the EKS cluster.

## AWS WAF web ACL

Terraform now creates an [AWS WAF v2 web ACL](../../infra/terraform/main.tf) (`aws_wafv2_web_acl.ingress`) and associates it with the ingress controller's load balancer. The web ACL uses two layers of protections:

- A global rate limit (`RateLimit` rule) that blocks any client IP exceeding the configured request budget.
- AWS managed rule groups (Common Rule Set and Known Bad Inputs) for baseline OWASP-style protections.

You can tune these rules through the [`waf_config` variable](../../infra/terraform/variables.tf). For example, update `rate_limit` to raise or lower the allowed request rate, or extend `managed_rule_groups` with additional managed packs. Setting `waf_config.enabled` to `false` disables the resource entirely.

## AWS Shield Advanced

An [`aws_shield_protection` resource](../../infra/terraform/main.tf) is attached to the same load balancer to benefit from automatic DDoS detection and response provided by AWS Shield Advanced. Extra Route53 health checks can be referenced via the [`shield_protection` variable](../../infra/terraform/variables.tf) when zonal failover needs to be coordinated.

Shield Advanced requires an active subscription on the AWS account. When it is unavailable, set `shield_protection.enabled` to `false` to prevent Terraform from attempting to manage the protection.

## Rate limiting visibility

Both the web ACL and its rules publish sampled requests and metrics to CloudWatch (see `metric_name` parameters in [`main.tf`](../../infra/terraform/main.tf)). This makes it easy to build dashboards and alarms that highlight suspicious spikes in traffic.

## External secrets consumption

Sensitive connection strings (database, Redis) and TLS certificates are no longer bundled as sealed secrets. They are fetched at runtime from Vault through External Secrets objects defined in [`infra/helm/meetinity/templates/shared-secrets.yaml`](../../infra/helm/meetinity/templates/shared-secrets.yaml) and environment-specific values files. Ensure that Vault contains the expected paths (for example `kv/data/<env>/shared/database`) before deploying.
