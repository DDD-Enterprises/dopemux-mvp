---
id: COCKPIT_ARCHITECTURE_SAFETY_OVERLAY
title: Architecture Safety Overlay (Cockpit TUI)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-25'
last_review: '2026-04-25'
next_review: '2026-07-25'
prelude: Architecture safety overlay binding visual hierarchy, pane semantics, provenance, bridge degradation, and chip vocabulary for the Dopemux Cockpit TUI Design System.
---

# Architecture Safety Overlay

## Purpose

This overlay is the safety contract for the Dopemux Cockpit TUI. It binds visual decisions to authority claims and prevents the cockpit from accidentally collapsing per-domain authority into a single "Dopemux brain" view. Every other doctrine file in this package defers to this overlay when in conflict, except where explicitly noted (UX_REFERENCE_RECONCILIATION.md is subordinate; PM_IMPLEMENTER_COCKPIT_REDIRECTION.md is compatible-with-and-narrower-than this overlay).

The overlay applies at design-time, mock-time, and review-time. It does not assert any runtime exists. Files in this package describe a control surface; package files do not certify implementation unless a runtime artifact in the repository proves it.

---

## Authority Model

Dopemux is a composed multi-system operator workspace. Authority is per-domain, not per-service. The cockpit coordinates surfaces; it does not own truth.

| Domain                                   | Authority owner                                                  | Cockpit role                                          |
|------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------|
| Operator control surface / coordination  | dopemux control surface                                          | host chrome, mode bar, command rail, status rail      |
| PM metadata, project & ticket snapshots  | Leantime                                                         | passive read; never mutated through cockpit chrome    |
| Workflow transitions, queue, blockers    | task-orchestrator                                                | canonical workflow state; transitions live here       |
| Decisions, progress, custom data, project context | ConPort                                                  | canonical structured records and knowledge graph      |
| Chronicle / receipts / mirror records    | dope-memory                                                      | historical receipt store; never mutated from cockpit  |
| Retrieval and index behavior             | dope-context                                                     | retrieval surface only; never authority for results   |
| Bridge adapter / proxy / routing         | dopecon-bridge                                                   | adapter/proxy actions only; never canonical writes    |
| Operator support / cognitive state       | ADHD Engine                                                      | advisory cues only; never gates or PM truth           |
| Repo extraction runtime / proof          | repo-truth-extractor                                             | Services child / workload surface only                |
| Execution agents (executors / supervisors / advisors) | agent system                                       | render as agent surface; never PM authority           |
| Optional technical-context support       | Serena                                                           | UNKNOWN unless runtime authority is proven            |

dopemux is the operator control surface and coordinator. It is not the PM truth owner, not the task-state owner, and not the canonical decision authority. Loose phrases that imply otherwise are forbidden (see Forbidden Phrases).

---

## Visual Hierarchy Law

Visual hierarchy is an authority claim.

If a pane looks canonical or peer-equivalent to canonical state, the design is making that claim, even if a small label says otherwise. Mocks must therefore:

- Reserve canonical visual weight (top-left primacy, full-width header, bordered emphasis, peer placement next to canonical state) for the actual authority owner of the data shown.
- Demote derived, mirrored, proxied, advisory, and adapter/proxy panels visually so they cannot be misread as canonical.
- Treat label-only disclaimers ("note: this is mirrored", "advisory") as insufficient. Hierarchy must reinforce the label.
- Treat font weight, border weight, color emphasis, anchored position, and selection priority as authority signals.

If a pane cannot be visually demoted enough to avoid an authority claim, it is removed from the layout or moved to inspector detail.

---

## Pane Declaration Law

Every major pane must answer the following four fields, declared explicitly in the spec, mock annotation, and implementation comments:

```
domain:       <which domain this pane represents>
authority:    <the authority owner for that domain>
role:         canonical | derived | mirrored | proxied | authoring | chrome
next_action:  <what the operator can do from this pane>
```

Rules:

- Unknown authority renders as `UNKNOWN` literally. Do not guess.
- Chrome panes (top frame, mode bar, command rail, status rail, bottom flag rail) declare `role: chrome` and `authority: dopemux control surface`.
- A pane with `role: chrome` carries no SRC, no canonical data labels, and no transition controls.
- Authoring panes (PM authoring, Implementer authoring) describe the surface authority for the artifact being authored, not for upstream truth.
- A pane that cannot answer all four fields is not promoted from mock to implementation.

---

## SRC / Provenance Law

SRC is provenance, not authority. SRC denotes which service produced or stores a logical data/provenance record. Authority is declared at the pane level, not at the row level.

Rules:

1. SRC appears only on logical data/provenance records, never on chrome.
2. SRC must not appear in the top frame header, mode bar, command rail, status rail, or bottom flag rail.
3. SRC appears once per logical record. Wrapped continuation rows align under the content column and do not repeat SRC.
4. SRC may repeat only when physical rows are independently selectable or independently exportable as separate logical records.
5. SRC is never a status. SRC does not change with transitions or chips.
6. SRC values name a service (for example: `SRC=conport`, `SRC=task-orchestrator`, `SRC=leantime`, `SRC=dope-memory`, `SRC=dope-context`, `SRC=repo-truth-extractor`). `SRC=dopemux` is forbidden in chrome and is forbidden as a label for canonical data, because dopemux is a control surface, not a data authority.

