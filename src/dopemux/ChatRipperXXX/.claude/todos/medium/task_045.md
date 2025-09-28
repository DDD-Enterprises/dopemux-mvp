## Task: Progressive Command Consolidation 48→24 Rollout with Safe Migration and Feedback
- **ID**: 20250906-185622
- **Priority**: Medium
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [33], [35]

### Description
Design and implement a staged consolidation (shadow → cohort → default) that maps 48 commands to 24 canonical actions using static mappings, targeting a 25% reduction in duplication while preserving backward compatibility and collecting user feedback.

### Implementation Details
Scope and goals:
- Consolidate 48 overlapping/duplicative commands into 24 canonical actions (48→24) using the static inventory/mapping from Task 35 and canonical maps/rules from ConfigManager (Task 33).
- Achieve at least a 25% reduction in effective command duplication without breaking existing workflows, with explicit user feedback capture and a rapid rollback path.

Key components:
1) Consolidation data model (ConfigManager integration)
- Extend ConfigManager schemas (Task 33) with a versioned ConsolidationRules spec:
  - canonical_actions: [{id, name, description, handler_ref, introduced_in, version}]
  - aliases: [{alias, canonical_id, deprecates?: bool, since_version, planned_removal_version?: str, help_redirect?: str}]
  - rollout: {version, stages: [shadow, cohort, default], flags: {enabled, shadow_only, cohort_percentage, kill_switch}, cohorts: {assignment_seed, buckets}}
  - migration_notes: [{canonical_id, from: [aliases], risk_level, test_cases: [..]}]
  - telemetry: {event_names, sampling, local_store_path}
- Store as deterministic static config (no runtime mutation) and snapshot checksums to detect drift.

2) Command Router and Compatibility Layer
- Implement CommandRouter in src/commands/consolidation/router.py:
  - route(input_cmd: str, context) -> CanonicalActionInvocation
  - Uses Task 35 mapping to resolve aliases → canonical_id; preserves all original arguments/options.
  - Emits Telemetry events: Consolidation.Routed, Consolidation.Fallback, Consolidation.WarningShown, Feedback.Provided.
  - In shadow stage, resolves and logs the canonical target but executes the original handler (no behavior change).
  - In active stages, executes canonical handler, logging alias_used=true and showing a brief deprecation notice with a link/--help redirect.
- Backward compatibility guarantees:
  - All legacy aliases remain accepted through the entire rollout; behavior-parity tests required.
  - Kill switch flag forces passthrough to legacy handlers.

3) Staged rollout controller
- Implement ConsolidationController in src/commands/consolidation/rollout.py:
  - Reads ConsolidationRules from ConfigManager (Task 33).
  - Stages:
    - Stage 0: Shadow (100%). Log-only mapping. No user-facing changes aside from optional subtle notices when --verbose.
    - Stage 1: Cohort (e.g., 20–50%). Alias calls execute canonical handlers with deprecation notices and auto-help redirect; non-cohort users remain in shadow.
    - Stage 2: Default (100%). Canonical by default; aliases remain supported. If metrics regress or error spikes occur, auto-revert to Stage 0 via kill switch.
  - Cohort assignment: deterministic hash(user_id or workspace_id, assignment_seed) to ensure stable bucket membership.

4) UX feedback capture and surfaces
- Add non-intrusive prompts after first N remaps per user/session: "Was this command behavior expected? [y/N]" (CLI) or inline toast with thumbs up/down (UI).
- Store feedback and minimal context locally (SQLite or JSONL) in a privacy-preserving manner: no PII, only alias, canonical_id, exit_code, duration, thumbs, optional freeform comment.
- Provide a feedback CLI: chatx feedback export --since=.. to review aggregated results.

5) Metrics and success criteria
- Define duplication_reduction metric: 1 - (unique_effective_actions_post / unique_effective_actions_pre). Target ≥25%.
- Track error_rate_delta, help_open_rate, re-run_rate (same command re-run within 2m), and satisfaction_rate (thumbs up ratio).
- Success gate for advancing stages: duplication_reduction ≥25%, error_rate_delta ≤ +0.5 p.p., satisfaction_rate ≥75%, p95 latency change ≤ +5%.

6) Safe migration and rollback
- One-line kill switch: config flag rollout.flags.kill_switch=true.
- Versioned rules with monotonic version numbers; on revert, router respects previous version mapping.
- Clear deprecation window settings; do not remove aliases in this task—only consolidate execution paths.

7) Documentation and ops
- Update help/usage to display canonical action first with alias badges.
- Provide a migration doc with before→after examples for all 48→24 clusters.
- Add release notes and a runbook for toggling stages and exporting feedback.

Implementation notes:
- Use existing static mapping from Task 35; do not recrawl/learn at runtime.
- Keep routing latency under 1 ms per invocation (pure table lookup and normalized matching).
- Ensure deterministic behavior across runs via ConfigManager snapshots and seeded cohorting.
- Provide JSON schemas for telemetry payloads and feedback records for downstream analytics.


### Test Strategy
Unit tests:
- Router resolution: For every alias in the 48→24 plan, assert alias maps to the correct canonical_id; arguments/options preserved; help redirect strings populated when configured.
- Shadow mode: Verify original handlers execute while Routed events are logged and no user-facing deprecation is shown by default.
- Active stages: In cohort/default stages, assert canonical handler is invoked, deprecation notice appears once per session (rate-limited), and exit codes/outputs match legacy behavior.
- Kill switch: When enabled, verify passthrough to legacy handlers with no consolidation side effects.
- Deterministic cohorting: Given a fixed assignment_seed and user_id/workspace_id, bucket assignment is stable across runs.

Integration tests:
- Stage transitions: Simulate config toggles from shadow → cohort (20%) → default; verify cohort coverage percentages within ±2% on synthetic user IDs and that non-cohort users remain unaffected in Stage 1.
- Backward compatibility: Run a suite of representative commands per alias and canonical action; assert identical outputs, side effects, and exit codes pre- and post-consolidation.
- Telemetry and feedback: Trigger routed and fallback events; submit thumbs up/down and optional comments; assert they are persisted, schema-valid, and exportable via CLI.
- Performance: Measure routing overhead; assert p95 < 1 ms for 10k invocations.
- Safety and rollback: Introduce a synthetic regression (e.g., canonical handler raises); assert health signals trigger revert (or simulate toggling kill switch) and system returns to shadow behavior.

Metrics validation:
- Compute duplication_reduction using precomputed "pre" baseline (from Task 35 inventory) vs consolidated routing; assert ≥25% reduction.
- Error rate and latency deltas remain within thresholds defined in details.

Documentation and UX:
- Snapshot tests for help output: canonical actions listed first with alias badges and deprecation notes for Stage 1+.
- Validate migration guide includes all 48→24 mappings with accurate examples.

### Migration Notes
- Originally Task ID: 45
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: medium
- Status mapping: pending
- Dependencies: [33, 35]

### Related Files
- Original: .taskmaster/tasks/tasks.json
