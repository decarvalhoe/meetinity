# Security Add-ons

This directory defines security-focused components for the Meetinity EKS cluster.

## Contents

- **cert-manager**: Automated TLS certificate management.
- **ClusterIssuer**: Lets cert-manager issue certificates via ACME (Let's Encrypt).
- **Network Policies**: Restrict traffic between namespaces and services.

## Deployment Steps

1. Install cert-manager using Helm:

   ```bash
   helm repo add jetstack https://charts.jetstack.io
   helm repo update
   helm upgrade --install cert-manager jetstack/cert-manager \
     --namespace security \
     --create-namespace \
     --set installCRDs=true \
     -f infra/security/cert-manager/values.yaml
   ```

2. Apply the ClusterIssuer once cert-manager CRDs are ready:

   ```bash
   kubectl apply -f infra/security/cluster-issuer.yaml
   ```

3. Enforce network policies:

   ```bash
   kubectl apply -f infra/security/network-policies/
   ```

## Operations

- Update the ACME email and secret reference in `cluster-issuer.yaml` per environment.
- When new services are added, define namespace-specific policies following the provided templates.
