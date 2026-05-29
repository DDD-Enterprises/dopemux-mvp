---
id: adr-cockpit-tui-as-canonical-ui-hero
title: "ADR: Cockpit TUI as the canonical UI hero; surface consolidation"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-29'
last_review: '2026-05-29'
next_review: '2026-08-29'
prelude: Consolidate ~7 fragmented dopemux UI surfaces onto one canonical hero — the live Textual cockpit running in tmux — with the web dashboard as a secondary aligned surface, gated behind the existing Claude Design blockers.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-task-orchestrator-as-workflow-authority
    - adr-serena-as-technical-context-plane
    - COCKPIT_ARCHITECTURE_SAFETY_OVERLAY
    - COCKPIT_DESIGN_SYSTEM_V1
---

# ADR: Cockpit TUI as the canonical UI hero; surface consolidation

**Status:** Proposed
**Date:** 2026-05-29
**Owners:** Dopemux UI / Brand System / Cognitive Plane
**Decision Type:** Surface Authority / UI Architecture
**Scope:** `src/dopemux/ui/cockpit/`, `src/dopemux/ui/` render layer, `scripts/ui/neon_dashboard/`, `src/dopemux/ui/dashboard.py`, `scripts/dopemux_dashboard.py`, `ui-dashboard/`, `services/conport_kg_ui/`, `src/dopemux/tmux/`

════════════════════════════════════════════════════════════

## Status

* Proposed

## Date

* 2026-05-29

## Owners

* @hu3mann (brand-system / UI)

────────────────────────────────────────────────────────────

## Context

Dopemux UI work is real but **fragmented across ~7 surfaces that were never
unified** (evidence: [D1 — ui-consolidation-audit-2026-05-29](../04-explanation/branding/ui-consolidation-audit-2026-05-29.md)).
Two agent-driven workstreams ran in parallel and never merged: **"Palette"**
(dozens of PRs polishing the React web dashboard `ui-dashboard/`) and
**"Cockpit"** (`codex/cockpit-*` — an audited TUI design system + IA package).

Current state, verified at HEAD `755bf38460`:

* **Cockpit TUI** (`src/dopemux/ui/cockpit/`) — a live Textual shell exists
  (`app.py:68 CockpitApp`) but renders **PM only**; `app.py:113` raises
  `ValueError` for the other four modes, and PM data is **static demo**
  (`render.py:41 STATIC_DEMO_BANNER`). The renderer is a linear deterministic
  text emitter, not the grid `frame.py` the v0 doc described (that module does
  not exist).
* **Web dashboard** (`ui-dashboard/`) — **build is broken**: `App.tsx` imports
  `CognitiveLoadGauge`, `PredictionPanel`, `TeamDashboard`, all deleted from
  disk in `87ea13440`. React encodes only the `mint-mojo` palette (no parity
  with the three Python palettes).
* **Three overlapping TUIs** — the cockpit, `src/dopemux/ui/dashboard.py`, and
  `scripts/ui/neon_dashboard/` (~2,239 LOC, zero `theme.py` imports, broken
  tests). `scripts/dopemux_dashboard.py` ships a foreign Catppuccin/Nord
  palette.
* **ConPort-Ink** (`services/conport_kg_ui/`) — Ink TUI with raw `color="cyan"`
  strings, no brand tokens (`theme.ts` absent).
* **Token drift** — `sync_brand_tokens.py` **FAILs**: `theme.py TEXT_PRIMARY
  #E5E5E5` ≠ `dopemux.tcss $text #E2E8F0`. The cockpit is **not** in
  `brand_lint.py`'s allow-list, so the hero surface has no banned-vocab/chip
  enforcement.
* **A formal design gate is already in place and unmet.**
  `runtime_contract.py::build_runtime_render_model` sets
  `claude_design_blocked: True` / `safe_for_claude_design="NO"` and
  `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md §3`
  enumerates **8 open blocking conditions** before the cockpit may be presented
  as ready for final screens. IA verdict:
  `CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`.

The brand itself is mature (synced mint-mojo palette, voice system, 165+ ADHD
learnings, lint enforcement) and the cockpit doctrine is authoritative and
explicit ([ARCHITECTURE_SAFETY_OVERLAY.md](../03-reference/Dopemux%20Cockpit%20TUI%20Design%20System/ARCHITECTURE_SAFETY_OVERLAY.md),
the "REVISE, don't replace" verdict in
[PM_IMPLEMENTER_COCKPIT_REDIRECTION.md](../03-reference/Dopemux%20Cockpit%20TUI%20Design%20System/PM_IMPLEMENTER_COCKPIT_REDIRECTION.md)).
The problem is not a missing brand — it is the absence of **one canonical
operator experience**. The user has chosen the **TUI / tmux cockpit as the
hero** and asked for full implementation.

