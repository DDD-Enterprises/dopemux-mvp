## Task: Integrate Smart Hooks Phase 1 enforcement into EmbeddingProvider pipeline
- **ID**: 20250906-185622
- **Priority**: Medium
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [3], [5]

### Description
Wire Enhanced Token Budget Management and Adaptive Security Model into the embedding workflow. Enforce per-request budgets and context-aware security on every embed call, standardize violations as RFC-7807 problems, and emit audit/metric events to existing dashboards.

### Implementation Details
Scope:
- Apply Smart Hooks Phase 1 (token budget management, adaptive security, pattern tracking, audit trails, real-time dashboards) to all embedding requests by wrapping the EmbeddingProvider chain.

Design/Implementation:
- SmartHookedProvider wrapper:
  - Create SmartHookedProvider(EmbeddingProvider) that decorates any concrete provider and intercepts embed() calls.
  - Inject via the provider registry (Task 5): when a provider is selected, return a wrapped instance. Ensure fallbacks are wrapped as well.
- Context propagation:
  - Define a RequestContext data class (tenant_id, user_id, project_id, purpose, data_sensitivity, allow_cloud_override, correlation_id, request_source) and propagate via contextvars to avoid mutating method signatures. Provide helpers set_request_context()/get_request_context().
- Preflight: Token budget enforcement
  - Policy model: per-tenant/project rules for max_tokens_per_request, max_tokens_per_item, batch_size_limit, truncation_strategy (truncate|split|reject), dry_run flag, and overflow_action (reject|fallback_local|truncate).
  - Token estimation: pluggable tokenizer interface; default to tiktoken or fast tokenizer; compute estimated tokens per item and total. Cache estimates per text hash within request scope to avoid recomputation.
  - Apply policy: if over limits, execute configured overflow_action. If truncate, apply safe truncation preserving UTF-8 boundaries; if split, split batch into smaller chunks consistent with provider max batch size.
- Preflight: Adaptive security checks
  - Rules: allow_cloud gating, data residency (e.g., region=EU only), sensitivity gating (block PII in cloud), time-of-day/role-based constraints.
  - Provider compatibility: validate selected provider against rules (e.g., is_cloud, region, residency guarantees). If incompatible and fallbacks exist (Task 5), attempt next compatible provider. If none, raise policy violation.
- Around-call: pattern tracking
  - Record request shape (batch size, token estimate distribution, provider/model_id, input_type). Detect anomalies (sudden spikes) and tag audit events with anomaly flags.
- Post-call: audit + metrics emission
  - Emit structured audit events for allow/deny, truncations/splits, provider selected, policy_id, enforcement outcomes, token_estimate, correlation_id, and reason codes. Reuse the existing audit bus and dashboard pipeline; add backpressure-safe, async, non-blocking publish (bounded queue + drop-oldest with WARN if saturated).
  - Emit counters (requests_allowed/denied), histograms (estimated_tokens_per_item), gauges (current budget utilization). Include per-tenant and per-provider dimensions.
- Error normalization (ties to Task 3)
  - Map enforcement failures to RFC-7807 ProblemDetails with types:
    - type: about:quota/exceeded, title: Token budget exceeded, status: 429 or 413
    - type: about:security/forbidden, title: Policy violation, status: 403
    - type: about:policy/unsupported-provider, title: No compliant provider available, status: 503 or 424
  - Include instance (correlation_id) and safe details; strip PII and secrets.
- Configuration and rollout
  - Central config under settings.smart_hooks.* with live reload support if available. Support per-environment defaults and dry_run to observe impact without blocking.
  - No-op mode when disabled; wrapper delegates directly to underlying provider.
- Performance/concurrency
  - Ensure O(1) overhead per item for checks. Batch compute token estimates. Use asyncio primitives to avoid blocking. Avoid repeated policy fetches by caching per request.
- Telemetry/Debugging
  - Add debug logging (opt-in) with redaction. Include correlation_id in all logs and audit events.

Migration/Compatibility:
- Backward compatible: if Smart Hooks disabled, behavior unchanged.
- Fallback chain remains effective; this task only constrains provider eligibility based on policy.

Security/Privacy considerations:
- Do not emit raw texts in audit or error details. Only stemmed statistics and hashed identifiers where needed.
- Respect allow_cloud and residency gates strictly before any network calls.

### Test Strategy
Unit tests:
- Budget enforcement
  - Given a policy with max_tokens_per_item=100, item of ~150 tokens with truncation_strategy=truncate => verify text is truncated and embed() called once with truncated text.
  - Given overflow_action=reject => verify embed() not called and RFC-7807 problem returned with type about:quota/exceeded, correct status, correlation_id propagated.
- Security policy
  - Context allow_cloud=False and selected provider marked is_cloud=True with available local fallback => verify fallback chosen; if no fallback, verify RFC-7807 about:security/forbidden.
  - Residency rule mismatch => verify denial with proper type and audit event includes reason_code=residency_violation.
- Fallback integration
  - Primary incompatible, secondary compatible => verify SmartHookedProvider chooses secondary and emits audit event provider_selected=secondary.
- RFC-7807 mapping
  - Verify ProblemDetails fields (type, title, status, detail redacted, instance=correlation_id) match Task 3 model and helpers. Snapshot test JSON.
- Audit/metrics
  - Mock audit bus; assert events emitted on allow/deny/truncate with required fields. Metrics counters/histograms updated with expected labels.
- Context propagation
  - Verify contextvars carry RequestContext across awaits; correlation_id appears in audit and error.
- Performance
  - Benchmark wrapper overhead on small batches (e.g., 8 items) to ensure added latency < X ms (configurable threshold) compared to bare provider.

Integration tests:
- Wrap a fake provider; send mixed batch exceeding total budget; with split strategy => verify multiple provider calls with correct chunk sizes and consistent correlation_id across audit events.
- Concurrency
  - Launch 50 concurrent embed() calls under same tenant; ensure no race conditions, consistent policy application, and no duplicate audit events per call.
- Dry-run mode
  - With dry_run=true, over-budget requests should pass through while still emitting audit warnings; ensure no RFC-7807 errors returned.

Security/privacy tests:
- Ensure raw text content never appears in audit events or ProblemDetails by scanning emitted payloads for sent strings.

Config reload test:
- Change policy at runtime (e.g., toggle allow_cloud) and verify subsequent requests honor the new setting without restart.

### Migration Notes
- Originally Task ID: 44
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: medium
- Status mapping: pending
- Dependencies: [3, 5]

### Related Files
- Original: .taskmaster/tasks/tasks.json
