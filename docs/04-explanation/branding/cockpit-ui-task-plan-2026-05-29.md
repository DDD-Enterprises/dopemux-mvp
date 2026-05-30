---
id: cockpit-ui-task-plan-2026-05-29
title: "Dopemux Cockpit UI — Implementation Task Plan (index) — 2026-05-29"
type: reference
owner: brand-system
author: '@hu3mann'
date: 2026-05-29
last_review: '2026-05-29'
next_review: '2026-08-29'
status: current
prelude: "Human-readable index of the task-orchestrator tree DMX-COCKPIT-UI (root 43410d39): 34 self-contained, model-tagged, sequenced packets across 6 phases that implement the approved D3 cockpit design + D4 ADR. The orchestrator is the source of truth; this mirrors it for review."
---

# Dopemux Cockpit UI — Implementation Task Plan (index)

Mirror of the **task-orchestrator** tree **`DMX-COCKPIT-UI`** (root `43410d39`).
The orchestrator is the execution source of truth (`get_next_item` / `claim_item`
/ `advance_item`); this doc is the reviewable index.

- **Design source:** [D3 Cockpit Design System v1](../../03-reference/Dopemux%20Cockpit%20TUI%20Design%20System/cockpit-design-system-v1.md) · [D4 ADR](../../90-adr/adr-cockpit-tui-as-canonical-ui-hero.md) · [D1 audit](ui-consolidation-audit-2026-05-29.md) · [D2 research](../../06-research/investigations/ui-ux-research-brief-2026-05-29.md)
- **Design gate:** `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md` — `safe_for_claude_design: NO` until the 8 Phase-1 blockers close; `runtime_contract.py::build_runtime_render_model` enforces it.

## Shared Definition of Done (every packet)

1. Branch `cockpit-ui/<task-id>` off the integration branch.
2. Implement **only** this packet's scope; minimal correct change; obey the doctrine
   (per-domain authority; closed chip set; `SRC=` on data rows only; viewport law;
   cockpit core animation-free; ADHD advisory-only-in-core; brand voice out of cockpit chrome).
3. Self-audit — **global**: `python scripts/brand_lint.py` (0/0) + `python scripts/sync_brand_tokens.py` (exit 0) + relevant `pytest`; **plus** the packet's own audit. Report **PASS / FAIL / NOT_RUN**.
4. Conventional commit; end with the implementer's `Co-Authored-By` trailer.
5. Self-contained PR to the integration branch, linking the packet + D3/D4 §.
6. Codereview (`/code-review` or `pal/codereview`) at effort matching the impl tag; address findings.
7. Record proof in work/review notes: files changed, validation outputs, PR URL, codereview status.

## Model tags (cost-optimized)

| Tag | # | Used for |
|---|---|---|
| `impl-haiku` | 4 | mechanical / single-file, fully specified |
| `impl-sonnet` | 20 | standard implementation |
| `impl-opus` | 7 | safety-critical / architectural / final verification |
| `impl-codex` | 2 | mechanical code transforms / inventory |
| `impl-gemini` | 1 | large-context doc/repo reconciliation |

Tags are recommendations; a supervisor may reassign.

## Sequence

```
P0 Stabilize ─┐ (un-gated, start now)
P1 Gate ──────┤  P0 ∥ P1
  (8 blockers ─▶ GATE-FLIP)
              └─▶ P2 Cockpit core ─┬─▶ P3 Data wiring ─┐
                                   └─▶ P4 tmux+ADHD/web ┴─▶ P5 Converge
```

---

## Phase 0 — Stabilize (un-gated) · parent `8691af42`

| TP | Title | impl | cx | Depends | Acceptance (short) |
|---|---|---|---|---|---|
| P0-01 | Fix TCSS↔theme token drift | haiku | 2 | — | `sync_brand_tokens.py` exit 0 |
| P0-02 | Add cockpit to brand_lint coverage | sonnet | 3 | — | `brand_lint.py` 0/0 incl. cockpit |
| P0-03 | Fix broken web build (3 missing components) | sonnet | 4 | — | `npm ci && tsc --noEmit && build` green |
| P0-04 | React palette parity + `--saint-gold` | sonnet | 4 | — | 3-palette switch; sync passes |

## Phase 1 — Claude Design Gate (8 blockers) · parent `7fb6c62d`

| TP (canonical) | Title | impl | cx | Depends | Acceptance (short) |
|---|---|---|---|---|---|
| TP-…-COMMAND-PALETTE-001 | Command Palette broker | opus | 8 | — | broker-only; routes by class; never executes |
| TP-…-SAFE-ACTIONS-001 | Safe Action Gate (T0i–T6) | opus | 9 | — | wired across non-read; TX/TU fail closed; no auto-confirm |
| TP-…-SETTINGS-RUNTIME-001 | Settings/Admin/Runtime | sonnet | 7 | SAFE-ACTIONS | 9 flow groups; per-flow gates |
| TP-…-UNKNOWN-DRIFT-001 | Unknown/Drift Queue | sonnet | 6 | — | non-executable; 22 reason codes; read-only |
| TP-…-PACK-REMEDIATE-006-IA | Package IA reconcile | opus | 8 | — | 5 modes + 4 surfaces; no 6th-mode |
| TP-…-RUNTIME-RENDER-001 | Runtime renderer validation | opus | 8 | — | matches SCREEN_CONTRACT_MATRIX; blocked rows no destructive affordance |
| TP-…-INVENTORY-REGEN-001 | Regenerate command inventory | codex | 5 | — | inventory vs HEAD; counts reconciled / UNKNOWN |
| TP-…-EVIDENCE-LEDGER-001 | Reduce EVIDENCE_LEDGER UNKNOWNs | gemini | 5 | — | ledger UNKNOWNs resolved/rejected |
| TP-…-GATE-FLIP-001 | Verify 8 closed → flip gate | opus | 4 | **all 8 above** | gate flips; `build_runtime_render_model` passes |

