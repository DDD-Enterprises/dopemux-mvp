---
id: ux-integration-spec
title: Ux Integration Spec
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Ux Integration Spec (reference) for dopemux documentation and developer workflows.
---
# Seamless Operator UX Integration Spec

## Design Goal

Provide a gorgeous, implicit operator experience that notices unfinished work, service drift, and cognitive-state risk without pretending advisory systems own workflow truth. The UX should reduce cognitive load while preserving determinism, replayability, proof, and explicit write gates.

## First-Screen Model

The first operator surface should be Cockpit, not a marketing or explanatory page. It should show:

- Current work state: active Task Orchestrator item, branch/worktree, dirty state.
- F001 signal: untracked work summary, false-start count, and highest-value next action.
- Cognitive advisory: ADHD Engine current state if live, otherwise `NOT_PROBED` or `DEGRADED`.
- Service spine: active/registered/degraded/unknown service count.
- Proof rail: latest validation or why no validation exists.

## Status Vocabulary

Use stable, audit-friendly labels:

- `LIVE`: directly probed and healthy.
- `DEGRADED`: service responded or fallback exists, but some dependency is missing.
- `NOT_PROBED`: intentionally not checked in this run.
- `UNKNOWN`: repo/runtime does not prove the claim.
- `BLOCKED`: known blocker prevents action.
- `ADVISORY`: support signal that must not mutate workflow truth.
- `PROXY`: bridge/adapter signal that is not source truth.

Do not collapse `UNKNOWN`, `NOT_PROBED`, and `DEGRADED` into a green state.

## Cockpit Layout

### PM Mode

- Show Task Orchestrator workflow truth.
- Include F001 detected-work row only as a recommendation unless explicitly tracked.
- If a F001 item was converted, show Task Orchestrator id and ConPort F001 record id.

### Implementer Mode

- Show current branch/worktree and dirty-state summary.
- Show untracked work detection with max three files by default.
- Actions: inspect, copy evidence, copy Task Packet prompt, open safe action gate.

### Services Mode

- Show grouped service model:
  - Active stack
  - Registered services
  - Source-only support surfaces
  - Duplicates/legacy/unknown
- Group aliases under canonical names.
- Show per-service authority: canonical, support, adapter, infra, unknown.

### Events Mode

- Show event-bus state and recent event categories when probed.
- Mark ADHD events as advisory/support.
- Mark bridge events as transport/proxy.

## Web Dashboard

The web dashboard can provide richer visualization, but it must use the same state vocabulary as Cockpit.

Required behavior:

- Show ADHD Engine state as advisory.
- Show F001 summary only when backed by Serena tool response or explicit degraded state.
- Use compact, scan-friendly layout.
- No fake healthy mock state; mock/demo data must be visibly marked.
- Provide receipts and source timestamps.

## F001 Interaction Pattern

When untracked work is detected:

1. Surface a concise summary.
2. Show why it was detected: branch, changed files count, orphan reason, confidence, grace period.
3. Show false-start context if available.
4. Offer low-friction actions:
   - Inspect
   - Track as workflow item
   - Create ADR/RFC first
   - Snooze
   - Ignore as experiment
   - Resume related abandoned work
5. Require explicit confirmation for any write.
6. Emit a receipt with canonical writer and target id.

Copy should be factual and non-shaming:

```text
Untracked work detected: "service integration audit"
5 files changed on codex/example. No linked workflow item found.
You can inspect, track, design first, snooze, or ignore this experiment.
```

Avoid:

- modal blocking by default
- blame language
- "production-ready" without proof
- hidden auto-track
- action buttons without provenance

## Safe Action Gate

Every mutating action must show:

- action name
- canonical writer
- target service
- expected files/records
- side effects
- rollback/undo guidance
- proof that will be emitted
- confirmation requirement

Examples:

- Track as workflow item: canonical writer `task-orchestrator`; link F001 record in ConPort.
- Snooze detection: canonical writer `ConPort custom_data: untracked_work`.
- Ignore detection: canonical writer `ConPort custom_data: untracked_work`.
- Create ADR/RFC: canonical writer repo docs path, through a separate Task Packet.

## Visual Quality Bar

- Dense but calm operational UI.
- No floating-card clutter; use full-width bands, rails, panes, and table rows.
- Use icons/symbols for actions when rendered in graphical UI.
- Max three primary recommendations at once.
- Stable dimensions for rows and counters.
- Visible provenance on every non-local signal.
- Button/action labels must not overflow on narrow widths.
- Degraded states should be visually distinct but not alarming unless action is blocked.

## Acceptance Scenarios

- Clean slate: no untracked work, services not probed, ADHD unavailable. UI shows `NOT_PROBED`/`UNKNOWN` honestly.
- F001 base only: enhanced tool absent. UI shows base detection available and enhanced unavailable, with no enhanced affordance.
- F001 enhanced detected: UI shows summary, false-start count, and safe actions.
- ConPort unavailable: UI shows degraded detection and disables ConPort-backed history/actions.
- ADHD Engine unavailable: UI hides cognitive recommendations or marks them degraded.
- Task Orchestrator unavailable: tracking action is blocked, but inspect/copy evidence remains available.
- Bridge available only: UX marks bridge data as proxy, not authority.
