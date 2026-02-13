---
title: "Usage Limits and Resets"
plane: "pm"
component: "dopemux"
status: "proposed"
---

# Usage Limits Tracking and Reset Strategy

## Purpose
Operational truth: quotas reset and we want auto-switch-back behaviors. Manage costs and avoid surprise bills.

## Scope
- Tracking token usage per provider.
- Defining budget limits (soft and hard).
- Handling quota resets.

## Non-negotiable invariants
1. **Fail-Safe**: If limits cannot be verified (network down), assume "Safe Mode" (Lowest Cost) or Block, depending on config.
2. **User Notification**: Never block a task silently. Always notify "Limit Reached" and offer Override.

## FACT ANCHORS (Repo-derived)

- **OBSERVED: Metrics API**: `services/task-orchestrator/app/main.py` provides `/metrics` with `tasks_orchestrated_total` and `ai_agent_dispatches_total`.
- **OBSERVED: Health Checks**: `PlaneCoordinator` monitors service health via `_check_plane_health`.
- **OBSERVED: Cognitive Load**: `OrchestrationTask` (in `models.py`) includes `cognitive_load` and `energy_required` for limit enforcement.
- **OBSERVED: Usage Tracking**: `services/task-orchestrator/app/core/sync.py` track sync events processed.
- **FUTURE: Hard Spending Caps**: Configuration exists in `settings.py` but enforcement logic is not yet observed in active service code.

## Open questions
- **Multi-Instance Aggregation**: How do we aggregate usage across concurrent instances?
  - *Resolution*: Use file locking on `usage.json` or a dedicated Usage MCP.
- **Multi-Instance Aggregation**: How do we aggregate usage across concurrent instances?
  - *Resolution*: Use file locking on `usage.json` or a dedicated Usage MCP.

## Tracking model
**Fields per Record**:
- `timestamp`: UTC
- `runner_id`: e.g., "anthropic"
- `model_id`: "claude-3-opus"
- `input_tokens`: Int
- `output_tokens`: Int
- `estimated_cost`: Float (USD)

**Aggregate View** (`limits.json`):
```json
{
  "month": "2024-02",
  "total_cost": 12.50,
  "by_provider": {
    "anthropic": 10.00,
    "openai": 2.50
  },
  "budget": 50.00,
  "reset_date": "2024-03-01"
}
```

## Policy behavior
- **Green (<50% budget)**: Prefer Best Performance (Opus/GPT-4o).
- **Yellow (50-80%)**: Warn user. Suggest switching "Meta" tasks to cheaper models.
- **Red (80-99%)**: Force "Economy Mode" (Haiku/DeepSeek/Local) for all but Critical tasks.
- **Black (100%+)**: **STOP**. Require explicit override `dmux run --auth-override`.

## Reset behavior
- **Trigger**: Date crosses `reset_date`.
- **Action**:
  - Archive `usage.json` to `usage_2024-02.json`.
  - Reset counters in memory.
  - **Auto-Switch-Back**: If currently forced to "Economy Mode" due to limits, switch back to "Performance Mode" defaults.

## Minimum implementation
- **Local Store**: Single JSON file `.dopemux/usage.json`.
- **Updates**: Updated synchronously at end of each Packet run.

## Failure modes
- **Stale Pricing**: Cost estimated using old rates.
  - *Mitigation*: Version the pricing config. Warn if > 30 days old.
- **Missing Data**: Runner doesn't report tokens.
  - *Fallback*: Estimate based on character count (approx 4 chars/token).

## Acceptance criteria
1. **Cap Test**: Set budget to $0.05. Run tasks. Ensure system warns/blocks once $0.05 is hit.
2. **Reset Test**: Manually set date to transition day. Ensure stats reset and archive is created.