The replacement doctrine (canonical) is:

> Every logical data/provenance record carries SRC=<service> once. Wrapped continuation rows align under the content column and do not repeat SRC unless physical rows are independently selectable/exportable.

---

## Bridge Law

dopecon-bridge is an adapter / proxy / routing surface. It transports calls between services. It is never canonical authority for the data it transports.

Use:

```
Bridge adapter/proxy: dopecon-bridge
```

Never use:

```
Bridge actions authority: dopecon-bridge
```

Rules:

- Bridge actions are adapter / proxy actions only. They never represent canonical writes.
- Bridge surfaces remain visually segregated from canonical state with a hard divider, distinct framing, and explicit `adapter/proxy` labeling.
- Bridge surfaces never sit as a peer pane to canonical state at smaller viewports (see Viewport Degradation Law).
- A bridge action that mutates canonical state must route through the canonical authority's own action surface and be labeled there. The cockpit must not present a bridge button that appears to commit canonical state.

---

## Viewport Degradation Law

The cockpit defines exactly three supported viewports plus a blocker viewport.

| Viewport (cols x rows) | Bridge placement                                                     |
|------------------------|----------------------------------------------------------------------|
| 120 x 40               | Dedicated bridge segregator pane allowed (right inspector lower).     |
| 100 x 32               | Bridge lives in inspector / lower detail. No dedicated segregator.    |
| 80 x 24                | Bridge collapses into inspector detail only. No peer pane.            |
| Below 80 x 24          | Render `BLOCKER terminal too small`. No content rendered.             |

Rules:

- Bridge never becomes a peer pane beside canonical state at 80 x 24.
- Below 80 x 24, the cockpit renders a single blocker message and exits the layout. No partial UI is rendered.
- The four-field declaration (domain, authority, role, next_action) must remain legible at every supported viewport.
- Inspector / lower detail at 80 x 24 may abbreviate values, but must not delete the authority field.

---

## Chip / Status Law

The cockpit uses a closed chip set as render/category markers. Chips are not the full semantic vocabulary.

Closed chip set:

```
LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE
```

Rules:

- Chips are visual category markers only. They do not replace explicit status words in body text.
- Explicit status words may appear in body text: `queued`, `running`, `complete`, `blocked`, `failed`, `degraded`, `unknown`, `exported`, `needs verification`.
- UNKNOWN remains literal. UNKNOWN is never a chip. Do not collapse UNKNOWN into EDGE.
- A row whose authority or status is not proven shows `UNKNOWN` as plain text in the affected field. UNKNOWN preserves the unresolved condition; it is not a status.
- Chips may be color-tinted, but color is secondary. Removing color must leave the chip readable from text alone.

---

## PM / Agent Law

PM and Implementer modes are shells / chrome that frame work, not PM truth owners.

- The PM mode does not own task state. task-orchestrator owns workflow transitions; ConPort owns decisions and progress; Leantime owns metadata. PM mode coordinates these surfaces.
- The Implementer mode does not own execution truth. Agents and runtimes own execution; ConPort owns logged outcomes; dope-memory owns receipts.
- Agent panes are executors / supervisors / advisors. Agent panes never imply PM truth ownership and never imply canonical decision authority.
- Agents may surface advisory cues, suggested handoffs, and proposed records, but commit only through the canonical authority's own action surface.
- The ADHD Engine surfaces advisory cues only. ADHD cues never gate PM transitions, never override workflow legality, and never become status chips.

PM and Implementer pane semantics are detailed in `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`. That file is compatible with this overlay and narrower in scope.

---

## Forbidden Phrases

The following phrases must not appear anywhere in this package's doctrine files, mocks, or examples. They collapse authority distinctions.

- `Every row carries SRC`
- `Every row in every pane carries SRC`
- `Services authority: dopemux`
- `command authority: dopemux`
- `Bridge actions authority: dopecon-bridge`
- `SRC=dopemux` in chrome (top frame, mode bar, command rail, status rail, bottom flag rail)
- `UNKNOWN->EDGE` as semantic collapse
- `UNKNOWN→EDGE` as semantic collapse
- `UNKNOWN=EDGE` as semantic collapse

These phrases are also gated by the Contradiction Gate in `ACCEPTANCE.md`.

---

## Related Files

- `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md` — narrower PM/Implementer pane semantics, compatible with this overlay.
- `UX_REFERENCE_RECONCILIATION.md` — how docs/ux supporting references are reconciled; this overlay wins on conflict.
- `PREIMPLEMENTATION.md` — preconditions and fail-closed rules before promoting any pane from mock to implementation.
- `ACCEPTANCE.md` — checklist and contradiction gate enforcing this overlay.
- `SKILL.md` — operational skill summary for cockpit work.