────────────────────────────────────────────────────────────

## Decision

**The live Textual cockpit running inside a branded tmux session is the
canonical dopemux UI hero.** All other UI surfaces align to it or are
deprecated. The unified design is specified in
[D3 — Cockpit Design System v1](../03-reference/Dopemux%20Cockpit%20TUI%20Design%20System/cockpit-design-system-v1.md);
that spec is **DIRECTION**, and implementation of final screens is **gated**
behind the 8 `CLAUDE_DESIGN_BLOCKERS.md` conditions.

Surface dispositions:

| Surface | Disposition |
|---|---|
| Cockpit TUI (`ui/cockpit/`) | **Canonical hero** — complete the 5 modes + 4 global surfaces + data wiring |
| `ui/` render layer (theme/voice/output/progress/splash) | **Keep** — shared token + primitive source the cockpit consumes |
| `neon_dashboard/` | **Absorb** — harvest its data layer (cache/dedup/rate-limit collectors) into the cockpit; retire the standalone app |
| `ui/dashboard.py` + `dashboard_detail.py` | **Deprecate** once cockpit reaches parity |
| `scripts/dopemux_dashboard.py` | **Deprecate** (foreign palette) |
| Web dashboard (`ui-dashboard/`) | **Secondary, aligned** — fix the build, add React palette parity, home for the rich (animated) ADHD visualizations |
| ConPort-Ink (`conport_kg_ui/`) | **Rebrand** via an Ink theme helper |
| tmux (`src/dopemux/tmux/`) | **Keep** — the hero's shell (status bar carrying the single ADHD cue, keybindings, layout) |

Invariants (binding):

* Authority is **per-domain**; the cockpit coordinates and never owns truth
  (Authority Model, overlay). dopemux is never the PM/task/decision authority.
* The **closed chip set** `LIVE BLOCKER OVERRIDE LOGGED AFTERCARE EDGE` is the
  only status vocabulary; color is secondary; `UNKNOWN` stays literal.
* `SRC=` on data rows only, never on chrome; `SRC=dopemux` forbidden.
* Viewport law: 120×40 / 100×32 / 80×24, BLOCKER below.
* The cockpit core is **animation-free**; motion (where allowed) is Textual
  `level="full"`, auto-suppressed at the shipped `TEXTUAL_ANIMATIONS=basic`.
* **ADHD support in the cockpit core is one advisory status-rail cue**, never a
  chip, never a gate. The rich, animated ADHD visualizations live on the tmux
  status bar, an opt-in Focus/HUD overlay, and the web dashboard.
* **Brand voice/persona** lives in splash/session-start/web/agent copy and is
  **suppressed in cockpit chrome and operator errors** (which use
  `Problem / Why / Fix / NEXT`).
* **The Claude Design gate is binding**: final cockpit screens are not approved
  until all 8 `CLAUDE_DESIGN_BLOCKERS.md` conditions hold and
  `safe_for_claude_design` can flip from `NO`.

Non-goals:

* A greenfield rebuild — this revises the existing doctrine + `render.py`.
* The cockpit owning or writing canonical data.
* Resurrecting closed/superseded "Palette" PRs.
* Renaming the design-system doc directory (deferred — separate task; touches
  `brand_lint` paths + inbound links).

────────────────────────────────────────────────────────────

## Alternatives Considered

**1. Web dashboard as the hero (Palette-forward).**
* Pros: live WebSocket data already wired; animation-friendly; the most
  actively-developed surface.
* Cons: contradicts the product identity (dopemux = dope+tmux), the
  terminal-first brand (Cockpit/HUD/Nerd-Font doctrine), and the operator-first
  voice. The web build is currently broken.
* Rejected: the brand, name, and doctrine are terminal-first; the web is a
  companion, not the flagship.

**2. Keep all surfaces, brand each in place.**
* Pros: least disruptive; matches the existing 8-wave rollout.
* Cons: fragmentation **is** the problem; three overlapping TUIs + an
  unbranded Ink UI guarantee continued drift and duplicated effort.
* Rejected: does not produce "one optimal UI/UX."

**3. Greenfield cockpit rebuild.**
* Pros: clean slate.
* Cons: discards a working deterministic renderer, an audited design system, a
  runtime IA contract, and the explicit "REVISE, don't replace" verdict.
* Rejected: high risk, ignores existing authority, violates minimal-correct-change.

