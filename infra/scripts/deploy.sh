#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
AWS_REGION="${AWS_REGION:-eu-west-1}"
DOMAIN="${DOMAIN:-meetinity.com}"
TF_DIR="$(dirname "$0")/../terraform"
HELM_DIR="$(dirname "$0")/../helm"
MONITORING_DIR="$(dirname "$0")/../monitoring"
SECURITY_DIR="$(dirname "$0")/../security"

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

log "Deploying application charts"
for chart in api-gateway user-service matching-service event-service; do
  helm upgrade --install "$chart" "$HELM_DIR/$chart" \
    --namespace default \
    --set environment="$ENVIRONMENT" \
    --set domain="$DOMAIN"
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
