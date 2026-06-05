# Multi-Project Registry Contract

## 1. Schema
The registry tracks projects by a unique `project_id`.

## 2. Validation Rules
- All incoming requests must supply a valid `project_id` (except `list_projects`).
- If `project_id` is missing or invalid, the facade rejects the request.

## 3. Eligibility vs Exposure
- `dopemux init` provides eligibility for a workspace.
- Explicit approval in the registry configuration is required for exposure via the facade.

## 4. Resolver Flow
- Request `project_id` is passed to the resolver.
- Resolver checks registry and retrieves the canonical path (resolving symlinks).
- Path is validated against the safe-paths allowlist.
