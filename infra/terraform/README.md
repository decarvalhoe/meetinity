# Meetinity Terraform Stack

This Terraform configuration bootstraps the AWS infrastructure required to run the Meetinity platform on Amazon EKS.

## Components

- **VPC module** – Creates a multi-AZ VPC with public and private subnets, routing tables, and optional NAT gateways.
- **EKS module** – Provisions an EKS control plane and managed node group spanning the private subnets.
- **Kubernetes namespaces** – Pre-creates logical namespaces for monitoring and security add-ons deployed with Helm.

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
   aws_region           = "eu-west-3"
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
   aws eks update-kubeconfig --region eu-west-3 --name $(terraform output -raw cluster_name)
   ```

   The sensitive `cluster_auth` output also contains the endpoint and CA bundle required by automation tools.

## State Management

Store state remotely (e.g. S3 + DynamoDB) in production by adding a backend block to `main.tf` before running `terraform init`.

## Cleanup

To destroy all resources created by this stack:

```bash
terraform destroy -var-file=dev.tfvars
```
