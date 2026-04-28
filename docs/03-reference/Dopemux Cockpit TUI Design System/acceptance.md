---
id: DOPEMUX_COCKPIT_TUI_DESIGN_SYSTEM_ACCEPTANCE
title: Acceptance
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-27'
last_review: '2026-04-27'
next_review: '2026-06-15'
prelude: Pass/fail checklist for the Cockpit design-system package.
---
# ACCEPTANCE.md

Acceptance checklist for the Dopemux cockpit design-system package.
Every box must be checkable against the artifacts in this folder.

---

## Tokens
- [x] No invented hex values; every color comes from `colors_and_type.css`.
- [x] No `--severity-*`, `--success-*`, `--warning-*`, `--error-*`,
      `--info-*`, `--debug-*`, `--hazard-*`, `--danger-*` aliases in CSS.
- [x] Token-card labels in `preview/01-brand-palette.html` use chip
      vocabulary (LIVE / LOGGED / BLOCKER / OVERRIDE / AFTERCARE) and
      role language (frame, heading, panel border) — never generic
      severity nouns.
- [x] Forbidden token-card label list is documented on the palette card.

## Status taxonomy
- [x] Closed chip set is the only status vocabulary:
      `LIVE, BLOCKER, OVERRIDE, LOGGED, AFTERCARE, EDGE`.
- [x] Forbidden chips are explicitly named:
      `UNKNOWN, DEGRADED, FAILED, BLOCKED, SYNC, DRAFT, READY, SUCCESS, ERROR`.
- [x] External vocab mapping is documented:
      `DEGRADED -> OVERRIDE`, `FAILED -> BLOCKER`, `BLOCKED -> BLOCKER`,
      `SYNC -> AFTERCARE`.
- [x] `UNKNOWN` is rendered as literal text in affected fields. `UNKNOWN`
      is never a chip. `UNKNOWN` is never collapsed into `EDGE`. The
      mappings `UNKNOWN->EDGE`, `UNKNOWN -> EDGE`, `UNKNOWN=EDGE` appear
      only as forbidden-pattern entries, never as positive doctrine.
- [x] Status Language explainer (`preview/14-status-language.html`)
      lives in design-system reference, not in the runtime cockpit.

## Chrome vs. data (SRC rule)
- [x] No `SRC=` token appears in the top frame header.
- [x] No `SRC=` in the mode bar.
- [x] No `SRC=` in the shortcut rail.
- [x] No `SRC=` in the status rail.
- [x] No `SRC=` in the bottom flag rail.
- [x] `SRC=` appears on data rows (services, runs).
- [x] `SRC=` appears on inspector pane fields.
- [x] `SRC=` appears on bridge segregator action lines.

## Authority boundaries
- [x] Each pane declares `authority: <service>` in its header.
- [x] Bridge / proxy actions are segregated into a pane that labels
      itself `[EDGE] adapter-only segregated`.
- [x] No bridge / adapter / wrapper / shim is promoted to authority.
- [x] Where authority is unknown, the design uses literal `UNKNOWN`.
- [x] All ten canonical authorities are named in PREIMPLEMENTATION.md
      with their roles.

## Surface separation
- [x] Surface A — Static Terminal Snapshot — is labeled
      "STATIC DEMO · seed-only · read-only · no service adapters · no repo-truth-extractor execution".
- [x] Surface A ships at three sizes (`A1` 120×40, `A2` 100×32, `A3` 80×24).
- [x] Surface B — Live Textual cockpit direction — is labeled
      "DESIGN DIRECTION · NOT IMPLEMENTED" and its chrome carries
      `writes:out-of-scope · proof-gen:out-of-scope · rte-exec:out-of-scope`.
- [x] Surface C — Web / operator dashboard direction — is labeled
      "DESIGN DIRECTION · NOT IMPLEMENTED" and preserves authority
      boundaries.
- [x] Surface D — Design-System Reference — lives in `preview/` and is
      not embedded inside any runtime cockpit screen.

## Typography & glyphs
- [x] Brand mono (`Dopemux Term`, `DopemuxTerm-Regular.ttf`) is declared
      via `@font-face` in `colors_and_type.css`.
- [x] Mono fallback chain documented:
      Dopemux Term Regular -> Dopemux Term Nerd Font Regular ->
      `ui-monospace` -> `monospace` ->
      ASCII/text fallback.
- [x] No font binary is committed without explicit approval; substitution
      and build provenance are documented in `fonts/README.md` and
      `fonts/BUILD.md`.
- [x] ASCII fallback table card exists (`preview/21-ascii-fallback.html`)
      and maps every glyph + frame char to its ASCII substitute.
