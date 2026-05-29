---
id: plugin-hooks-port
title: Orchestrator Plugin Hooks Port (Path B)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: What TP-CS-101 ported from the upstream task-orchestrator Claude plugin into Dopemux's native hook dispatcher and /dx: command surface, and why.
related_packets:
  - TP-CS-100
  - TP-CS-101
---

# Orchestrator Plugin Hooks Port (Path B)

## Why

TP-CS-100 assessed the upstream `claude-plugins/task-orchestrator/` bundle (`jpicklyk/task-orchestrator` @ `main`, plugin v3.2.2) and recommended **Path B — fork + adapt** (assessment shipped via PR #719). TP-CS-101 implements the recommendation, scoped (operator decision) to the genuinely net-new value: the **hooks** (Dopemux lacked `SubagentStart`, orchestrator-tool `PreToolUse` matching, and actor/skill enforcement) plus a few net-new **skills** as `/dx:` commands. The other 8 upstream skills are already covered by the existing `/dx:` surface; `ralph` and the output styles (TP-CS-110, shipped via PR #722) are out of scope.

**Architecture decision**: port the hook behavior into the existing Python dispatcher (`src/dopemux/claude/native_hooks.py`) rather than vendoring the upstream Node `.mjs` files. No Node runtime, one hook system, consistent with the "all hooks route through `native_hooks.py`" doctrine and the existing `orchestrator_session_start.py` / `orchestrator_post_edit_nudge.py` helpers (shipped via PR #722).

## What was ported

Helper modules in `.claude/hooks/` (imported by `native_hooks.py` with a no-op `ImportError` fallback, matching the established pattern):

| Dopemux module | Upstream source (`.../hooks/`) | Behavior |
|---|---|---|
| `orchestrator_subagent_protocol.py` | `subagent-start.mjs` | `SubagentStart` → injects the agent-owned-phase protocol into implementation subagents; skips read-only agent types (`Explore`, `Plan`). |
| `orchestrator_enforcement.py` (actor) | `enforce-actor-attribution.mjs` | `PreToolUse[advance_item\|manage_notes]` → **blocks** writes missing an `actor` object, **only when** `actor_authentication.enabled: true` in `config.yaml`. Dormant otherwise. |
| `orchestrator_enforcement.py` (skill) | `skill-enforcement.mjs` | `PreToolUse[manage_notes upsert]` → **non-blocking** warning when a skill-gated note is filled with a thin/placeholder body (<200 chars). |
| `orchestrator_enforcement.py` (plan-mode) | `pre-plan.mjs` / `post-plan.mjs` | `PreToolUse[EnterPlanMode]` → `/dx:plan-enter` guidance; `PostToolUse[ExitPlanMode]` → `/dx:plan-exit` guidance. |

Adaptations from upstream: Dopemux `mcp__task-orchestrator__` tool prefix (matching is substring-based, so prefix-agnostic); the Dopemux actor-ID convention `{id:"worktree-<basename>-<branch>", kind, parent}`; the AGENTS.md §9/§12 proof-bundle-into-note rule; `yaml.safe_load` (PyYAML) instead of the upstream line-based YAML parsing.

## Wiring (native_hooks.py)

- `handle_event` dispatches `SubagentStart` → `_on_subagent_start`.
- `_on_pre_tool_use` runs enforcement **above** the workflow-state gate (orchestrator-tool calls must be checked regardless of an active Dopemux workflow): actor-attribution (hard block), then EnterPlanMode + skill-enforcement (advisory context), then the existing iteration/time-limit logic.
- `_on_post_tool_use` injects ExitPlanMode guidance alongside the existing edit-nudge.
- `config.yaml` is only read for orchestrator write-tool calls (`advance_item`/`manage_notes`), avoiding per-call overhead on ordinary tools.
- `.claude/settings.json` adds a `SubagentStart` registration routing to `native_hooks.py` (no matcher; `agent_type` filtering happens in the dispatcher).

## `/dx:` commands added

`summary` (PM dashboard, read-only), `plan-enter` / `plan-exit` (plan-mode entry/exit workflow), `schema` (read-only schema inspector). These extend the broader `/dx:` surface.

## Fail-safe and integration notes

- Every hook **fails open**: missing helper modules, missing `config.yaml`, or parse errors → no-op (never blocks legitimate work).
- **`SubagentStart` support** was confirmed from the official Claude Code hooks docs and the upstream plugin's production use; a live in-session probe was not run (self-modifying session config is gated). The handler is additive and harmless if the event does not fire.
- **`config.yaml` is not on `main`** (it lives on the `task-orchestrator-claude-surface` series branch). Until it lands, the actor/skill enforcement hooks are dormant by design, and `/dx:schema` reports the absence gracefully. The broader `/dx:` command surface and `dx-command-authoring.md` also live on that series branch; the four commands here follow its documented convention and integrate when it merges.
- **Do not edit `.taskorchestrator/config.yaml`** to enable actor authentication — that is a separate, ADR-gated change (contract-sensitive per AGENTS.md §6).

## Tests

- `tests/test_orchestrator_subagent_protocol.py` — protocol emission + Explore/Plan skip + dispatcher injection.
- `tests/test_orchestrator_enforcement_hooks.py` — actor auth parsing (block/inline/absent), violation detection (prefix-agnostic), the enabled-gate, skill-map collection, thin/substantive/placeholder bodies, worktree-safe config walk, and dispatcher block/warning/plan-mode paths.
