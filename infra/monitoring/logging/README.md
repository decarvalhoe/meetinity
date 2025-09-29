# Logging Stack Helm Configuration

This directory centralises Helm values and supporting configuration for the Elastic (ELK) logging stack used by Meetinity.
It is designed to be used in combination with the official community Helm charts for Elasticsearch, Kibana, Logstash and Fluent Bit.

## Components

- **Elasticsearch** – Stateful storage cluster tuned for observability workloads.
- **Logstash** – Stateful pipeline that enriches cluster logs and fan-outs to long term storage.
- **Fluent Bit** – Lightweight log forwarder deployed as a DaemonSet on every node to collect container logs.
- **Kibana** – UI for querying and building dashboards on top of Elasticsearch indices.

## Installation

1. Add the required Helm repositories:

   ```bash
   helm repo add elastic https://helm.elastic.co
   helm repo add fluent https://fluent.github.io/helm-charts
   helm repo update
   ```

2. Deploy the stack using the curated values:

   ```bash
   helm upgrade --install elasticsearch elastic/elasticsearch -n logging -f elasticsearch/values.yaml
   helm upgrade --install logstash elastic/logstash -n logging -f logstash/values.yaml
   helm upgrade --install fluent-bit fluent/fluent-bit -n logging -f fluent-bit/values.yaml
   helm upgrade --install kibana elastic/kibana -n logging -f kibana/values.yaml
   ```

3. Ensure the `logging` namespace exists and that the service account used by Helm has permissions to create the resources described in the values.

## Workload integration

The Fluent Bit configuration deploys a privileged DaemonSet with host log directory mounts so that every workload running on the cluster has its stdout/stderr captured without code changes.
It enriches log records with Kubernetes metadata (namespace, pod, container, labels) and forwards them to Logstash over TLS.

Logstash is configured to:

- Parse container log payloads as JSON when possible.
- Normalise severity levels and timestamps.
- Fan out to Elasticsearch indices partitioned by environment (`logs-meetinity-<env>-YYYY.MM.DD`).

Kibana dashboards are pre-configured (via saved objects) to surface application, ingress and infrastructure log views; import these via the Kibana UI or automation.

Refer to `docs/observability.md` for a complete overview of the log ingestion pipeline and operational guidance.