## Phase 2 — Cockpit core · parent `3ddc5c24` (gated by Phase 1)

| TP | Title | impl | cx | Depends | Acceptance (short) |
|---|---|---|---|---|---|
| P2-01 | Frame + Rule primitives (grid) | sonnet | 6 | — | 3-column grid at 3 sizes; <80×24 BLOCKER |
| P2-02 | Chip + Row shared renderers | haiku | 3 | — | chips from enum; NO_COLOR literals |
| P2-03 | `validate_rendered_text` | sonnet | 5 | — | render path validated; UI closer-gap closed |
| P2-04 | Implementer mode pane-builder | sonnet | 5 | — | deterministic; declarations complete |
| P2-05 | Services mode + RTE child + Service/RunRow | sonnet | 6 | — | RTE child declares own authority; T5 lifecycle |
| P2-06 | Overview mode pane-builder | haiku | 4 | — | display+inspect only; no bridge |
| P2-07 | Events mode + RichLog feed | sonnet | 5 | — | mirrored feed; bounded ring-buffer; capture gated |
| P2-08 | `app.py` mode dispatch (5 modes) | sonnet | 5 | P2-01/02/04/05/06/07 | all 5 modes render; no ValueError |

## Phase 3 — Data wiring · parent `5b73ca23` (gated by Phase 2 + gate-flip)

| TP | Title | impl | cx | Depends | Acceptance (short) |
|---|---|---|---|---|---|
| P3-01 | Collector/worker integration (absorb neon) | opus | 7 | — | live workers; out-of-order safe; SRC/authority preserved |
| P3-02 | Wire PM panes live | sonnet | 6 | P3-01 | PM live; SRC correct |
| P3-03 | Wire Implementer/Services/Overview/Events live | sonnet | 6 | P3-01 | 4 modes live; SRC/authority correct |
| P3-04 | Retire STATIC_DEMO per-pane | sonnet | 3 | P3-02/03 | no false live claims; write scope labeled |

## Phase 4 — tmux + ADHD/web · parent `76e22743` (gated by Phase 2)

| TP | Title | impl | cx | Depends | Acceptance (short) |
|---|---|---|---|---|---|
| P4-01 | tmux hero session (status bar/keys/layout) | sonnet | 5 | — | deck launches; one cue, no emoji |
| P4-02 | Focus/HUD overlay (opt-in, static) | sonnet | 5 | — | opt-in only; static content; never gates |
| P4-03 | Web dashboard alignment (3 components) | sonnet | 6 | P0-03, P0-04 | 3 components on-brand + accessible; build green |

## Phase 5 — Converge & deprecate · parent `2e42b9a9` (gated by Phase 3 + 4)

| TP | Title | impl | cx | Depends | Acceptance (short) |
|---|---|---|---|---|---|
| P5-01 | Absorb neon fully; retire standalone | sonnet | 5 | P3-01 | no standalone neon app; collectors reused |
| P5-02 | Deprecate dashboard.py + dopemux_dashboard.py | haiku | 3 | P2-08 | deprecation notices; no orphan imports |
| P5-03 | Rebrand ConPort-Ink (Ink theme helper) | sonnet | 5 | — | no raw Ink colors; brand tokens |
| P5-04 | Extend brand_lint to TSX/HTML/bash (CI gate) | codex | 5 | — | lint covers new surfaces; CI fails on violation |
| P5-05 | Dedupe Leantime plugin triplication | sonnet | 4 | — | single source; token-driven CSS |
| P5-06 | Final E2E acceptance + proof + docs + memory | opus | 6 | **P5-01..05** (+ P3/P4) | D3 §11 green; proof bundle; gate flipped |

---

## How to drive it

- `get_next_item` (or `claim_item`) surfaces the next **unblocked** packet by deps + priority. **Phase 0 and Phase 1 are the two ready fronts** (parallel).
- Each packet's orchestrator `description` is the implementer's full brief — a cheaper model can execute one packet without the whole design in context.
- `query_items operation=overview itemId=43410d39` prints the live tree; `get_context mode=item itemId=<id>` shows a packet's gate/notes.
- Assign by the `impl-<model>` tag; record proof in each packet's work/review notes per the DoD.

> **Status (2026-05-29):** plan only — no packet implemented yet. D2 research is 1-of-5 streams (re-runnable). Nothing here lifts the `safe_for_claude_design: NO` gate; Phase 1 does.
