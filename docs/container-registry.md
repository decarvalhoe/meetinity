# Container Registry Strategy

This document defines how container images are published, tagged, authenticated, and retired for Meetinity.

## Hosting platform

Meetinity stores container images in **GitHub Container Registry (GHCR)** under the organization namespace (`ghcr.io/<org>/<image>`). GHCR is backed by the same identity provider as GitHub and gives us:

- First-class integration with GitHub Actions via the built-in `GITHUB_TOKEN`.
- Organization level permissions that can be delegated independently to build (write) and runtime (read) personas.
- Native lifecycle APIs for automation (retention and purge jobs).

Existing environments should migrate any ECR references to GHCR using the updated `IMAGE_URI` published by the CD workflow.

## Authentication model

Two types of tokens are required and are configured at the organization level so that repositories and runtime clusters reuse the same credentials.

| Persona | Token | Scope | Storage |
|---------|-------|-------|---------|
| CI/CD writers | Built-in `GITHUB_TOKEN` | `packages:write` | Automatically available to workflows when `permissions.packages: write` is set. |
| Runtime readers | Fine-scoped personal access token (classic) with `read:packages` or GH App installation token | Saved as org secret `GHCR_READER_TOKEN` with companion username secret `GHCR_READER_USERNAME`. |
| Retention automation | Fine-scoped PAT (classic) with `read:packages`, `write:packages`, `delete:packages` | Saved as optional org secret `GHCR_RETENTION_TOKEN`. The workflow falls back to `GITHUB_TOKEN` when the PAT is not supplied. |

Runtime clusters reference the reader token via the Kubernetes pull secret `ghcr-pull-secret`, which is managed by the CD workflow.

## Tagging scheme

Every build publishes three immutable tags so that stakeholders can pull images by deployment, environment, or semantic version:

- `app:branch-SHORT_SHA` – immutable build tag, derived from the branch name (sanitized to kebab-case) and the 7-character commit SHA.
- `app:env-release` – mutable release pointer updated on every deployment to a given environment (defaults to `production` but can be overridden with the `RELEASE_ENVIRONMENT` secret).
- `app:version` – semantic version sourced from `infra/helm/api-gateway/Chart.yaml` (`appVersion` fallback to `version`).

The CD workflow enforces this scheme by failing the pipeline when the version cannot be inferred and by pushing the three tags on every deployment.

## Publication workflow

1. GitHub Actions builds the Docker image and logs in to GHCR using the repository's `GITHUB_TOKEN` (packages: write).
2. The workflow tags the image using the scheme above and pushes all tags to `ghcr.io/<org>/api-gateway`.
3. The Kubernetes pull secret is (re)created with the organization-wide runtime credentials so that workload pods keep access to GHCR.
4. Helm is upgraded with the immutable branch/SHA tag, guaranteeing reproducible rollouts.

### Release environment override

Set the organization secret `RELEASE_ENVIRONMENT` (for example `staging`, `production`) when you need the `env-release` tag to target a specific namespace. The CD workflow lowercases and sanitizes the value to make it registry-safe.

## Retention and purge

Automated retention is handled by the scheduled workflow `.github/workflows/ghcr-retention.yml`:

- Keeps the last **30** branch build images that only contain `branch-shortSHA` tags.
- Preserves images that also carry release or semantic version tags.
- Removes orphaned container versions (no tags).
- Uses the optional `GHCR_RETENTION_TOKEN` secret when available to satisfy the `delete:packages` scope.

Manual purge procedure:

1. Trigger the "GHCR Retention" workflow manually (`workflow_dispatch`) and confirm that the job deletes the intended versions.
2. For emergency purges, run the workflow with `GHCR_RETENTION_TOKEN` present so deletions succeed even if branch builds are protected by org policies.
3. Validate that the latest `env-release` and semantic version tags still exist by listing package tags in the GitHub UI or via `crane ls ghcr.io/<org>/api-gateway`.
4. If additional cleanup is needed (e.g., deprecating a semantic version), delete the tag in the GitHub UI which will detach it from its container version; the retention workflow will pick up the orphaned version on the next run.

Document owners should update this guide whenever the Helm chart path, registry namespace, or tagging strategy changes.
