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

Releases that flow through [`.github/workflows/cd.yml`](../.github/workflows/cd.yml) publish **two** tags for each container version:

- `vX.Y.Z` – semantic-release tag derived from the `release/v*` Git reference that triggered the workflow.
- `sha-<SHORT_SHA>` – immutable build tag that captures the 7-character commit SHA associated with the release.

The workflow fails fast if it cannot infer the semantic version and always pushes both tags to keep the build reproducible and auditable.

### Release promotion

Releases are promoted by creating (or dispatching) tags that match `release/v*`:

1. The `release/v*` ref is converted to the semantic version (`vX.Y.Z`) used for tagging the image.
2. The build job publishes the versioned and SHA tags to `ghcr.io/<org>/api-gateway`.
3. Subsequent jobs deploy the umbrella chart at `infra/helm/meetinity` into the `meetinity-dev`, `meetinity-staging`, and `meetinity-prod` namespaces in order, ensuring the same release version rolls through each environment.

## Publication workflow

1. GitHub Actions builds the Docker image and logs in to GHCR using the repository's `GITHUB_TOKEN` (packages: write).
2. The workflow tags the image using the scheme above and pushes both tags to `ghcr.io/<org>/api-gateway`.
3. The Kubernetes pull secret is (re)created with the organization-wide runtime credentials so that workload pods keep access to GHCR.
4. Helm upgrades the umbrella chart (`infra/helm/meetinity`) with the semantic version tag, guaranteeing reproducible rollouts across namespaces.

## Retention and purge

Automated retention is handled by the scheduled workflow `.github/workflows/ghcr-retention.yml`:

- Keeps the last **30** build images that only contain `sha-<SHORT_SHA>` tags (no semantic version).
- Preserves images that also carry semantic-release tags (`vX.Y.Z`).
- Removes orphaned container versions (no tags).
- Uses the optional `GHCR_RETENTION_TOKEN` secret when available to satisfy the `delete:packages` scope.

Manual purge procedure:

1. Trigger the "GHCR Retention" workflow manually (`workflow_dispatch`) and confirm that the job deletes the intended versions.
2. For emergency purges, run the workflow with `GHCR_RETENTION_TOKEN` present so deletions succeed even if branch builds are protected by org policies.
3. Validate that the latest semantic version and SHA tags still exist by listing package tags in the GitHub UI or via `crane ls ghcr.io/<org>/api-gateway`.
4. If additional cleanup is needed (e.g., deprecating a semantic version), delete the tag in the GitHub UI which will detach it from its container version; the retention workflow will pick up the orphaned version on the next run.

Document owners should update this guide whenever the Helm chart path, registry namespace, or tagging strategy changes.
