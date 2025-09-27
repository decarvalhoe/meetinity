# Monitoring Stack

This folder contains the configuration used to deploy the Meetinity monitoring toolchain on the EKS cluster.

## Components

- **Prometheus Operator (kube-prometheus-stack)**: Provides Prometheus, Alertmanager, and related CRDs.
- **Grafana**: Dashboards for application and infrastructure metrics.
- **Alerting**: Routing rules and default notification templates for on-call rotations.

## Deployment Steps

1. Add the Helm repositories:

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   ```

2. Deploy or upgrade Prometheus:

   ```bash
   helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
     --namespace monitoring \
     --create-namespace \
     -f infra/monitoring/prometheus/values.yaml
   ```

3. Configure Grafana (optional override separate release). Update the ingress host in `grafana/values.yaml` before deploying:

   ```bash
   helm upgrade --install grafana grafana/grafana \
     --namespace monitoring \
     -f infra/monitoring/grafana/values.yaml
   ```

4. Apply Alertmanager rules if not managed by Helm:

   ```bash
   kubectl apply -n monitoring -f infra/monitoring/alertmanager/config.yaml
   ```

5. Import dashboards referenced in `grafana/values.yaml` and update credentials via Kubernetes secrets.

## Operations

- Use `kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring` for local access.
- Alertmanager routes to Slack (example webhook) and email by default; update secrets referenced in the config before deploying.
- ServiceMonitor and PodMonitor objects can be created per microservice to collect metrics automatically.
