#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
AWS_REGION="${AWS_REGION:-eu-west-1}"
TF_DIR="$(dirname "$0")/../terraform"
HELM_DIR="$(dirname "$0")/../helm"
K8S_DIR="$(dirname "$0")/../kubernetes"
MONITORING_DIR="$(dirname "$0")/../monitoring"
SECURITY_DIR="$(dirname "$0")/../security"
NAMESPACE="meetinity-${ENVIRONMENT}"
HELM_VALUES_DIR="${HELM_DIR}/meetinity/values"
K8S_ENV_DIR="${K8S_DIR}/environments/${ENVIRONMENT}"
DATABASE_SECRET_NAME="platform-database"
REDIS_SECRET_NAME="platform-redis"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to parse Terraform outputs" >&2
  exit 1
fi

if [[ ! -d "$K8S_ENV_DIR" ]]; then
  echo "Unknown environment '${ENVIRONMENT}'. Expected directory ${K8S_ENV_DIR}" >&2
  exit 1
fi

if [[ ! -f "${HELM_VALUES_DIR}/${ENVIRONMENT}.yaml" ]]; then
  echo "Missing Helm values file for environment '${ENVIRONMENT}'" >&2
  exit 1
fi

function log() {
  echo "[deploy] $*"
}

log "Initialising Terraform backend"
(cd "$TF_DIR" && terraform init -input=false)

log "Applying Terraform stack"
TF_VARS_FILE="${TF_DIR}/${ENVIRONMENT}.tfvars"
if [[ -f "$TF_VARS_FILE" ]]; then
  (cd "$TF_DIR" && terraform apply -input=false -auto-approve -var-file="$TF_VARS_FILE")
else
  (cd "$TF_DIR" && terraform apply -input=false -auto-approve -var environment="$ENVIRONMENT" -var aws_region="$AWS_REGION")
fi

log "Collecting infrastructure outputs"
TF_OUTPUT_JSON="$(cd "$TF_DIR" && terraform output -json)"

DATABASE_ENDPOINT="$(echo "$TF_OUTPUT_JSON" | jq -r '.database_endpoint.value')"
DATABASE_READER_ENDPOINT="$(echo "$TF_OUTPUT_JSON" | jq -r '.database_reader_endpoint.value')"
DATABASE_PORT="$(echo "$TF_OUTPUT_JSON" | jq -r '.database_port.value')"
DATABASE_NAME="$(echo "$TF_OUTPUT_JSON" | jq -r '.database_name.value')"
DATABASE_USERNAME="$(echo "$TF_OUTPUT_JSON" | jq -r '.database_username.value')"
DATABASE_PASSWORD="$(echo "$TF_OUTPUT_JSON" | jq -r '.database_password.value')"

REDIS_PRIMARY_ENDPOINT="$(echo "$TF_OUTPUT_JSON" | jq -r '.redis_primary_endpoint.value')"
REDIS_READER_ENDPOINT="$(echo "$TF_OUTPUT_JSON" | jq -r '.redis_reader_endpoint.value')"
REDIS_PORT="$(echo "$TF_OUTPUT_JSON" | jq -r '.redis_port.value')"
REDIS_AUTH_TOKEN="$(echo "$TF_OUTPUT_JSON" | jq -r '.redis_auth_token.value')"

if [[ -z "$DATABASE_ENDPOINT" || "$DATABASE_ENDPOINT" == "null" ]]; then
  echo "Failed to obtain database endpoint from Terraform outputs" >&2
  exit 1
fi

if [[ -z "$REDIS_PRIMARY_ENDPOINT" || "$REDIS_PRIMARY_ENDPOINT" == "null" ]]; then
  echo "Failed to obtain Redis endpoint from Terraform outputs" >&2
  exit 1
fi

if [[ -z "$DATABASE_READER_ENDPOINT" || "$DATABASE_READER_ENDPOINT" == "null" ]]; then
  DATABASE_READER_ENDPOINT="$DATABASE_ENDPOINT"
fi

if [[ -z "$REDIS_READER_ENDPOINT" || "$REDIS_READER_ENDPOINT" == "null" ]]; then
  REDIS_READER_ENDPOINT="$REDIS_PRIMARY_ENDPOINT"