- [x] Box-drawing characters are single-cell or carry an ASCII fallback.
- [x] No emoji anywhere in operator-facing copy.

## Command glyphs
- [x] TUI surfaces (Surface A, Surface B) use `ctrl+k` / `quick ref: k`,
      never `⌘K`.
- [x] Web surface (Surface C) is allowed to use `⌘K`; it also keeps
      keybinds visible for accessibility.

## Static / live scope discipline
- [x] Surface A footer says "STATIC DEMO · NO WRITES ...".
- [x] Surface B footer says "DIRECTION · not implemented" and lists
      `writes / proof-gen / rte-exec` all as `out-of-scope`.
- [x] No surface implies a service adapter, a write, a proof bundle
      generation, or repo-truth-extractor execution.
- [x] No surface fakes a live stream beyond decorative cursor / WS pulse
      tokens that are themselves marked direction-only.

## Adaptation
- [x] Three frame sizes documented (120×40, 100×32, 80×24).
- [x] Adaptation rules documented in
      `preview/07-adaptation.html` — what disappears first, what must
      never disappear.
- [x] Below 80×24 is a `[BLOCKER]` panel — see
      `src/dopemux/ui/cockpit/render.py::TOO_SMALL_MESSAGE`.

## Error / blocker panel anatomy
- [x] Error panels carry `Problem / Why / Fix / NEXT`.
- [x] Forbidden phrasing is enumerated: "Something went wrong", "Oops",
      "Try again later", "Workflow supercharged", "Magic", etc.
- [x] Authority and write scope are part of the panel surface.

## Handoff
- [x] `PREIMPLEMENTATION.md` documents authority list, token map,
      forbidden assumptions, and the review gate.
- [x] `ACCEPTANCE.md` (this file) enumerates pass/fail criteria.
- [x] No file in this package is positioned as production code.

---

## GPT-5.5 Pro PM-Plane Integration Checklist

This checklist gates promotion of any PM-plane work referenced by the
GPT-5.5 Pro PM/Implementer redesign packet (see
`docs/03-reference/gpt55_pm_implementer_redesign.md`) into a cockpit
mock or implementation.

- [ ] PM mode is workflow triage and adjudication first; not a unified
      mega-list.
- [ ] PM does not own PM truth. It coordinates split authority from
      Leantime metadata, task-orchestrator workflow transitions,
      ConPort decisions/progress context, and dope-memory chronicle
      mirrors.
- [ ] PM left rail is a workflow / slice map, not a service / system map.
- [ ] PM center upper is the workflow triage / readiness queue.
- [ ] PM center lower is adjudication context: blockers, allowed
      transitions, linked decisions, and handoff readiness.
- [ ] PM inspector upper is selected slice detail only.
- [ ] PM inspector lower presents canonical actions first, then a
      hard-divided bridge adapter/proxy panel.
- [ ] `PKT-*` refs are secondary only, never primary authorities or
      dominant screen anchors.
- [ ] Implementer mode is current task / acceptance / evidence /
      validation first; not a retrieval-only console.
- [ ] Implementer left rail is a work contract / support rail, not a
      service / system map.
- [ ] Implementer center upper is current task, next action, active
      acceptance subset, and blockers.
- [ ] Implementer center lower is an evidence workspace with Top-3,
      `more_count`, `next_token`, and source-labeled read-only context.
- [ ] Implementer inspector upper is selected acceptance, evidence, or
      proof detail.
- [ ] Implementer inspector lower presents canonical actions first, then
      a hard-divided bridge adapter/proxy panel.
- [ ] `PKB-*` refs are secondary only, never primary authorities or
      dominant screen anchors.
- [ ] No unified PM record, no unified task record, no single "save
      everything" button is implied or rendered.
- [ ] `PKT-*` / `PKB-*` packet objects appear only as secondary
      compose-and-forward refs, never as primary screen anchors.
- [ ] PM left rail is a workflow / slice map. Implementer left rail is
      a work contract / support rail. Neither is a service / system map.
- [ ] Each PM and Implementer pane carries the four-field declaration
      (`domain`, `authority`, `role`, `next_action`).
- [ ] Authority is split per domain: Leantime (metadata),
      task-orchestrator (workflow), ConPort (decisions/progress),
      dope-memory (chronicle), dope-context (retrieval),
      repo-truth-extractor (extraction).
- [ ] Bridge segregation rule holds at every supported viewport (see
      Viewport Degradation Law in `ARCHITECTURE_SAFETY_OVERLAY.md`).
- [ ] ADHD/operator-support cues are advisory, source-labeled, never
      gates, never status chips.
- [ ] Serena is optional technical-context support only and remains
      `UNKNOWN` unless runtime authority is proven.
