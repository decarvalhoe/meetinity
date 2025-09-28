# Kubernetes Platform Decision Record

## Managed Control Plane
- **Provider:** Amazon Elastic Kubernetes Service (EKS)
- **Region:** eu-west-1 (Ireland)

EKS is aligned with our existing AWS footprint and allows us to reuse IAM, networking and
monitoring primitives already provisioned for the platform. The `eu-west-1` region offers
three availability zones for high availability while staying close to our primary user base
in Europe.

## Implications
- Terraform code in this repository provisions all foundational infrastructure required to
  run the cluster (VPC, IAM, managed node groups, add-ons).
- Team members should request onboarding to the `meetinity-eks-admin` IAM role to obtain
  `kubectl` access (see `docs/dev-environment.md`).
- Workloads relying on managed services in other regions may incur cross-region latency; new
  services should be deployed in `eu-west-1` by default.