fi

DATABASE_URL="postgresql://${DATABASE_USERNAME}:${DATABASE_PASSWORD}@${DATABASE_ENDPOINT}:${DATABASE_PORT}/${DATABASE_NAME}"
DATABASE_READER_URL="postgresql://${DATABASE_USERNAME}:${DATABASE_PASSWORD}@${DATABASE_READER_ENDPOINT}:${DATABASE_PORT}/${DATABASE_NAME}"
REDIS_URL="rediss://default:${REDIS_AUTH_TOKEN}@${REDIS_PRIMARY_ENDPOINT}:${REDIS_PORT}"
REDIS_READER_URL="rediss://default:${REDIS_AUTH_TOKEN}@${REDIS_READER_ENDPOINT}:${REDIS_PORT}"

log "Updating kubeconfig"
aws eks update-kubeconfig --name "$(cd "$TF_DIR" && terraform output -raw cluster_name)" --region "$AWS_REGION"

log "Deploying cert-manager"
helm repo add jetstack https://charts.jetstack.io >/dev/null
helm repo update >/dev/null
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace security \
  --create-namespace \
  --set installCRDs=true \
  -f "$SECURITY_DIR/cert-manager/values.yaml"

log "Applying ClusterIssuer and network policies"
kubectl apply -f "$SECURITY_DIR/cluster-issuer.yaml"
kubectl apply -f "$SECURITY_DIR/network-policies"

log "Provisioning namespace, quotas and network policies"
kubectl apply -f "${K8S_ENV_DIR}/namespace.yaml"

log "Synchronising application secrets"
kubectl -n "$NAMESPACE" create secret generic "$DATABASE_SECRET_NAME" \
  --dry-run=client -o yaml \
  --from-literal=host="$DATABASE_ENDPOINT" \
  --from-literal=reader_host="$DATABASE_READER_ENDPOINT" \
  --from-literal=port="$DATABASE_PORT" \
  --from-literal=database="$DATABASE_NAME" \
  --from-literal=username="$DATABASE_USERNAME" \
  --from-literal=password="$DATABASE_PASSWORD" \
  --from-literal=url="$DATABASE_URL" \
  --from-literal=reader_url="$DATABASE_READER_URL" | kubectl apply -f -

kubectl -n "$NAMESPACE" create secret generic "$REDIS_SECRET_NAME" \
  --dry-run=client -o yaml \
  --from-literal=host="$REDIS_PRIMARY_ENDPOINT" \
  --from-literal=reader_host="$REDIS_READER_ENDPOINT" \
  --from-literal=port="$REDIS_PORT" \
  --from-literal=username="default" \
  --from-literal=password="$REDIS_AUTH_TOKEN" \
  --from-literal=url="$REDIS_URL" \
  --from-literal=reader_url="$REDIS_READER_URL" | kubectl apply -f -

log "Deploying umbrella chart"
helm upgrade --install "meetinity-${ENVIRONMENT}" "$HELM_DIR/meetinity" \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --values "$HELM_DIR/meetinity/values.yaml" \
  --values "${HELM_VALUES_DIR}/${ENVIRONMENT}.yaml" \
  --set-string global.environment="$ENVIRONMENT" \
  --set-string global.database.secretName="$DATABASE_SECRET_NAME" \
  --set-string global.redis.secretName="$REDIS_SECRET_NAME" \
  --wait

log "Waiting for core services to be ready"
for svc in api-gateway user-service matching-service event-service; do
  kubectl rollout status deployment/"${svc}-${ENVIRONMENT}" \
    --namespace "$NAMESPACE" \
    --timeout=5m
done

log "Deploying monitoring stack"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null
helm repo update >/dev/null
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f "$MONITORING_DIR/prometheus/values.yaml"
helm upgrade --install grafana grafana/grafana \
  --namespace monitoring \
  -f "$MONITORING_DIR/grafana/values.yaml"
kubectl apply -f "$MONITORING_DIR/alertmanager/config.yaml"

log "Deployment completed"
