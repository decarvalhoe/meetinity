# GitHub Workflows

This directory contains the automation used to validate and deploy the Meetinity project.

## Continuous Integration (`ci.yml`)

The CI workflow runs on every push and pull request. It now orchestrates a broader validation matrix:

- **Build & Lint** – Installs Node.js dependencies (when a `package-lock.json` file is present) and runs the `npm run lint` script if it exists.
- **Tests** – Reuses the Node.js cache, reinstalls dependencies when necessary, and runs the configured `npm test` script.
- **Security Scan** – Runs `npm audit --production` when a lock file is available to check dependencies for known vulnerabilities.
- **Performance tests (k6)** – Executes `tests/performance/smoke.js` with Grafana k6. Threshold failures fail the workflow and the JSON summaries are uploaded as the `k6-performance-report` artifact so that run statistics can be reviewed offline.
- **OWASP ZAP baseline scan** – Launches a lightweight active scan against the target URL (configurable through the `ZAP_TARGET_URL` repository/organization variable) and stores the resulting HTML/JSON bundle as `zap-baseline-report`.
- **Trivy filesystem scan** – Scans the repository contents for vulnerable dependencies and packages. Findings are exported as `trivy-report.json` and shared via the `trivy-vulnerability-report` artifact.

Each job uses the `actions/setup-node` cache integration so that Node.js dependencies are restored automatically between runs. Reports produced by the new performance and security stages are retained as workflow artifacts for traceability and regression analysis.

## Continuous Delivery (`cd.yml`)

The CD workflow promotes tagged releases through each Kubernetes environment. It triggers automatically for tags that match `release/v*` and can also be invoked manually via **Run workflow**. When dispatched manually you must provide the `version` input (for example `v1.2.3`), which is used for both the container tag and the Helm release metadata.

Container images are built from the repository root and published to GitHub Container Registry (GHCR). Helm deploys the umbrella chart at `infra/helm/meetinity` while layering per-environment overrides from `infra/helm/meetinity/values/<environment>.yaml`. Namespace policies, quotas, and other baseline resources live under `infra/kubernetes/environments/<environment>/namespace.yaml`; the workflow applies these manifests before running Helm so operators should update them when adjusting limits or admission controls.

Deployments run sequentially—`dev` → `staging` → `prod`—so a failure in an earlier environment blocks promotion to the next stage. Each deployment executes a blue/green upgrade via Helm by setting `global.rolloutStrategy=blueGreen` (overridable through environment-specific variables described below). If the upgrade fails at any point, the workflow automatically runs `helm rollback` to restore the last successful revision and prevent partial rollouts.

### Required secrets and variables

| Name | Type | Description |
|------|------|-------------|
| `AWS_ACCESS_KEY_ID` | Secret | IAM user or role credentials with permissions for building/pushing images and interacting with the target EKS cluster. |
| `AWS_SECRET_ACCESS_KEY` | Secret | Secret access key paired with `AWS_ACCESS_KEY_ID`. |
| `AWS_REGION` | Variable or Secret | AWS region hosting the EKS cluster (for example, `eu-west-1`). |
| `EKS_CLUSTER_NAME` | Secret or Variable | Name of the Amazon EKS cluster targeted by the deployments. |
| `GHCR_READER_USERNAME` | Secret | Service account username for the GHCR pull secret created inside each namespace. |
| `GHCR_READER_TOKEN` | Secret | Token with `read:packages` scope used by the cluster to pull images from GHCR. |

The workflow also expects the environment manifests referenced at `infra/kubernetes/environments/<environment>/namespace.yaml` (dev, staging, prod) to exist so that namespace configuration can be applied as part of each deployment.

### Optional configuration

| Name | Type | Description |
|------|------|-------------|
| `GHCR_RETENTION_TOKEN` | Secret | Fine-scoped PAT with `read:packages`, `write:packages`, and `delete:packages` used by the retention workflow when deletions require elevated privileges. |
| `DEV_DEPLOYMENT_STRATEGY` / `STAGING_DEPLOYMENT_STRATEGY` / `PROD_DEPLOYMENT_STRATEGY` | Variable | Override the default `blueGreen` strategy passed to the Helm chart for each environment (for example `canary`). |
| `K6_TARGET_URL` | Variable | Custom endpoint for the k6 smoke test job; defaults to `https://test-api.k6.io/public/crocodiles/1/`. |
| `ZAP_TARGET_URL` | Variable | Override the default target scanned by the OWASP ZAP baseline job. |

If your project uses a custom Dockerfile path, release name, or chart path, update the environment variables defined at the top of `cd.yml` (defaults: `IMAGE_NAME=api-gateway`, `CHART_PATH=infra/helm/meetinity`, `VALUES_PATH=infra/helm/meetinity/values`).

For production environments, prefer using short-lived credentials with GitHub's OpenID Connect (OIDC) integration and an assumable IAM role instead of long-lived access keys.

## Registry retention (`ghcr-retention.yml`)

The registry retention workflow runs weekly (and on-demand) to prune GHCR package versions:

- Keeps the latest 30 branch build tags (`branch-shortSHA`).
- Preserves any version that also carries release or semantic tags.
- Deletes orphaned versions with no tags.

By default the workflow uses the repository `GITHUB_TOKEN`. Supplying `GHCR_RETENTION_TOKEN` as an organization secret grants the `delete:packages` scope when stricter registry policies are in place.

