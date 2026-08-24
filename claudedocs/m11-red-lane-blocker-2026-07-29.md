---
title: "M11 rename BLOCKED — services/task-orchestrator and services/dopecon-bridge are DCP-RED-MERGE-SEAM-0001 red-lane paths"
date: 2026-07-29
status: blocker (requires canonical-writer / operator action)
related: claudedocs/m11-workflow-api-rename-consumer-sweep-2026-07-29.md, claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md §10.2 (rewritten M11)
---

# M11 rename — blocked on the red lane

## What happened

Attempting to execute M11's "one bounded packet, behavior preserved" rename of the FastAPI
`task-orchestrator` service (:8000) to `dopemux-workflow-api`, `services/task-orchestrator/app/main.py`
edits were **hard-blocked** by the `PreToolUse` hook (`.claude/hooks/dcp_surface_guard.py`, dispatched via
`src/dopemux/claude/native_hooks.py`). Confirmed programmatically:

```python
from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS
# services/task-orchestrator/.*  -> BLOCKED
# services/dopecon-bridge/.*     -> BLOCKED
# (also blocked: services/dope-context/*, services/working-memory-assistant/*,
#  docker/mcp-servers-source/conport/*, src/conport/*, and the DCP-RED-MERGE-SEAM-0001
#  originals: queue_drain.py execute seam, batch_resolve_and_merge.py, .github/workflows/*,
#  scripts/dopetask, scripts/taskx)
```

This is `DCP-RED-MERGE-SEAM-0001` — documented in `docs/03-reference/dcp/README.md` and
`.claude/CLAUDE.md` (H1 hook: "PreToolUse hard-deny for DCP-RED-MERGE-SEAM-0001 paths... contract
surfaces") and AGENTS.md's "Contract-sensitive surfaces... require canonical-writer inspection before
editing." This is a deliberate, intentional guardrail — not a bug, and not something to route around
(no `--no-verify`, no editing-around-the-hook).

## Why a partial rename is worse than no rename

The M11 checklist requires renaming the identifier in multiple places together:
`compose.yml` service key/container_name, `services/registry.yaml`, `app/main.py`'s `SERVICE_NAME` and
`service=` health-payload labels, and the Prometheus metric prefixes — all inside
`services/task-orchestrator/`, which is entirely red-lane blocked.

Renaming ONLY the outward-facing identity (`compose.yml` service key, `container_name`,
`services/registry.yaml`) while the service's own internals keep self-reporting
`service="task-orchestrator"` in health/metrics JSON would create a **third**, worse naming
inconsistency — external DNS/container says `dopemux-workflow-api`, the service's own health
payload and Prometheus metrics still say `task-orchestrator`. That is a strictly worse state than
today's single, well-documented "shadow twin on :8000" confusion. **Not executing the rename is the
correct call here, not a workaround.**

## What IS safe and was NOT done (deliberately, to keep the packet atomic)

Everything on the M11 checklist that lives outside `services/task-orchestrator/` and
`services/dopecon-bridge/` is editable — `compose.yml`, `services/registry.yaml`,
`src/dopemux/commands/mcp_commands.py:400`, `tests/unit/test_task_orchestrator_runtime_config.py`,
`tests/unit/pm/test_pm_route_contracts.py`, `services/adhd_engine/config.py` +
`core/engine.py` (bare-DNS default), `.vibe/config.toml`, and the docs. These were deliberately **not**
touched either, even though they're individually editable, because the design's own M11 spec requires
"one bounded packet, behavior preserved" — partially renaming the compose/registry/consumer layer
while the service's own identity strings stay `task-orchestrator` internally would be the same class of
inconsistency described above, just distributed differently. Doing the edit-able 90% now and leaving the
red-lane 10% as a dangling TODO would produce a half-renamed system that is harder to reason about than
the current fully-consistent (if confusingly-named) one.

## What unblocks this

Per AGENTS.md's own governance principle, contract-sensitive surfaces require **canonical-writer
inspection before editing** — this reads as a human/operator review step, not an automated bypass
mechanism. Options, for the operator to choose:

1. **Canonical-writer session**: run this exact rename (see the full checklist in
   `claudedocs/m11-workflow-api-rename-consumer-sweep-2026-07-29.md` §(c)) through whatever process is
   the intended canonical-writer path for `services/task-orchestrator/**` and
   `services/dopecon-bridge/**` (not identified in this investigation — likely an operator-run session
   with the red lane consciously overridden, or a dedicated skill/tool this session doesn't have
   visibility into).
2. **Narrow the red lane**: if `services/task-orchestrator/**` and `services/dopecon-bridge/**` were
   added to `FORBIDDEN_PATHS` for a different original reason (the DCP read-only facade's data
   surfaces) that doesn't actually apply to a same-behavior identifier rename, an operator could
   evaluate narrowing the rule — out of scope for this session to judge unilaterally.
3. **Defer M11 entirely** until a future session/operator context has the right authority — the
   consumer-sweep evidence (already committed) remains valid and doesn't go stale; the shadow-twin
   confusion this rename fixes is already extensively documented and worked around elsewhere (every
   doc/script in this repo that mentions `:8000` now carries a "not the MCP surface" disclaimer per
   PR #1150's repair rounds).

**Recommendation: option 3 for now.** The rename is a hygiene improvement, not a live bug — every
consumer already has working defaults (env-var-overridable), and the confusion it fixes is already
mitigated by the extensive disclaimers added throughout PR #1150. Nothing is broken by waiting.
