# Meetinity Terraform Stack

This Terraform configuration bootstraps the AWS infrastructure required to run the Meetinity platform on Amazon EKS.

## Components

- **VPC module** – Creates a multi-AZ VPC with public and private subnets, routing tables, and optional NAT gateways.
- **EKS module** – Provisions an EKS control plane, managed node group, core add-ons (VPC CNI, CoreDNS, kube-proxy, EBS CSI), and IAM roles for administrators and CSI drivers.
- **Helm releases** – Installs cert-manager (with a default self-signed issuer) and the NGINX ingress controller, wiring a default TLS certificate for new ingresses.
- **Kubernetes namespaces & storage classes** – Pre-creates logical namespaces for monitoring/security, the ingress and cert-manager system namespaces, and a default gp3 storage class backed by the AWS EBS CSI driver.
- **Static assets CDN** – Optional S3 bucket plus CloudFront distribution for hosting static web resources with HTTPS enforcement.
- **Shared load balancers** – Application and Network Load Balancers ready to accept targets from EKS/EC2 workloads.
- **AWS Backup plan** – Daily backups for the Aurora PostgreSQL cluster with configurable retention windows.
- **Cost monitoring** – Monthly AWS Budget capable of notifying stakeholders when spend exceeds thresholds.
- **Managed search domain** – Highly available OpenSearch cluster with TLS enforced endpoints for the Search Service.
- **Managed streaming (Kafka + schema registry)** – Amazon MSK brokers with TLS-only access, dedicated client security groups, and an AWS Glue schema registry for validating event contracts.

## Usage

1. Install Terraform (>= 1.5) and configure AWS credentials with rights to manage VPC, IAM and EKS resources.
2. Initialise the working directory:

   ```bash
   terraform init
   ```

3. Review and override variables in a `.tfvars` file if needed. Example `dev.tfvars`:

   ```hcl
   environment          = "dev"
   cluster_name         = "meetinity-dev"
   aws_region           = "eu-west-1"
   node_group_config = {
     desired_size   = 2
     max_size       = 4
     min_size       = 1
     instance_types = ["t3.medium"]
     disk_size      = 40
   }
   ```

4. Plan and apply:

   ```bash
   terraform plan -var-file=dev.tfvars
   terraform apply -var-file=dev.tfvars
   ```

5. Once applied, configure `kubectl`:

   ```bash
   aws eks update-kubeconfig --region eu-west-1 --name $(terraform output -raw cluster_name)
   ```

   The sensitive `cluster_auth` output also contains the endpoint and CA bundle required by automation tools. Team members should assume the `cluster_admin_role_arn` output (default `meetinity-eks-admin`) before running the command.

## State Management

Store state remotely (e.g. S3 + DynamoDB) in production by adding a backend block to `main.tf` before running `terraform init`.

## Cleanup

To destroy all resources created by this stack:

```bash
terraform destroy -var-file=dev.tfvars
```
