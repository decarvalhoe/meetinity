# Meetinity Helm Charts

This directory contains the umbrella chart used to deploy the Meetinity platform. The `meetinity` chart bundles service subcharts and provides shared templates for configuration, secrets, and HTTP probes.

## Structure

```
infra/helm/
└── meetinity/
    ├── Chart.yaml
    ├── values.yaml
    ├── values/
    │   ├── dev.yaml
    │   ├── staging.yaml
    │   └── prod.yaml
    └── charts/
        ├── common/          # Library chart exposing shared templates
        ├── api-gateway/
        ├── user-service/
        ├── matching-service/
        └── event-service/
```

- `charts/common` defines reusable templates for ConfigMaps, Secrets, SealedSecrets, ExternalSecrets, and HTTP probe snippets.
- Each service chart (`api-gateway`, `user-service`, `matching-service`, `event-service`) renders Deployments, Services, HPAs, and Ingress resources while consuming the shared templates.
- The top-level `values.yaml` captures global defaults. Environment-specific overrides live under `values/` and demonstrate how to integrate Vault-backed `ExternalSecret` resources and Bitnami `SealedSecret` manifests.

## Usage

Render the entire stack for a target environment:

```bash
helm dependency update infra/helm/meetinity
helm template meetinity infra/helm/meetinity \
  --values infra/helm/meetinity/values.yaml \
  --values infra/helm/meetinity/values/dev.yaml \
  --set-string global.environment=dev
```

Install into a Kubernetes cluster:

```bash
kubectl apply -f infra/kubernetes/environments/dev/namespace.yaml

helm upgrade --install meetinity-dev infra/helm/meetinity \
  --namespace meetinity-dev \
  --create-namespace \
  --values infra/helm/meetinity/values.yaml \
  --values infra/helm/meetinity/values/dev.yaml \
  --set-string global.environment=dev
```

Subchart values can be overridden by targeting their keys (e.g. `--set api-gateway.image.tag=v1.2.3`).

### Release naming convention

All rendered Kubernetes objects follow the `<service>-<environment>` naming convention. The umbrella release itself should adopt
the same suffix (e.g. `meetinity-dev`, `meetinity-staging`, `meetinity-prod`) to keep workloads, network policies, and quotas in
sync with the dedicated namespaces defined under `infra/kubernetes/environments/`.

### Secret management

The chart exposes two approaches for secret delivery:

- **Bitnami SealedSecrets** via the `sealedSecrets` arrays (shared or per-service) for storing encrypted blobs inside the Git
  repository.
- **External Secrets Operator** through the `vaultSecrets` arrays that render `ExternalSecret` resources pointing at the secret
  store defined in `global.secretStores`.

Environment overlays demonstrate both patterns. At deployment time the pipeline only needs read access to the upstream secret
store; the manifests themselves remain immutable in Git.
