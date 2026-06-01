"""
Orchestrator SubagentStart phase-protocol injector.

Provides one public function used by native_hooks.py:
  emit_subagent_protocol(agent_type) -> str | None
    — called from SubagentStart to inject the agent-owned-phase protocol
      into an implementation subagent at spawn time.

Dopemux-adapted port of the upstream claude-plugins/task-orchestrator
hooks/subagent-start.mjs (jpicklyk/task-orchestrator @ main). Adaptations:
  - mcp__task-orchestrator__ tool prefix (Dopemux .mcp.json),
  - Dopemux actor-ID convention (worktree-<basename>-<branch>),
  - AGENTS.md §12 proof-bundle-into-note completion rule,
  - skip read-only agent types (Explore, Plan) — they do no orchestrator
    phase work, so the protocol would be noise.

Static text only; no state, no I/O.
"""
from __future__ import annotations

from typing import Optional

# Read-only subagent types that never own an orchestrator phase. The protocol
# is skipped for these to avoid injecting irrelevant guidance.
READONLY_AGENT_TYPES = frozenset({"Explore", "Plan"})

SUBAGENT_PHASE_PROTOCOL = """\
## Agent-Owned-Phase Protocol (task-orchestrator)

**You own exactly ONE phase.** Enter it, fill its notes, then return. Do NOT advance beyond your phase.

### Phase entry

1. **Enter your phase:** `advance_item(transitions=[{itemId: "<your-item-UUID>", trigger: "start", actor: {...}}])`
   - Moves the item into your phase (queue→work or work→review).
   - The response carries `guidancePointer` (authoring instructions for the first note) and `noteProgress {filled, remaining, total}`.
   - If the item is already in your phase (`applied: false`), call `get_context(itemId="<your-item-UUID>")` instead.

### Just-in-time note progression

2. **Read guidance:** `guidancePointer` says what the schema author expects for the current note. If the response has a non-null `skillPointer`, you MUST invoke that skill via the Skill tool before filling the note — it provides the structured evaluation framework.
3. **Do the work and fill the note:** `manage_notes(operation="upsert", notes=[{itemId, key, role, body, actor}])`. If `noteProgress.total` is 1 (or absent), skip to step 6.
4. **Get next guidance:** `get_context(itemId="<your-item-UUID>")` — returns updated `guidancePointer` + `noteProgress`.
5. **Check if done:** `guidancePointer` null ⇒ all required notes filled ⇒ step 6. Otherwise repeat from step 2.

### Return

6. **Return results.** Report: (1) files changed with line counts, (2) test results, (3) blockers. Do not echo the task description back.

**CRITICAL:** Do NOT call `advance_item(trigger="start")` a second time (skips your phase). Do NOT call `advance_item(trigger="complete")` — the orchestrator owns terminal transitions, and per AGENTS.md §9/§12 the proof bundle goes INTO the `proof-bundle` note, filed in review phase before completion.

## Actor attribution (Dopemux)

Every `advance_item` transition and `manage_notes` upsert MUST carry an `actor`:
`{id: "worktree-<basename>-<branch>", kind: "subagent", parent: "<dispatching-session-id>"}`
(derive `<basename>`/`<branch>` from `git rev-parse --show-toplevel` + `git branch --show-current`).

## Subagent discipline

1. **Commit before returning.** Stage + commit your changes with a descriptive message — the orchestrator needs committed changes to squash-merge your branch.
2. **Stay in scope.** Only touch files for your assigned task. Do NOT bump versions, edit shared config, CI files, or `.taskorchestrator/config.yaml` (contract-sensitive, ADR-gated). Cross-cutting changes are handled after all agents return.
3. **Use absolute paths or `git -C <path>`.** Your dispatch prompt names your working directory; if it is a worktree, operate there.
"""


def emit_subagent_protocol(agent_type: Optional[str] = None) -> Optional[str]:
    """Return the agent-owned-phase protocol for SubagentStart injection.

    Returns None for read-only agent types (Explore, Plan), which never own an
    orchestrator phase, so the protocol is suppressed as noise.
    """
    if agent_type and agent_type in READONLY_AGENT_TYPES:
        return None
    return SUBAGENT_PHASE_PROTOCOL
