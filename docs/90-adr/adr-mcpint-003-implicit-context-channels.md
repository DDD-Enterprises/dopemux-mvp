---
id: adr-mcpint-003
title: 'ADR-MCPINT-003: The Closed List of Implicit-Context Channels'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Declares native_hooks.py SessionStart the sole implicit-context injection point with four bounded blocks under a ~3KB budget, limits PostToolUse to two channels, and formally retires the six orphaned legacy hooks.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - adr-mcpint-001
    - adr-mcpint-002
    - adr-mcpint-004
    - adr-mcpint-005
---

# ADR-MCPINT-003: The Closed List of Implicit-Context Channels

**Status**: Proposed
**Date**: 2026-07-16
**Owners**: @hu3mann (program DMX-MCPINT, root `af10eefd`)

## Context

"Implicit use" — context that reaches the agent without being summoned — is the program's
end goal, and today it has exactly one working mechanism: the task-orchestrator
`get_context` cache replayed into SessionStart (register HOOK-TO-CONTEXT-REPLAY — "the
only implicit-context loop today"; text advisory, Claude-only). Everything else that was
supposed to inject context is either unwired or rotten:

- **Six orphaned legacy hook scripts** sit in `.claude/hooks/` unreferenced by the
  dispatcher's active flows: `check_energy.sh`, `save_context.sh`, `track_file_edit.sh`,
  `log_progress.sh`, `prompt_analyzer.py` (carries stale ports), `session_lifecycle.py`
  (register HOOK-LEGACY-ORPHANS, status `built-unwired`, decision `adr:adr-mcpint-003`).
- Instruction surfaces hardcode ~11 nonexistent ConPort tool names (register
  CMD-NAME-DRIFT-REPAIR) — prose-based "implicit" guidance rots without gates.
- The MCF proactive-injection fabric that would have owned this space is design-only NO-GO
  (register MCF-FABRIC — shelved by ADR-MCPINT-005; its viable child TP-MCF-004 escapes
  into this ADR's channel list).

All 11 lifecycle hook events already dispatch through a single entry point,
`src/dopemux/claude/native_hooks.py` (SessionStart `:316-356`, PostToolUse TO cache
`:486-518`). An unbounded set of injection channels is how context budgets die; a closed,
budgeted list is how implicit context stays trustworthy.

## Decision

The set of implicit-context channels is **CLOSED** and enumerated here. Adding, removing,
or rebudgeting a channel requires superseding this ADR.

### 1. SessionStart — the sole injection point

`native_hooks.py` SessionStart is the **only** place implicit context is injected into a
session. It emits exactly **four bounded blocks**:

| # | Block | Register id / packet | Status |
|---|---|---|---|
| 1 | Task-orchestrator context replay (cached `get_context`) | HOOK-TO-CONTEXT-REPLAY | live |
| 2 | dope-memory recap (bounded Top-3) | TP-MCF-004 → MCPINT-IMP-RECAP-003 | planned; **BLOCKED by DMX-MEMSPINE-IDENTITY-005** (N2 contamination means recap would inject cross-workspace data today) |
| 3 | Fleet-capability line ("conport:ok dope-memory:ok TO:ok facade:ok serena:degraded") | HOOK-FLEET-CAPABILITY-LINE → MCPINT-IMP-HEALTH-004 | planned; reuses `render_health_probe_list`, cached probe, 60s TTL — subsumes the H3 health snapshot (HOOK-H3-HEALTH-PROBE) as its mechanism |
| 4 | Untracked-work probe (F001-lite) | HOOK-H5-UNTRACKED-PROBE | live; becomes the lite front-end that dedupes against the dope-adhd F001 backend once MCPINT-IMP-ADHDINTEL-007 lands (placement map §2) |

**Budgets, uniform across blocks**: ~3KB total per session across all four blocks; 2s
timeout per block; **fail-open** — a slow or dead backend yields a missing block, never a
blocked session and never a stack trace in the transcript.

### 2. PostToolUse — limited to two channels

1. The task-orchestrator `get_context` cache refresh (existing, `native_hooks.py:486-518`)
   — feeds block 1.
2. The ADHD activity ingress (hooks → adhd-engine `/external-activity`) — **SVCFIN-owned**
   (DMX-ADHDLOOP-HOOKINGRESS-001); this ADR reserves the channel slot and decides nothing
   about its content.

**G4 exception (user decision 2026-07-16)**: the predictive-risk pilot runs as a
**time-boxed, flag-gated PostToolUse advisory** behind `DOPEMUX_ENABLE_PREDICTIVE_RISK`
(default off), per MCPINT-IMP-RISK-005 — a 2-week keep/kill pilot of the 527-line
`predictive_risk_assessment.py` module (register TO-PREDRISK). It ships **no new tool
surface** (placement map §3). If the pilot is kept, the closed list is amended by a
superseding note adding it as PostToolUse channel 3; if killed, the flag and hook wiring
are removed and TO-PREDRISK moves to the ADR-MCPINT-005 shelf. The pilot is the only
sanctioned temporary exception to the closed list.

### 3. Enforcement and guard hooks are out of scope

PreToolUse/PostToolUse **guard** hooks (H1 DCP surface guard, H2 denylist nudge, H4 proof
guard, orchestrator enforcement/attribution, Stop checkpoint gate) are enforcement, not
context injection — they are unchanged by this ADR and not counted against the budget.

### 4. The six orphaned legacy hooks are formally retired

`check_energy.sh`, `save_context.sh`, `track_file_edit.sh`, `log_progress.sh`,
`prompt_analyzer.py`, `session_lifecycle.py` are **retired**: deleted from
`.claude/hooks/` (or moved to the graveyard per repo hygiene convention), with register
HOOK-LEGACY-ORPHANS flipped to `retired`. Any capability they gestured at that is still
wanted (energy checks, activity tracking) arrives through the adhd-engine ingress and
dope-adhd surface — never by resurrecting the scripts.

### Invariants

- One injection point: no hook other than `native_hooks.py` SessionStart may write
  implicit context into a session; no MCP server may push context outside these channels.
- Every channel is bounded (size + timeout) and fail-open.
- Channel content must name only tools that exist in the committed
  `mcp_tool_surfaces.json` (the ADR-MCPINT-001 drift gate applies to hook-emitted text
  templates too).
- Implicit channels are Claude-only until an equivalent hook runtime exists for another
  agent; non-Claude agents get context by explicit reads through the ADR-MCPINT-002 read
  plane.

### Non-goals

- The ADHD activity ingress content/contract (owner: DMX-ADHDLOOP-HOOKINGRESS-001).
- The recap TUI consumer (owner: DMX-ADHDLOOP-RECAP-003 — same upstream tool, different
  consumer).
- Timer/break automation (ADHD_FEATURES doctrine already marks these aspirational; nothing
  here wires them).

## Alternatives Considered

- **Open-ended hook additions (status quo trajectory).** Rejected: six orphaned scripts
  and ~11 phantom tool names are what an ungoverned channel set produces; budget-less
  injection also competes with the user's actual context.
- **MCF proactive injection fabric as the channel owner.** Rejected: MCF-FABRIC is
  design-only NO-GO (shelved by ADR-MCPINT-005); this ADR keeps its one viable child
  (TP-MCF-004) as a bounded block instead of a fabric.
- **Retain legacy hooks as dormant "may rewire later" assets.** Rejected: dormant-but-
  present scripts read as capability in every audit (the BUILT-UNWIRED failure mode this
  program exists to end); `prompt_analyzer.py` already carries stale ports.
- **Per-channel opt-in flags instead of a closed list.** Rejected for the base set: flags
  multiply states to verify; the fail-open budget makes the four blocks safe-by-default.
  (G4's pilot flag is deliberately the exception — reversibility is the point there.)

## Consequences

- **Packets**: MCPINT-IMP-RECAP-003 (block 2; cross-tree BLOCKS dep on
  DMX-MEMSPINE-IDENTITY-005), MCPINT-IMP-HEALTH-004 (block 3), MCPINT-IMP-RISK-005 (G4
  pilot, PostToolUse exception), MCPINT-FND-DRIFTGATE-003 (hook-template names in scan
  roots), MCPINT-IMP-ADHDINTEL-007 (H5↔F001 dedupe). Hook retirement is a small change
  executable within FND-INSTRREPAIR-004's surface-repair scope.
- A fresh session predictably carries ≤ ~3KB of implicit context with a fixed shape —
  P4/P6 verification captures a transcript with all four blocks.
- Losing a backend degrades gracefully (missing block + degraded entry in the capability
  line) instead of failing the session.
- Anyone proposing a new implicit channel now has a named place to argue it — a
  superseding ADR — instead of a quiet hook edit.
- Deleting `session_lifecycle.py` et al. removes the last excuse for audits to count them
  as live ADHD support (the 2026-05-31 ADHD audit's "largely aspirational" finding gets
  structurally resolved rather than re-litigated).

## Migration Strategy

1. Land blocks 3 (HEALTH-004) — no dependencies — then 2 (RECAP-003) after IDENTITY-005.
2. Retire the six scripts + flip the register entry in the same PR as the SessionStart
   block consolidation (so the hooks directory and the ADR agree in one commit).
3. G4 pilot: wire behind the flag, default off; calendar the 2-week keep/kill decision.
4. Rollback: each block is independently removable (they are additive text blocks); hook
   retirement is revertable from git history.

## Verification

- Fresh-session transcript showing all four SessionStart blocks within budget (P4 proof).
- Kill-one-backend test: stop dope-memory → session starts, block 2 absent, capability
  line shows `dope-memory:down`, exit 0.
- `grep` gate: no references to the six retired scripts remain in `.claude/settings.json`
  or dispatcher code.
- Flag test: `DOPEMUX_ENABLE_PREDICTIVE_RISK` off → zero predictive-risk output;
  on → advisory present (P4 flag on/off proof).

## Validation

- **PAL consensus**: NOT_RUN for this ADR — the Phase-2 packet requires the consensus pass
  on the load-bearing pair (ADR-001/ADR-002); this ADR receives consensus review at
  merge/acceptance time. See the program note appended to ADR-MCPINT-001.
- ConPort `log_decision`: owed at acceptance.

## Cross-references

- ADR-MCPINT-001 (drift gate + snapshot the channels must respect), ADR-MCPINT-002
  (non-Claude agents read explicitly — no implicit channel for them), ADR-MCPINT-004
  (activity events these hooks produce ride the blessed ingress), ADR-MCPINT-005
  (MCF-FABRIC shelf; TO-PREDRISK's conditional shelf).
- `docs/03-reference/mcp/tool-placement-map.md` §2-3 (H5↔F001 dedupe; predictive-risk "no
  new tool surface").
- Owners referenced, not decided for: DMX-ADHDLOOP-HOOKINGRESS-001,
  DMX-ADHDLOOP-RECAP-003, DMX-MEMSPINE-IDENTITY-005.
- Runtime evidence: `claudedocs/mcp-fleet-runtime-verification-2026-07-16.md` finding N2
  (block-2 blocker), claim 16 (adhd-engine absent — ingress channel's backend must be
  ignited first, DMX-ADHDLOOP-IGNITION-VERIFY-002).
