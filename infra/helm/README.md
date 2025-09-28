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
  --values infra/helm/meetinity/values/dev.yaml
```

Install into a Kubernetes cluster:

```bash
helm upgrade --install meetinity infra/helm/meetinity \
  --namespace meetinity \
  --create-namespace \
  --values infra/helm/meetinity/values.yaml \
  --values infra/helm/meetinity/values/prod.yaml
```

Subchart values can be overridden by targeting their keys (e.g. `--set api-gateway.image.tag=v1.2.3`).
