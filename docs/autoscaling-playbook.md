# Autoscaling & Capacity Management Playbook

This document summarizes how Meetinity collects metrics, sizes workloads, and reviews autoscaling guardrails across environments.

## Metrics pipeline
- **Prometheus Operator** scrapes workloads via ServiceMonitor/PodMonitor definitions (see `infra/monitoring/prometheus/values.yaml`).
- **Prometheus Adapter** exposes CPU/memory resources and the following custom metrics to the Kubernetes Metrics API:
  - `http_requests_per_second` (API gateway)
  - `events_processed_per_second` (Event service)
  - `matches_computed_per_second` (Matching service)
  - `user_profile_sync_per_second` (User service)
- Install/update the adapter with:
  ```bash
  helm upgrade --install monitoring-adapter prometheus-community/prometheus-adapter \
    --namespace monitoring \
    -f infra/monitoring/prometheus-adapter/values.yaml
  ```

## Baseline requests/limits
Sizing reflects load-test profiles captured in Q2 2024. Requests cover P95 usage; limits provide ~2x burst headroom.

| Service            | Environment | Requests (CPU/Mem) | Limits (CPU/Mem) |
|--------------------|-------------|--------------------|------------------|
| API Gateway        | dev         | 150m / 192Mi       | 300m / 384Mi     |
|                    | staging     | 350m / 448Mi       | 800m / 896Mi     |
|                    | prod        | 600m / 768Mi       | 1200m / 1536Mi   |
| User Service       | dev         | 120m / 192Mi       | 250m / 384Mi     |
|                    | staging     | 250m / 384Mi       | 600m / 768Mi     |
|                    | prod        | 350m / 448Mi       | 800m / 896Mi     |
| Matching Service   | dev         | 120m / 192Mi       | 250m / 384Mi     |
|                    | staging     | 250m / 384Mi       | 600m / 768Mi     |
|                    | prod        | 350m / 448Mi       | 800m / 896Mi     |
| Event Service      | dev         | 120m / 192Mi       | 250m / 384Mi     |
|                    | staging     | 250m / 384Mi       | 600m / 768Mi     |
|                    | prod        | 350m / 512Mi       | 900m / 1228Mi    |

Baseline values are encoded per environment under `infra/helm/meetinity/values/`.

## Horizontal Pod Autoscaler
- Each service chart renders an HPA targeting CPU, memory, and optional custom metrics defined in `autoscaling.metrics`.
- Aggressive scale-ups are capped via `behavior.scaleUp` policies; scale-down stabilization is set to five minutes to avoid flapping.
- Custom metric targets (e.g., requests per second) are tuned per environment and enforced in the same values files listed above.

### Review cadence
1. **Weekly:** confirm HPA events stay below 12/hour during business hours; inspect `kubectl describe hpa <release>` for anomalies.
2. **Monthly:** compare average pod utilization vs. requests with Grafana dashboards; adjust `averageUtilization` thresholds if pods idle <30%.

## Vertical Pod Autoscaler
- VPA objects are rendered per service with `updateMode: Off` to collect recommendations without mutating pods automatically.
- Enable/disable per environment via `vpa.enabled`. Prod/staging default to `true`; dev remains disabled.
- Fetch recommendations with:
  ```bash
  kubectl describe vpa <release>-api-gateway -n <env-namespace>
  ```
- Quarterly during capacity reviews, reconcile VPA recommendations with Helm values by raising requests when recommended target exceeds current request by >20% for two consecutive weeks.

## PodDisruptionBudgets
- Each service chart now renders a PodDisruptionBudget controlled through `podDisruptionBudget` values.
- Defaults:
  - dev: `minAvailable: 1`
  - staging/prod: `minAvailable: 1` (staging) / `minAvailable: 2` (prod)
- Review PDB status before planned maintenance:
  ```bash
  kubectl get pdb -n <env-namespace>
  kubectl describe pdb <release>-api-gateway -n <env-namespace>
  ```
- Update budgets during scaling changes so that `minAvailable` < current replica count to avoid blocking voluntary disruptions.

## Change management
- All resource/autoscaling adjustments flow via Pull Request with updated Helm values and links to Grafana/VPA evidence.
- Platform team owns monthly reviews; service owners sign off when changes impact their SLOs.