- [ ] repo-truth-extractor / repo-truth appears only as a Services child / workload
      surface, not PM or Implementer authority.
- [ ] dope-context is retrieval / support only, not source truth for
      acceptance, decisions, workflow state, or implementation success.

## Contradiction Gate

The package fails acceptance if any of the following appear anywhere in
the doctrine files (`README.md`, `PREIMPLEMENTATION.md`, this file,
`SKILL.md`) outside of an explicit forbidden-pattern list:

- `Every row carries SRC` / `Every data row carries SRC` /
  `every row in every pane carries SRC` / `every row carries one`.
- `Services authority: dopemux`.
- `command authority: dopemux`.
- `Bridge actions authority: dopecon-bridge`.
- `SRC=dopemux` used as canonical data provenance or in chrome.
- `UNKNOWN->EDGE`, `UNKNOWN -> EDGE`, `UNKNOWN=EDGE`
  used as positive doctrine.
- Any task-packet-forbidden named fallback font described as canonical,
  preferred, fallback, comparison baseline, or glyph source.

If any match is found, classify it as one of:

- allowed forbidden-pattern definition,
- PASS evidence,
- violation,
- UNKNOWN.

Patch all violations and rerun the affected validation commands listed
in the Re-running Acceptance section below.

## Pane-Level Acceptance

For each pane in any mock or implementation derived from this package:

- [ ] The four-field declaration is present and complete:
      `domain`, `authority`, `role`, `next_action`.
- [ ] Visual hierarchy matches the declared `role`. Canonical visual
      weight is reserved for canonical authority.
- [ ] Chrome panes (`role: chrome`) carry no `SRC=`, no canonical data
      labels, and no transition controls.
- [ ] Bridge panes are visually segregated with a hard divider, distinct
      framing, and explicit `adapter/proxy` labeling.
- [ ] `SRC` appears once per logical data/provenance record. Wrapped
      continuation rows align under the content column and do not
      repeat `SRC` unless physical rows are independently
      selectable/copyable.
- [ ] Status chips are drawn from the closed set only.
- [ ] `UNKNOWN` appears (if at all) as literal text in affected fields,
      never as a chip, never collapsed into `EDGE`.
- [ ] Color-only signal is not used. Removing color preserves meaning.

## Package-Level Acceptance

For the package as a whole:

- [ ] The Architecture Safety Overlay set is referenced from
      `README.md`: `ARCHITECTURE_SAFETY_OVERLAY.md`,
      `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`,
      `UX_REFERENCE_RECONCILIATION.md`, `PREIMPLEMENTATION.md`,
      `ACCEPTANCE.md`, `SKILL.md`.
- [ ] `PREIMPLEMENTATION.md` carries Architecture Safety Preconditions
      and explicit fail-closed rules.
- [ ] `ACCEPTANCE.md` carries the Contradiction Gate and the GPT-5.5
      Pro PM-Plane Integration Checklist.
- [ ] `SKILL.md` operational rules match the overlay.
- [ ] Dopemux Term Regular is named as the canonical brand mono. Dopemux
      Term Nerd Font Regular is named as the canonical rich-glyph terminal
      font. `ui-monospace`, `monospace`, and ASCII/text fallback are the
      only fallbacks after the Dopemux families.
- [ ] PLAIN and AUDIT modes are documented as log-safe and ANSI-free.
- [ ] Bridge phrasing is `Bridge adapter/proxy: dopecon-bridge`. The
      forbidden phrase `Bridge actions authority: dopecon-bridge` does
      not appear outside the forbidden-pattern list.

## Re-running Acceptance

Re-run these checks after any edit to the four merged doctrine files:

```
rg -n "UNKNOWN.?->.?EDGE|UNKNOWN.?->.?EDGE|UNKNOWN=EDGE" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/readme.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/preimplementation.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/acceptance.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/skill.md"

rg -n "Every row carries SRC|Every data row carries SRC|every row carries SRC|every row carries one|every row in every pane" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/readme.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/preimplementation.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/acceptance.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/skill.md"

rg -n "Bridge actions authority|Services authority: dopemux|command authority: dopemux|SRC=dopemux" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/readme.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/preimplementation.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/acceptance.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/skill.md"

rg -n "Canonical brand mono|UNKNOWN|Bridge adapter/proxy|Every logical data/provenance record carries SRC|Dopemux Term|Dopemux Term Nerd Font" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/readme.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/preimplementation.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/acceptance.md" \
  "docs/03-reference/Dopemux Cockpit TUI Design System/skill.md"
```

Classify every remaining match as: allowed forbidden-pattern definition,
PASS evidence, violation, or UNKNOWN. Patch violations and rerun the
affected check until all matches are accounted for.
