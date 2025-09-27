# Meetinity Helm Charts

This directory contains self-contained Helm charts for Meetinity microservices.

## Charts

- `api-gateway`
- `user-service`
- `matching-service`
- `event-service`

Each chart expects the following values when installed:

- `environment`: deployment stage (dev, staging, prod). Used to build ingress hostnames.
- `domain`: top-level domain appended to ingress hosts.
- `image.repository` / `image.tag`: container image configuration.
- `env`: list of environment variables propagated to the workload.

## Usage

Deploy a chart with:

```bash
helm upgrade --install api-gateway infra/helm/api-gateway \
  --namespace default \
  --set environment=dev \
  --set domain=meetinity.com
```

Override `values.yaml` as necessary for production (e.g. resource limits, ingress annotations).
