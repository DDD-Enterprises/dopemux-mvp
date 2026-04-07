# PROMPT_G5

## Goal
Produce `G5` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Extract authentication and authorization flow implementations: dependency-injection auth guards, JWT/OAuth2 token handling, permission checks, role-based access control, and session management patterns across all services.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `shared/**`
- `plugins/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- `GOV_HYGIENE_POLICIES.json`
- `GOV_POLICIES.json`
- `GOV_SECRETS_SURFACE.json`
- `API_DASHBOARD_SURFACE.json`
- `SERVICE_ENTRYPOINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `AUTH_FLOW_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"AUTH_FLOW_SURFACE@v1","items":[...]}`
- Output contracts:
  - `AUTH_FLOW_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G5`
    - `id_rule`: `AUTH_FLOW_SURFACE:<stable-hash(path|symbol|auth_type)>`
    - `required_item_fields`: `id, auth_type, mechanism, protected_symbol, enforcement_point, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "AUTH_FLOW_SURFACE:<hash>",
  "auth_type": "dependency_injection|decorator_guard|middleware|manual_check|token_validation|role_check|permission_check|session_management",
  "mechanism": "fastapi_depends|oauth2_password_bearer|http_bearer|api_key_header|api_key_query|jwt_decode|custom_middleware|manual_if_check",
  "protected_symbol": "<function or route being protected>",
  "guard_symbol": "<the auth function/class invoked, e.g. 'get_current_user'>",
  "guard_module": "<repo-relative path to guard implementation>",
  "enforcement_point": "route_parameter|decorator|middleware_stack|manual_inline",
  "token_type": "jwt|oauth2|api_key|session_cookie|bearer_opaque|none",
  "claims_extracted": ["<JWT claims accessed, e.g. 'sub', 'exp', 'roles'>"],
  "roles_required": ["<role strings if RBAC, e.g. 'admin', 'editor'>"],
  "permissions_required": ["<permission strings if fine-grained, e.g. 'tasks:write'>"],
  "fallback_behavior": "401_unauthorized|403_forbidden|redirect_login|silent_skip|custom",
  "is_optional": false,
  "bypass_conditions": "<conditions under which auth is skipped, or null>",
  "service_name": "<service name from registry.yaml>",
  "path": "<repo-relative path to auth usage site>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Auth Type Definitions
- **dependency_injection**: Auth enforced via FastAPI `Depends(get_current_user)` or similar DI pattern
- **decorator_guard**: Auth enforced via `@requires_auth`, `@login_required`, or custom decorators
- **middleware**: Auth enforced at middleware layer before route handlers execute
- **manual_check**: Inline `if not user.is_authenticated` or equivalent conditional checks
- **token_validation**: Explicit JWT decode/verify calls (e.g., `jwt.decode()`, `jose.jwt.decode()`)
- **role_check**: Role-based access control check (e.g., `if user.role != 'admin': raise 403`)
- **permission_check**: Fine-grained permission check (e.g., `if 'tasks:write' not in user.permissions`)
- **session_management**: Session creation, validation, or destruction (login/logout flows)

### Mechanism Definitions
- **fastapi_depends**: `Depends(callable)` in FastAPI route signature
- **oauth2_password_bearer**: `OAuth2PasswordBearer(tokenUrl=...)` scheme
- **http_bearer**: `HTTPBearer()` or `HTTPAuthorizationCredentials` scheme
- **api_key_header**: API key extracted from request header
- **api_key_query**: API key extracted from query parameter
- **jwt_decode**: Direct call to `jwt.decode()`, `jose.jwt.decode()`, or equivalent
- **custom_middleware**: Application-level middleware class or function
- **manual_if_check**: Inline conditional checking auth state

### Enforcement Point Definitions
- **route_parameter**: Auth injected as a route handler parameter via DI
- **decorator**: Auth checked via decorator before handler body executes
- **middleware_stack**: Auth checked in middleware before request reaches router
- **manual_inline**: Auth checked inside handler body with manual conditional logic

### Fallback Behavior Definitions
- **401_unauthorized**: Returns HTTP 401 with WWW-Authenticate header
- **403_forbidden**: Returns HTTP 403 Forbidden
- **redirect_login**: Redirects to login page/endpoint
- **silent_skip**: Silently proceeds without auth (dangerous)
- **custom**: Application-defined error handling

### Worked Example
```json
{
  "id": "AUTH_FLOW_SURFACE:f2a7c3d1",
  "auth_type": "dependency_injection",
  "mechanism": "fastapi_depends",
  "protected_symbol": "decompose_task",
  "guard_symbol": "get_current_user",
  "guard_module": "services/task-orchestrator/app/auth.py",
  "enforcement_point": "route_parameter",
  "token_type": "jwt",
  "claims_extracted": ["sub", "exp"],
  "roles_required": [],
  "permissions_required": [],
  "fallback_behavior": "401_unauthorized",
  "is_optional": false,
  "bypass_conditions": null,
  "service_name": "task-orchestrator",
  "path": "services/task-orchestrator/app/api/pm_tools.py",
  "line_range": [45, 48],
  "status": "ok",
  "evidence": [{"path": "services/task-orchestrator/app/api/pm_tools.py", "line_range": [45, 46], "excerpt": "async def decompose_task(request: DecomposeRequest, user = Depends(get_current_user)):"}]
}
```

## Extraction Procedure
1. Load upstream GOV_INVENTORY, GOV_PARTITIONS, and GOV_SECRETS_SURFACE; use governance partition as scan surface.
2. Scan for **FastAPI Depends auth**: search for `Depends(get_current_user)`, `Depends(get_api_key)`, or any `Depends()` call where the injected callable performs authentication. Record the route handler, guard function, and module path.
3. Scan for **OAuth2 schemes**: search for `OAuth2PasswordBearer(`, `OAuth2PasswordRequestForm`, `HTTPBearer(`, `HTTPAuthorizationCredentials`. Record scheme configuration (tokenUrl, auto_error).
4. Scan for **JWT token handling**: search for `jwt.decode(`, `jose.jwt.decode(`, `JWTBearer`, token validation functions. Record claims accessed, secret key source, algorithm.
5. Scan for **decorator-based auth**: search for `@requires_auth`, `@login_required`, `@permission_required`, `@roles_required` or custom auth decorators. Record decorator name and wrapped function.
6. Scan for **middleware auth**: search for middleware classes/functions that inspect `Authorization` headers, cookies, or session tokens. Record middleware registration and protected routes.
7. Scan for **role/permission checks**: search for `user.role`, `user.is_admin`, `user.permissions`, `has_permission(`, `check_role(`. Record the check, required values, and fallback behavior.
8. Scan for **session management**: search for session creation (`session[`, `request.session`), login/logout handlers, session configuration.
9. Cross-reference with `API_DASHBOARD_SURFACE.json` to identify which routes have auth and which don't — flag unprotected endpoints that handle sensitive data.
10. Build deterministic IDs using stable content keys `(path|symbol|auth_type)`.
11. Attach evidence to every item with exact excerpts showing the auth pattern.
12. Emit exactly `AUTH_FLOW_SURFACE.json` and no additional files.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent auth mechanisms, guard functions, or permission requirements.
- Do not assume auth is present because a route handles sensitive data — only record explicit auth code.
- If auth presence is ambiguous (e.g., inherited from middleware but not visible in handler), mark `status: needs_review`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not extract secret values (tokens, keys, passwords) — only extract paths, patterns, and loaders.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Dynamic auth: if auth is configured at runtime (e.g., feature flags), emit with `status: needs_review` and note the dynamic configuration.
- Transitive auth: if a function delegates to another for auth checking, record both the delegation site and the actual check, linked by evidence.
