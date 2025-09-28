# GitHub Workflows

This directory contains the automation used to validate and deploy the Meetinity project.

## Continuous Integration (`ci.yml`)

The CI workflow runs on every push and pull request. It executes three independent jobs:

- **Build & Lint** – Installs Node.js dependencies (when a `package-lock.json` file is present) and runs the `npm run lint` script if it exists.
- **Tests** – Reuses the Node.js cache, reinstalls dependencies when necessary, and runs the configured `npm test` script.
- **Security Scan** – Runs `npm audit --production` when a lock file is available to check dependencies for known vulnerabilities.

Each job uses the `actions/setup-node` cache integration so that Node.js dependencies are restored automatically between runs.

## Continuous Delivery (`cd.yml`)

The CD workflow is triggered on pushes to the `main` branch. It builds and tags a Docker image, pushes it to Amazon ECR, and then deploys the Helm chart located at `infra/helm/api-gateway` to the target EKS cluster.

The workflow expects the following secrets/variables to be defined in the repository (or organization) settings:

| Name | Type | Description |
|------|------|-------------|
| `AWS_ACCESS_KEY_ID` | Secret | IAM access key with permissions for ECR (push) and EKS (update kubeconfig / deploy). |
| `AWS_SECRET_ACCESS_KEY` | Secret | Secret access key paired with `AWS_ACCESS_KEY_ID`. |
| `AWS_REGION` | Variable or Secret | AWS region for both ECR and EKS resources (for example, `eu-west-1`). |
| `ECR_REGISTRY` | Secret or Variable | Fully qualified ECR registry URL (e.g. `123456789012.dkr.ecr.eu-west-1.amazonaws.com`). |
| `EKS_CLUSTER_NAME` | Secret or Variable | Name of the Amazon EKS cluster targeted by the deployment. |
| `K8S_NAMESPACE` | Secret or Variable | Kubernetes namespace where the chart should be installed/updated. |

### Optional configuration

If your project uses a custom Dockerfile path, Helm release name, or chart path, update the environment variables defined at the top of `cd.yml` (defaults: `IMAGE_NAME=api-gateway`, `CHART_PATH=infra/helm/api-gateway`).

For production environments, prefer using short-lived credentials with GitHub's OpenID Connect (OIDC) integration and an assumable IAM role instead of long-lived access keys.

