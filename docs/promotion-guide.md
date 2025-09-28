# Promotion guide

This document explains how Kubernetes namespaces, Helm releases, and the continuous delivery pipeline collaborate to promote a
build from development to staging and production.

## Namespaces, quotas, and network policies

- Each environment has a dedicated namespace manifest under `infra/kubernetes/environments/<env>/namespace.yaml` that includes:
  - Namespace creation with the `meetinity.io/environment` label used by the NetworkPolicies.
  - Resource quotas and limit ranges tailored to the expected workload footprint.
  - A default `NetworkPolicy` that allows intra-namespace traffic, inbound connections from namespaces labelled
    `networking.meetinity.io/ingress-allowed="true"`, DNS resolution via `kube-system`, and HTTPS/HTTP egress.
- Apply the manifest before deploying an environment:

  ```bash
  kubectl apply -f infra/kubernetes/environments/dev/namespace.yaml
  ```

- Label any ingress controller or shared namespace that must reach the workloads (for example `ingress-nginx`) with
  `networking.meetinity.io/ingress-allowed=true` so that traffic is not blocked by the default deny policy.

## Helm release naming and secrets

- Releases must follow the `<service>-<environment>` pattern. The umbrella chart therefore expects release names such as
  `meetinity-dev`, `meetinity-staging`, and `meetinity-prod`. Resource names (Deployments, Services, Secrets, etc.) inherit the
  same suffix to match namespace isolation and quotas.
- Secrets can be delivered in two complementary ways:
  - `sealedSecrets`: render Bitnami `SealedSecret` resources that keep encrypted payloads in Git.
  - `vaultSecrets`: render `ExternalSecret` manifests that pull material from the configured secret store (for example a Vault
    cluster) at runtime.
- Environment value files (`infra/helm/meetinity/values/<env>.yaml`) showcase both approaches. The CI/CD workflow only requires
  access to the upstream secret store and does not manipulate plain-text secrets.

## Automated promotion pipeline

Releases are promoted by tagging the repository:

1. Create a tag that matches the `release/v*` pattern (e.g. `release/v1.4.0`) or trigger the `Continuous Delivery` workflow
   manually with the desired version (e.g. `v1.4.0`).
2. The `build` job compiles the Docker image, tags it with the provided version and the commit SHA, and pushes both tags to GHCR.
3. The pipeline deploys sequentially to each environment:
   - **dev** (`meetinity-dev` / namespace `meetinity-dev`).
   - **staging** (`meetinity-staging` / namespace `meetinity-staging`).
   - **production** (`meetinity-prod` / namespace `meetinity-prod`).
4. Each deployment job:
   - Applies the namespace manifest to ensure quotas and policies are up to date.
   - Refreshes the GHCR pull secret (`ghcr-pull-secret`).
   - Upgrades/installs the Helm release with the shared and environment-specific values.
   - Waits for the four core Deployments (`api-gateway`, `user-service`, `matching-service`, `event-service`) to complete their
     rollout using the `<service>-<environment>` naming convention.

GitHub Environments (`dev`, `staging`, `production`) can be configured with reviewers to gate the progressive rollout. Because
promotions always reuse the same tag-driven container image, parity between environments is guaranteed.

## Manual interventions

If a promotion step needs to be re-run for a given environment, dispatch the workflow manually with the same version and cancel
any unneeded jobs. The build stage will detect that the image already exists and push identical tags, while the deployment stage
reuses the latest chart values.
