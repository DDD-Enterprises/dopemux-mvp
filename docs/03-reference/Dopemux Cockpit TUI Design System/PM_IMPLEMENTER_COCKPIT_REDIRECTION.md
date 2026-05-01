---
id: COCKPIT_PM_IMPLEMENTER_REDIRECTION
title: PM / Implementer Cockpit Redirection
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-25'
last_review: '2026-04-25'
next_review: '2026-07-25'
prelude: Redirects PM and Implementer cockpit modes from a unified "dopemux brain" model to per-mode pane semantics that respect split authority across Leantime, task-orchestrator, ConPort, dope-memory, dope-context, and dopecon-bridge.
---

# PM / Implementer Cockpit Redirection

## Purpose

This file revises the PM and Implementer cockpit semantics so they match the split-authority world the cockpit actually operates in. PM and Implementer are shells / chrome that frame work; they are not PM truth owners and not execution truth owners. Outer geometry from earlier mocks may remain; pane semantics differ by mode and are described here.

This file is compatible with `ARCHITECTURE_SAFETY_OVERLAY.md` and narrower in scope. The overlay wins on conflict.

---

## Core Verdict

The current cockpit model should be revised, not replaced.

- Shared outer geometry (mode bar, three-column body, command rail, status rail) may remain.
- Pane semantics inside the body differ by mode.
- PM mode is workflow triage and adjudication first.
- Implementer mode is current task, acceptance, evidence, and validation first.
- `PKT-*` and `PKB-*` are secondary compose-and-forward refs. They are not primary authorities and not primary screen anchors.
- A unified PM record, a unified task record, and a "save everything from one button" model are forbidden.

---

## PM Mode Law

PM mode's primary job is readiness and workflow movement across split authorities. The PM operator answers six things in this mode:

- metadata completeness (from Leantime)
- workflow legality (from task-orchestrator)
- blockers (from task-orchestrator and linked records)
- linked decisions / progress (from ConPort)
- chronicle receipts (from dope-memory)
- handoff readiness (PM -> Implementer)

### PM Pane Model

| Slot                          | Pane                                                                              |
|-------------------------------|------------------------------------------------------------------------------------|
| Left rail                     | Workflow / slice map. Not a service / system map.                                  |
| Center upper                  | Workflow triage / readiness queue.                                                 |
| Center lower                  | Adjudication context: blockers, allowed transitions, linked decisions, handoff readiness. |
| Right inspector upper         | Selected slice detail only.                                                        |
| Right inspector lower         | Canonical actions, then a hard-divided bridge adapter/proxy panel.                 |
| Command / status rail         | Current filter, legality check, warnings, keybindings, optional source-labeled support cue. |

Each PM pane carries the four-field declaration:

```
domain:       <e.g. workflow_state | metadata | decisions | chronicle>
authority:    <task-orchestrator | leantime | conport | dope-memory>
role:         canonical | derived | mirrored | proxied | authoring | chrome
next_action:  <transition | open | inspect | handoff | none>
```

### PM Forbidden Patterns

- Mixed story / task / decision / chronicle / research / mirror mega-list as the PM primary surface.
- Handoff draft dominating the primary screen area.
- A unified PM save button or a single PM commit affecting multiple authorities.
- Workflow mutation routed through dopecon-bridge instead of through task-orchestrator's own action surface.
- Leantime metadata shown as workflow authority. Leantime is metadata; workflow legality is task-orchestrator.
- dope-memory mirror receipts shown as canonical PM success. Receipts mirror what already happened.
- Service / system map as PM primary left rail. The PM left rail is workflow / slice map.
- Global "search everything" as the PM primary surface.

---

## Implementer Mode Law

Implementer mode's primary job is one bounded task. The Implementer operator answers six things in this mode:

- understand the current task
- confirm acceptance criteria
- inspect blockers
- gather bounded evidence
- run or record validation
- prepare handback refs

### Implementer Pane Model

| Slot                          | Pane                                                                              |
|-------------------------------|------------------------------------------------------------------------------------|
| Left rail                     | Work contract / support rail. Not a service / system map.                          |
| Center upper                  | Current task, next action, acceptance subset, blockers.                            |
| Center lower                  | Evidence workspace. Top-3 results, `more_count`, `next_token`.                     |
| Right inspector upper         | Selected acceptance, evidence, or proof detail.                                    |
| Right inspector lower         | Canonical actions, then a hard-divided bridge adapter/proxy panel.                 |
| Command / status rail         | Validation status, task drift warning, UNKNOWN support / retrieval gaps, keybindings. |

