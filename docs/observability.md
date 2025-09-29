# Observability Playbook

This document explains how Meetinity captures metrics, logs and traces, how the data is visualised, and what the on-call team must do when alerts fire.
It supplements the manifests under `infra/monitoring` and acts as a runbook for platform engineers.

## Logging pipeline

The logging stack is built around the Elastic ecosystem and is deployed with the Helm values stored in `infra/monitoring/logging/`.

1. **Collection (Fluent Bit DaemonSet)**
   - Every Kubernetes node runs a Fluent Bit pod via the DaemonSet configuration in `infra/monitoring/logging/fluent-bit/values.yaml`.
   - Fluent Bit tails `/var/log/containers/*.log`, enriches entries with Kubernetes metadata (namespace, pod, labels) and forwards structured records to Logstash over a TLS-enabled Beats/Forward output.
   - The DaemonSet tolerates control-plane taints and mounts `/var/log` and `/var/lib/docker/containers` so that all workloads are captured without requiring application changes.

2. **Processing (Logstash)**
   - The Logstash pipeline defined in `infra/monitoring/logging/logstash/values.yaml` normalises log payloads, parses JSON bodies, and derives an environment tag from namespace labels.
   - Filter stages drop chatty system namespaces (`kube-system`, `logging`) and convert timestamps to `@timestamp` so that Kibana timelines align with ingestion time.
   - Enriched events are written to daily Elasticsearch indices following the naming pattern `logs-meetinity-<environment>-YYYY.MM.DD`.

3. **Storage & Query (Elasticsearch + Kibana)**
   - The Elasticsearch cluster configured in `infra/monitoring/logging/elasticsearch/values.yaml` provides high-availability hot storage with TLS enforced.
   - Kibana, customised via `infra/monitoring/logging/kibana/values.yaml`, exposes dashboards at `https://kibana.meetinity.com` and authenticates against the shared `elastic-credentials` secret.
   - Saved objects should be version-controlled (export/import JSON) so that dashboards and index patterns can be reconstructed after a disaster.

### Kibana dashboards

Recommended dashboards:

- **Application Overview** – service-level log volume, error ratios, request latency percentiles.
- **Ingress / Edge** – aggregated NGINX Ingress logs with geo-IP enrichment to spot attack patterns.
- **Infrastructure Health** – node logs, kubelet/kube-proxy warnings, Fluent Bit delivery errors.

Store dashboard JSON exports under `infra/monitoring/logging/dashboards/` (create the folder as needed) to enable reproducible environments.

## Tracing pipeline

Distributed tracing is powered by Jaeger with OpenTelemetry instrumentation.

1. **Collector & Storage**
   - The Jaeger control-plane is deployed using the values in `infra/monitoring/jaeger/values.yaml` and persists spans into the Elasticsearch cluster shared with logging.
   - OTLP/gRPC (port 4317) and Jaeger gRPC (port 14250) receivers are enabled by default to support both modern and legacy SDKs.

2. **Service sidecars**
   - Each Meetinity service chart (`infra/helm/meetinity/charts/*`) now exposes an `observability.tracing` block.
   - When enabled (default in each service values file), the chart injects a Jaeger agent sidecar and configures application containers with standard OpenTelemetry environment variables (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_RESOURCE_ATTRIBUTES`, sampler settings, propagators).
   - Resource attributes automatically include the deployment environment via the shared helper so traces can be filtered by stage.

3. **Instrumentation guidelines**
   - Use the OpenTelemetry SDK for your language and rely on the environment variables emitted by the chart—no hard-coded endpoints.
   - For manual spans, prefer semantic conventions (`http.*`, `db.*`) to maximise auto-generated dashboard compatibility.

### Jaeger usage

- Access Jaeger Query at `https://jaeger.meetinity.com` (TLS enforced by the ingress defined in the Helm values).
- Create service-level dashboards highlighting p95/p99 latency, error rate, and trace volume by operation.
- Use trace comparison to detect regression after deployments and feed results into release notes.

## Metrics and dashboards

While this update focuses on logs and traces, Prometheus and Grafana remain the primary metrics stack (see `infra/monitoring/prometheus/values.yaml`).
Integrate log-derived alerts with Grafana by embedding Kibana panels or linking to saved searches.

Recommended Grafana dashboards:

- **Service SLO dashboards** mapping latency/error budgets across services.
- **Infrastructure saturation** – CPU/memory pressure, pod churn, and HPA/VPA actions.
- **Tracing health** – OTLP exporter errors, Jaeger collector queue depth, Fluent Bit output retries.

## Incident alerting procedures

1. **Alert routing**
   - Alertmanager (configured in `infra/monitoring/alertmanager/config.yaml`) sends pages to the on-call rotation and notifies Slack `#incident-response` for awareness.
   - Kibana watchers or Alerting rules should forward high-priority log anomalies to the same channel.

2. **On-call checklist**
   - Acknowledge the alert in Alertmanager or the paging tool within 5 minutes.
   - Check Grafana SLO dashboards to assess scope; pivot to Jaeger to determine whether latency originates upstream or downstream.
   - Use Kibana saved searches for the affected service to correlate errors with recent deployments or configuration changes.

3. **Escalation & Postmortem**
   - Escalate to the feature team if MTTA exceeds 15 minutes or the blast radius spans multiple services.
   - Capture a timeline using traces/logs screenshots and export relevant charts for the incident review.
   - File a postmortem in the knowledge base within 48 hours, linking to the dashboards and traces used during the investigation.

## Maintenance

- Rotate TLS certificates (`logstash-tls`, `kibana-tls`, `jaeger-tls`) 30 days before expiry.
- Validate Fluent Bit and Logstash upgrades in staging; pay attention to parser compatibility.
- Reindex Elasticsearch monthly to keep shard sizes consistent and archive indices older than 90 days to cold storage if retention requires.

By following this playbook, the Meetinity platform gains end-to-end observability coverage with consistent deployment artefacts and operational procedures.
