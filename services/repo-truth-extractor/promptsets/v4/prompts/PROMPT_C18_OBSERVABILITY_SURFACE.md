# PROMPT_C18

## Goal
Produce `C18` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract operator-visible observability surfaces across the codebase: logging configuration, structured logging adapters, metrics emitters, health endpoints, readiness checks, `/metrics` exposure, and OpenTelemetry instrumentation points.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `shared/**`
  - `config/**`
  - `configs/**`
  - `.github/workflows/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `API_DASHBOARD_SURFACE.json`
  - `SERVICE_CATALOG.partX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `OBSERVABILITY_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"OBSERVABILITY_SURFACE@v1","items":[...]}`
- Output contracts:
  - `OBSERVABILITY_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C18`
    - `id_rule`: `OBSERVABILITY_SURFACE:<stable-hash(path|surface_type|symbol|endpoint)>`
    - `required_item_fields`: `id, surface_type, mechanism, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `surface_type` enum:
  - `logger_config`
  - `structured_logger`
  - `metric_emitter`
  - `health_endpoint`
  - `readiness_endpoint`
  - `metrics_endpoint`
  - `otel_instrumentation`
- Recommended fields per item:
  - `symbol`, `service_name`, `framework`, `endpoint`, `metric_types`, `instrumentation_scope`, `status`

## Extraction Procedure
1. Load upstream inventory, partitions, entrypoint, API, and service-catalog artifacts; use the code partition as the scan surface.
2. Scan for logger initialization patterns such as `logging.getLogger`, `basicConfig`, `dictConfig`, `structlog.get_logger`, and service-specific logger factories.
3. Scan for metrics emission patterns such as `Counter(`, `Gauge(`, `Histogram(`, Prometheus client registration, StatsD emitters, and wrappers around instrumentation libraries.
4. Scan for health and readiness routes such as `/health`, `/healthz`, `/ready`, `/readiness`, and route handlers returning service state.
5. Scan for metrics exposure such as `/metrics`, Prometheus ASGI apps, middleware registration, and instrumentation bootstrap code.
6. Scan for OpenTelemetry patterns such as `opentelemetry`, tracer or meter providers, span decorators, tracing middleware, and exporter configuration.
7. Cross-reference `API_DASHBOARD_SURFACE.json` to distinguish operator-visible endpoints from internal helper functions.
8. Build deterministic IDs from `(path|surface_type|symbol|endpoint)` and attach exact evidence for every load-bearing value.
9. Normalize arrays by stable sort keys, deduplicate by ID, and emit exactly `OBSERVABILITY_SURFACE.json`.

## Evidence Rules
- Every item must include at least one evidence object with exact `path`, `line_range`, and `excerpt`.
- `path` must be repo-relative and must point to the concrete implementation or route declaration.
- `excerpt` must be exact text from the source and stay at or below 200 characters.
- If a route or metric surface is inferred from registration plus helper indirection, include both evidence sites and mark the item `status: needs_review`.

## Determinism Rules
- Do not emit timestamps, run identifiers, or environment-local absolute paths.
- Sort `items` by `(path, line_start, id)` when available, otherwise by `id`.
- Use stable enums for `surface_type` and `mechanism`; avoid free-text drift when an enum fit exists.
- Deduplicate repeated wrappers by ID and merge evidence sets deterministically.

## Anti-Fabrication Rules
- Do not claim a health or metrics endpoint exists unless a concrete route, mount, or exporter registration is evidenced.
- Do not infer OpenTelemetry usage from dependency presence alone; require code or config evidence.
- Do not label generic logging as structured logging unless a structured logger implementation is visible.
- If observability is configured only through deployment glue outside the repo, emit no item rather than inventing a repo-owned surface.

## Failure Modes
- If observability code is partially generated or imported from vendored packages, keep only directly evidenced local surfaces.
- If endpoint names are configurable, emit the configured default only when the default value is visible in code or config.
- If instrumentation helpers are reused across services, emit one item per concrete registration site plus one shared helper item when both are evidenced.
- If required fields cannot be established, keep the item with `UNKNOWN` placeholders only where evidence gaps are explicit.