Each Implementer pane carries the four-field declaration:

```
domain:       <e.g. current_task | acceptance | evidence | proof>
authority:    <task-orchestrator | conport | dope-context | repo-truth-extractor>
role:         canonical | derived | mirrored | proxied | authoring | chrome
next_action:  <run | record | inspect | request_more | handback | none>
```

### Implementer Forbidden Patterns

- Retrieval console as the primary Implementer mode.
- Handback draft dominating the inspector.
- PM metadata edits performed inside Implementer mode.
- Workflow transitions routed through dopecon-bridge instead of through task-orchestrator.
- Retrieval (dope-context) treated as source truth for acceptance, decisions, or workflow state. Retrieval is retrieval.
- Serena treated as canonical. Serena is optional UNKNOWN support unless runtime authority is proven.
- Global "search everything" as the Implementer primary surface.
- Dopemux owning execution truth. Execution is owned by agents and runtimes; outcomes are logged to ConPort and mirrored to dope-memory.
- Service / system map as Implementer primary left rail. The Implementer left rail is work contract / support rail.

---

## Packet Object Law

Packet objects (`PKT-*`, `PKB-*`) may appear as secondary compose-and-forward refs.

- They are not canonical PM state, not workflow state, not execution truth.
- They must not dominate the PM or Implementer home screens.
- Draft state for a packet is plain text / ref state. It is not a new chip and not a new authority surface.
- A packet may reference canonical records by their authority labels (for example, a ConPort decision id, a task-orchestrator transition id, a Leantime ticket id), but the packet itself is a transport artifact.
- Packet panes may live in inspector lower, in handoff/handback flows, or in compose surfaces. They do not appear in the primary left rail and do not appear in the center upper slot.

---

## Support Cue Law

ADHD / operator-support cues are advisory only.

- They may appear as narrow, source-labeled cues (for example a single status-rail line: `cue: ADHD_engine: low energy detected`).
- They never become workflow gates. A blocked workflow is blocked by task-orchestrator legality, not by an ADHD cue.
- They never become PM truth. A PM record is canonical because of its authority owner, not because of an operator-state cue.
- They never become implementation success. Acceptance is acceptance; cues do not satisfy it.
- They never become status chips. The closed chip set in `ARCHITECTURE_SAFETY_OVERLAY.md` is exhaustive.
- Lifestyle automation and personal dashboards are out of first cockpit scope.

---

## Authority Label Examples

These are example labels for pane declarations. They are illustrative, not exhaustive.

```
# PM left rail
domain:      workflow_slice
authority:   task-orchestrator
role:        derived
next_action: open

# PM center upper
domain:      readiness_queue
authority:   task-orchestrator
role:        canonical
next_action: triage

# PM right inspector lower (canonical actions)
domain:      decisions
authority:   conport
role:        authoring
next_action: log_decision

# PM right inspector lower (hard-divided bridge segregator)
Bridge adapter/proxy: dopecon-bridge
role:        proxied
note:        Adapter actions only. Canonical writes route through their owners.

# Implementer center upper
domain:      current_task
authority:   task-orchestrator
role:        canonical
next_action: confirm_acceptance

# Implementer center lower
domain:      evidence
authority:   dope-context
role:        derived
next_action: request_more

# Implementer status rail cue
cue: ADHD_engine: scattered attention; suggest 25-min focus block
role:        chrome
authority:   dopemux control surface
note:        advisory only; does not gate transitions
```

---

## Compatibility With ARCHITECTURE_SAFETY_OVERLAY.md

This file is narrower than the overlay and consistent with it.

- The pane declaration four-field requirement comes from the overlay (Pane Declaration Law).
- The bridge segregation comes from the overlay (Bridge Law and Viewport Degradation Law).
- The chip vocabulary comes from the overlay (Chip / Status Law).
- The forbidden phrases enforced by the Contradiction Gate live in the overlay and `ACCEPTANCE.md`.
- If any sentence here appears to soften or contradict the overlay, the overlay wins and this file must be patched.
