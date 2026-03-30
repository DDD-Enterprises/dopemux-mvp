---
id: container-build-fallback-plan
title: Container Build Fallback Plan
type: reference
owner: '@hu3mann'
---
# Plan: Container Build Fallback

## Context
The CI container build job fails for multiple images (frontend, backend, orchestrator, etc.) because it attempts to pull hardened images from `dhi.io` (e.g., `dhi.io/python:3.11-slim`, `dhi.io/node:18-alpine`). 
When the `DHI_TOKEN` GitHub Secret is not provided, access is denied. Although the CI workflow correctly warns about the missing token, the subsequent `docker buildx` step proceeds to fail when it cannot pull the base images.

## Objective
Make the container build pipeline resilient to missing `DHI_TOKEN`s, allowing tests and PR checks to pass using standard public Docker Hub images as a fallback, while retaining the secure `dhi.io` registry for production builds where the token is present.

## Implementation Steps
1. **Modify `.github/workflows/containers.yml`**:
   - Locate the `Check DHI token availability` step.
   - Insert a new step immediately following it: `Fallback to public images (if DHI_TOKEN missing)`.
   - In this new step, use a conditional `if: ${{ env.DHI_TOKEN == '' }}`.
   - Run a bash command to find all Dockerfiles and dynamically strip the `dhi.io/` string from all `FROM` statements:
     ```bash
     find . -name "Dockerfile*" -type f -exec sed -i 's|dhi.io/||g' {} +
     ```

## Verification
- Run the workflow without a `DHI_TOKEN`. It should log the fallback event and successfully build using public images (e.g., `python:3.11-slim` and `node:18-alpine`).
- To fully restore hardened security builds, the repository administrator must add the `DHI_TOKEN` to the GitHub Secrets for the environment.