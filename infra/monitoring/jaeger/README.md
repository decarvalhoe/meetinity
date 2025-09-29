# Jaeger / OpenTelemetry Collector Helm Configuration

This directory contains baseline values for deploying a production-ready Jaeger tracing platform using the upstream Helm chart.
The deployment exposes OTLP and Jaeger-native ingestion endpoints and stores trace data in Elasticsearch so that the logging stack can be reused for retention.

## Installation

```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm upgrade --install jaeger jaegertracing/jaeger -n observability -f values.yaml
```

The `values.yaml` file configures:

- A dedicated Collector deployment with OTLP/GRPC and Jaeger gRPC receivers.
- An Agent DaemonSet for node-level sampling (optional if sidecars are used).
- Query service exposed via Kubernetes ingress.
- Storage integration with the Elasticsearch cluster provisioned under `infra/monitoring/logging`.

Sidecars for the application workloads are enabled through chart values under `infra/helm/meetinity/charts/*`.
Refer to the observability documentation for detailed wiring instructions.
