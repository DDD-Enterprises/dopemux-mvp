---
id: frontend-architecture-restoration-plan
title: Frontend Architecture Restoration Plan
type: reference
owner: '@hu3mann'
---
# Plan: Restore Frontend Build and Standardize Framework

## Context
The `dopemux-frontend` container build is failing because the `Dockerfile.frontend` expects a Next.js application at the repository root, while the actual dashboard source is located in `ui-dashboard/` and configured as a Vite SPA. Furthermore, `ui-dashboard/` contains "ghost" Next.js files that conflict with the Vite configuration.

## Objective
Restore the frontend build pipeline, standardize on Vite for the dashboard (as per `package.json`), and clean up legacy/conflicting artifacts.

## Implementation Steps

### Phase 1: Framework Standardization (Standardizing on Vite)
1.  **Delete Legacy Root Frontend**: Remove the root `package.json` and `package-lock.json` which are non-functional Next.js placeholders.
2.  **Purge Ghost Next.js Files**: Delete the `ui-dashboard/app/` directory (containing `page.tsx` and `layout.tsx`) to eliminate architectural confusion. 
3.  **Verify Vite Entrypoint**: Ensure `ui-dashboard/src/index.tsx` (or similar) is the correct and functional entrypoint.

### Phase 2: Dockerfile Refactor
1.  **Rewrite `Dockerfile.frontend`**:
    - **Stage 1 (Build)**: Use `node:18-alpine`. Set `WORKDIR /app/ui-dashboard`. Copy `package.json` and `package-lock.json` from `ui-dashboard/`. Run `npm ci --legacy-peer-deps`. Copy the rest of `ui-dashboard/`. Run `npm run build`.
    - **Stage 2 (Runtime)**: Use `nginx:alpine`. Copy the `dist/` directory from the build stage to `/usr/share/nginx/html`.
    - **Configuration**: Add a basic `nginx.conf` if needed for SPA routing (fallback to `index.html`).

### Phase 3: CI/CD Integration
1.  **Update `compose.yml`**: Add the `frontend` service (if missing) or update its build context to `.`.
2.  **Update CI Pipeline**: Add a basic check in `.github/workflows/ci-complete.yml` to verify the frontend build succeeds.

## Verification
- Local build: `docker build -f Dockerfile.frontend -t dopemux-frontend:test .`
- Run container: `docker run -p 3000:80 dopemux-frontend:test` and verify dashboard loads.
- CI: Ensure the `Container Build and Publish` workflow passes for `dopemux-frontend`.
