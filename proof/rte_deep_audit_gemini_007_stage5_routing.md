# RTE Deep Audit Stage 5: Routing, Safety, & Admission

## Routing Policy
- **Manifest:** `services/repo-truth-extractor/promptsets/v4/model_map.yaml` (v2.0).
- **Strategy:** Granular routing based on `lane_class` (e.g., `CE` for critical extraction).
- **Ladders:** Primary routes are prioritized (e.g., `gpt-5.3-codex`), with explicit `repair_routes` and `sidefill_routes` for recovery.
- **Strictness:** `strict_schema_required_primary: true` is enforced for base phases (A, H, D, C).

## Live Execution Gating
- **Consent Gate:** `DPMX_LIVE_OK_ENV=1` is mandatory for any `--execute` run.
- **Pre-Live Validator:** `validate_pre_live_gate_v25.py` is invoked for all preset-based live runs. It enforces fail-closed behavior for P0 readiness issues.
- **Auth Doctor:** Mandatory preflight check for provider availability and API key validity.

## Cost & Spend Control
- **Ledger System:** `initialize_spend_tracker` creates a dynamic run-time ledger.
- **Projected Abort:** `_check_projected_cost_limit` performs a per-partition cost estimate *before* invocation and raises `CostLimitExceededError` if the run cap is breached.
- **Abort Persistence:** Cost aborts are persisted to `COST_ABORT.json` with a dedicated `COST_ABORTED` run status.

## Verdict
Routing and Safety systems are **Architecturally Mature and Fail-Closed**. The combination of environment-gating, pre-live validation, and projected-cost-aborting provides a high degree of operational safety.