────────────────────────────────────────────────────────────

## Consequences

**Positive**
* One canonical operator experience; the IA contract (`runtime_contract.py`) is
  honored, not bypassed.
* Brand coherence: the hero consumes `theme.py` tokens; drift is lintable.
* The ADHD/voice tension is resolved by placement, not compromise.
* The web dashboard becomes the deliberate home for rich ADHD visualization.

**Negative / costs**
* "Full implementation" is **gated** by the 8 design blockers — real
  prerequisite work (Command Palette, Safe Action Gate, Settings surface, Drift
  Queue, IA reconcile, runtime-render validation, inventory regen, evidence
  ledger), already scoped as `TP-DMX-COCKPIT-*` packets.
* Deprecations (`dashboard.py`, `dopemux_dashboard.py`, standalone neon) need a
  migration window so no capability is lost before parity.
* Absorbing the neon data layer is non-trivial integration.

**Failure modes removed**
* Silent palette drift on the hero (cockpit enters `brand_lint`).
* The web build staying broken unnoticed (CI build gate).

**Failure modes to watch**
* Flipping `safe_for_claude_design` prematurely — the build-time `[BLOCKER]`
  guard must remain until the 8 conditions genuinely hold.

────────────────────────────────────────────────────────────

## Migration Strategy

* **Step 0 — Stabilize** (no design changes): fix TCSS drift so
  `sync_brand_tokens.py` passes; add `ui/cockpit/*` to `brand_lint`
  `AUDITED_PYTHON_FILES`; decide the 3 web components (restore from
  `87ea13440^` or remove imports) so the web build is green.
* **Step 1 — Close the Claude Design gate**: execute the 8 `TP-DMX-COCKPIT-*`
  blocker packets (Command Palette broker, Safe Action Gate, Settings/Admin,
  Unknown/Drift Queue, IA reconcile to 5 modes, runtime-render validation,
  inventory regen, evidence-ledger UNKNOWNs).
* **Step 2 — Cockpit core**: add the four mode pane-builders + deterministic
  emitters; make `app.py` dispatch on mode; build the primitive widgets over
  `render.py`; wire the grid layout in TCSS at the three sizes; implement the
  real `validate_rendered_text` (D3 §9).
* **Step 3 — Data wiring**: feed panes from live services via Textual workers,
  authority/SRC-respecting; retire `STATIC_DEMO_BANNER` per-pane only when live.
* **Step 4 — tmux hero + ADHD/web**: status bar + keybindings + layout; Focus
  overlay; align/complete the web dashboard (3 components + palette parity).
* **Step 5 — Converge**: absorb neon collectors; deprecate `dashboard.py` /
  `dopemux_dashboard.py`; rebrand ConPort-Ink; extend `brand_lint` (Wave 8).

**Rollback:** all work on a feature branch; per-wave commits enable `git
revert`. Deprecated surfaces are removed only after the cockpit reaches parity,
so reverting a wave restores the prior surface.

────────────────────────────────────────────────────────────

## Verification

* Tests: `tests/unit/dopemux/ui/cockpit/*` (render, runtime_contract) extended
  for the four new modes + the validator; new pane-builder tests.
* Commands: `python scripts/brand_lint.py` → 0 errors;
  `python scripts/sync_brand_tokens.py` → pass; `pytest` for cockpit + neon;
  run `dopemux cockpit` at 120×40 / 100×32 / 80×24 and `<80×24` (BLOCKER);
  `NO_COLOR=1` and PLAIN/AUDIT emit ANSI-free deterministic output.
* Expected signals: the 8 `CLAUDE_DESIGN_BLOCKERS.md` conditions checkable;
  `safe_for_claude_design` flips to a non-`NO` value only when they hold;
  D3 §11 acceptance checklist green; `design:accessibility-review` confirms the
  contrast findings (D3 §10).

────────────────────────────────────────────────────────────

## Notes

* Deliverables: [D1 audit](../04-explanation/branding/ui-consolidation-audit-2026-05-29.md),
  [D2 research](../06-research/investigations/ui-ux-research-brief-2026-05-29.md),
  [D3 design system v1](../03-reference/Dopemux%20Cockpit%20TUI%20Design%20System/cockpit-design-system-v1.md).
* Gate authority: `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md`,
  `out/cockpit-pack-remediation/TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA/INTEGRATED_COCKPIT_IA_CONTRACT.md`.
* Open question: whether the neon data layer is absorbed wholesale or
  re-implemented against the event bus — to be resolved in Step 5 planning.
* To be logged to ConPort as a decision once accepted.
