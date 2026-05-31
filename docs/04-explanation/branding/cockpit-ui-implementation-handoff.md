---
id: cockpit-ui-implementation-handoff
title: "Dopemux Cockpit UI — Implementation Handoff (Codex pickup)"
type: explanation
owner: brand-system
author: '@hu3mann'
date: 2026-05-30
last_review: '2026-05-30'
next_review: '2026-08-30'
status: current
prelude: "Self-contained handoff for the agent (Codex) picking up the dopemux Cockpit UI implementation after the design phase + Phase 0. Encodes the verified state, the binding doctrine, the doc-vs-runtime traps, the design gate, the work list, the per-packet Definition of Done, and known pitfalls."
---

# Dopemux Cockpit UI — Implementation Handoff (Codex pickup)

> **You are picking up the implementation of the dopemux unified Cockpit UI.**
> The design is approved and committed; Phase 0 (stabilization) is done. Your job
> is to execute the remaining packets (Phases 1–5) — **one self-contained PR per
> packet** — obeying the doctrine and the design gate below. Everything you need is
> in the repo. **Runtime outranks docs (including this file): verify, don't trust.**

---

## 0. Mission in one paragraph

Consolidate dopemux's ~7 fragmented UI surfaces onto **one hero: the live Textual
cockpit running inside tmux**. The design is fully specified in **D3** (Cockpit
Design System v1) and decided in **D4** (ADR). The cockpit runtime today is a
**PM-only Textual shell** over a deterministic linear renderer, with 4 of 5 modes
stubbed and a build-time gate (`safe_for_claude_design: NO`) that blocks final
screens until 8 conditions close. Work the packets in dependency order, prove each
one, and do not lift the gate until it is genuinely earned.

## 1. Read these first (authority order, highest first)

1. **`AGENTS.md`** (repo root) — project governance, Truth Order, PAL chain rules, proof-and-finality. **Canonical.** Your final reports + proof bundles follow §8.
2. **The cockpit doctrine package** — `docs/03-reference/Dopemux Cockpit TUI Design System/` — **absolute authority on cockpit semantics:**
   - `ARCHITECTURE_SAFETY_OVERLAY.md` (wins on conflict), `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`, `acceptance.md`, `preimplementation.md`, `UX_REFERENCE_RECONCILIATION.md`.
3. **D3 — the spec you implement:** `docs/03-reference/Dopemux Cockpit TUI Design System/cockpit-design-system-v1.md` (IA for 5 modes + 4 global surfaces, ASCII mockups at 120×40/100×32/80×24, the component/primitive system mapped to `render.py`, spacing/type/motion, ADHD + voice reconciliation, the **text-validation contract** §9, measured contrast §10, the acceptance checklist §11).
4. **D4 — the decision:** `docs/90-adr/adr-cockpit-tui-as-canonical-ui-hero.md`.
5. **The work list:** `docs/04-explanation/branding/cockpit-ui-task-plan-2026-05-29.md` — 34 packets, phases, deps, per-packet acceptance, the shared Definition of Done.
6. **D1 — the audit (surface state + gaps):** `docs/04-explanation/branding/ui-consolidation-audit-2026-05-29.md`.
7. **The design gate:** `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/CLAUDE_DESIGN_BLOCKERS.md` (§3 = the 8 exact unblock conditions) + siblings (`CLAUDE_DESIGN_GATE.md`, `PROOF.json`, `EVIDENCE_LEDGER.md`, `COMMAND_PALETTE_SPEC.md`, `COMMAND_EXPOSURE_POLICY.json`, `SCREEN_CONTRACT_MATRIX*`) and `out/cockpit-pack-remediation/TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA/INTEGRATED_COCKPIT_IA_CONTRACT.md`.
8. D2 research (partial — see §10 pitfalls): `docs/06-research/investigations/ui-ux-research-brief-2026-05-29.md`.

## 2. Non-negotiable doctrine (obey on every packet)

- **Authority is per-domain. dopemux is the coordinator/chrome — never the PM/task/decision truth owner.** Leantime = PM metadata; task-orchestrator = workflow legality/transitions; ConPort = decisions/progress; dope-memory = chronicle; dope-context = retrieval; dopecon-bridge = adapter/proxy ONLY (never authority, visually segregated); ADHD Engine = advisory cues only; repo-truth-extractor = Services child.
- **Every pane declares four fields:** `domain / authority / role(canonical|derived|mirrored|proxied|authoring|chrome) / next_action`. Visual weight is an authority claim — demote derived/mirrored/proxied/advisory.
- **`SRC=<service>` on data rows + inspector + bridge lines only — never on chrome** (mode bar, command rail, status rail, frame). `SRC=dopemux` is forbidden.
- **Closed chip set: `LIVE BLOCKER OVERRIDE LOGGED AFTERCARE EDGE`.** Color is secondary; chips must survive `NO_COLOR` as bracketed literals. `UNKNOWN` is literal text, **never** a chip (never collapse to EDGE). Map external vocab only at the boundary (`DEGRADED→OVERRIDE`, `FAILED→BLOCKER`, `BLOCKED→BLOCKER`, `SYNC→AFTERCARE`).
- **Viewports: 120×40 (north star), 100×32, 80×24; below 80×24 = single BLOCKER panel.** Character-grid breakpoints, not viewport reflow; no parallel layout trees.
- **The cockpit core is animation-free and keyboard-only** (no mouse/hover; active row = leading `>`; press = bracketed `[N]`). Ship Textual at `TEXTUAL_ANIMATIONS=basic`; tag any non-essential motion `level="full"` (auto-suppressed); deterministic/test core = `TEXTUAL_ANIMATIONS=none`.
- **ADHD support in the cockpit core = exactly one advisory status-rail cue** (source-labeled `adhd-engine`), never a chip, never a gate. Rich/animated ADHD lives on the **tmux status bar + an opt-in Focus/HUD overlay + the web dashboard**.
- **Brand voice/persona lives in splash/session-start/web/agent copy — suppressed in cockpit chrome + operator errors**, which use `Problem / Why / Fix / NEXT` and neutral operator voice. No emoji in operator surfaces.
- **Map every visual to the primitive set:** `Frame, PaneHeader, Rule, Row, Chip, ServiceRow, RunRow, ModeBar, CommandRail, StatusRail, Inspector, BridgeSegregator`. **Build on `render.py` — do not invent a parallel renderer.**
- **Tokens (no new hex; import from `theme.py`):** ritual-cyan `#7DFBF6` (LIVE/heading), serum-mint `#94FADB` (LOGGED), gremlin-pink `#FF8BD1` (BLOCKER), gilt-edge `#F5F26D` (OVERRIDE), aftercare-violet `#9B78FF` (AFTERCARE), mint-dim `#4A9E94` (border/muted), ink-black `#020617` (bg), void-navy `#041628` (alt-row). Mono = Iosevka Hue Term → JetBrains Mono Nerd Font.

## 3. CRITICAL — doc↔runtime divergence (verify everything)

The v0 design README references modules + a validator that **DO NOT EXIST** at HEAD. Confirmed in D1.

| v0 doc says | Runtime reality |
|---|---|
| `cockpit/tokens.py`, `frame.py`, `model.py` | **absent** — dir is `__init__.py`, `app.py`, `render.py`, `runtime_contract.py` |
| `cockpit/tokens.py::validate_rendered_text` | **absent** — zero hits repo-wide |

**The real renderer:** `src/dopemux/ui/cockpit/render.py` is a **linear, deterministic, ANSI-free text emitter** — `pm_panes()` returns 6 `PaneRender`s; `render_pm(cols, rows)` emits `## title` + four-field declaration + `SRC=` + body + a `---` chrome rail; `viewport_supported()`, `_bridge_role_for_viewport()`, `TOO_SMALL_MESSAGE`. The **grid is the Textual app's job** (the `Frame`/`Rule` primitives are NEW — packet P2-01), fed by `render.py` data.
**`app.py:113`** raises `ValueError` for any mode ≠ `pm` (packet P2-08 fixes this).
**The real text-enforcement path:** `services/shared/brand_voice.py` → `src/dopemux/voice/core.py::validate_output` → `scripts/brand_lint.py` → the `StatusChip` enum in `src/dopemux/ui/theme.py`. D3 §9 specifies implementing a real `validate_rendered_text` and the `Surface.UI` closer-enforcement gap to close (packet P2-03).

**Rule: if this handoff, D3, or any doc conflicts with the runtime, the runtime wins — fix the doc and tell the user.**

## 4. The design gate (bounds what you may ship)

`runtime_contract.py::build_runtime_render_model` sets `claude_design_blocked: true` / `safe_for_claude_design: "NO"` and raises `[BLOCKER]` until the **8 conditions** in `CLAUDE_DESIGN_BLOCKERS.md §3` all hold. Those 8 conditions **are** the Phase-1 packets. Pre-design primitive drafting is explicitly permitted (gate §5) — so Phase-2 primitives may proceed in parallel. **Do not flip the gate** (packet `TP-DMX-COCKPIT-GATE-FLIP-001`) until all 8 genuinely hold; the build-time guard must stay until then.

## 5. The work list & order

Source of truth for tasks: the **task-orchestrator** tree **`DMX-COCKPIT-UI`** (root id `43410d39-454e-4ca3-8c4c-200b2cb30970`) **and** the human-readable mirror `cockpit-ui-task-plan-2026-05-29.md`.

- **If you have the `task-orchestrator` MCP:** `query_items operation=overview itemId=43410d39` shows the tree; `get_next_item` / `claim_item` / `advance_item` drive it; record proof in each packet's work/review notes (`manage_notes`). Tags `impl-<model>` were cost hints for a mixed fleet — **you (Codex) own all of it now; treat them as advisory.**
- **If you don't:** use the task-plan doc as the work list and report status to the user.

**Phase status & order:**
```
Phase 0 Stabilize ........ DONE (4/4, committed)
Phase 1 Gate (8 blockers ⟶ GATE-FLIP) ... NEXT — the front that lifts the gate
Phase 2 Cockpit core (5 modes + Frame/Rule/Chip/Row + validate_rendered_text + app.py dispatch)
Phase 3 Data wiring (gated by GATE-FLIP + Phase 2)
Phase 4 tmux hero + Focus overlay + web alignment (P4-03 web-align is already claimable — its P0 deps are done)
Phase 5 Converge & deprecate + final E2E acceptance
```
Intra-phase deps that matter: SETTINGS-RUNTIME ← SAFE-ACTIONS; GATE-FLIP ← all 8 blockers; P2-08 dispatch ← the mode-builders + Frame/Chip; P3-02/03 ← P3-01; P3-04 ← P3-02/03; P4-03 ← P0-03+P0-04 (done); P5-06 final ← all P5.

**Phase-1 gate-blocker → artifact map** (each blocker conforms to a carried artifact):

| Packet | Build | Key artifacts to conform to |
|---|---|---|
| `…COMMAND-PALETTE-001` | broker-only palette (never executes; routes by class) | `COMMAND_PALETTE_SPEC.md` §2, `COMMAND_PALETTE_POLICY.md`, `COMMAND_EXPOSURE_POLICY.json`; invariant `palette_broker_only` |
| `…SAFE-ACTIONS-001` | Safe Action Gate, tiers T0i–T6; TX/TU fail closed | `SAFE_ACTION_GATES.md`; `runtime_contract.py:70 SAFE_ACTION_TIERS` |
| `…SETTINGS-RUNTIME-001` | 9 flow groups + per-flow gates | `runtime_contract.py:92 SETTINGS_ADMIN_FLOW_GROUPS` |
| `…UNKNOWN-DRIFT-001` | non-executable queue, 22 reason codes, read-only affordances | `runtime_contract.py:37 UNKNOWN_DRIFT_REASON_CODES`, `:62 ALLOWED_UNKNOWN_DRIFT_AFFORDANCES` |
| `…PACK-REMEDIATE-006-IA` | IA = 5 modes + 4 surfaces, no 6th-mode | `REVISED_COCKPIT_IA.md`, `INTEGRATED_COCKPIT_IA_CONTRACT.md`; `runtime_contract.py:1350` |
| `…RUNTIME-RENDER-001` | renderer vs contract matrix; no destructive affordance on blocked rows | `SCREEN_CONTRACT_MATRIX*`, `PROOF.json` |
| `…INVENTORY-REGEN-001` | regen inventory vs HEAD; reconcile counts / explicit UNKNOWN | the inventory artifacts + `tests/unit/dopemux/ui/cockpit/test_inventory_regen_artifacts.py` |
| `…EVIDENCE-LEDGER-001` | resolve/reject the open ledger UNKNOWNs | `EVIDENCE_LEDGER.md` |

## 6. Per-packet Definition of Done

1. **Branch** `codex/cockpit-ui-<packet-id>` off the integration branch (§7).
2. **Implement only** that packet's scope; minimal correct change; obey §2; build on `render.py`.
3. **Audit** — global: `python scripts/brand_lint.py` (0/0) + `python scripts/sync_brand_tokens.py` (exit 0) + relevant `pytest`; plus the packet's own audit. Report **PASS / FAIL / NOT_RUN** (never collapse NOT_RUN into PASS).
4. **Conventional commit** referencing the packet id; `Co-Authored-By` trailer.
5. **PR** to the integration branch, self-contained, linking the packet + the D3/D4 §.
6. **Codereview** (PAL `codereview` or your reviewer) at effort matching risk; address findings.
7. **Proof bundle** per `AGENTS.md §8` (TP id, branch, files, validations w/ exit codes, codereview status, commit SHA, PR URL, residual risks, UNKNOWNs). Record proof in the orchestrator notes if available.

## 7. Current git state (where to start)

- **Integration branch:** `claude/hungry-buck-67a0d3` (a worktree). **HEAD = `c50150978`.** Confirm with the operator whether to base your `codex/*` branches on this branch directly or whether it gets merged to `main` first.
- **Commits so far (all this initiative):** `9e75ddac1` D1–D4 design docs · `930483ae4` task-plan index · `3462179fa` P0-01 · `27266f2f4` P0-02 · `c87aedc70` P0-04 · `c50150978` P0-03.
- **Phase 0 verified at HEAD:** `sync_brand_tokens` exit 0 · `brand_lint` 0/0 (cockpit now covered) · `ui-dashboard` build green · working tree clean.

## 8. Tooling / audit commands

```
python scripts/brand_lint.py            # must be 0 errors / 0 warnings (cockpit is now in scope)
python scripts/sync_brand_tokens.py     # must exit 0 (theme.py ↔ dopemux.tcss ↔ theme.ts)
python -m pytest tests/unit/dopemux/ui/cockpit/ -q   # cockpit unit tests (94 green at HEAD)
dopemux cockpit                          # run the TUI; verify at 120x40 / 100x32 / 80x24; try NO_COLOR=1 + PLAIN/AUDIT
cd ui-dashboard && npm ci --legacy-peer-deps && npx tsc --noEmit && npm run build   # web (see pitfall below)
```

## 9. Known issues / pitfalls (don't rediscover these)

- **`npm ci` needs `--legacy-peer-deps`** — pre-existing `eslint@10` ↔ `eslint-plugin-react-hooks@4.6.2` lockfile conflict. (Fixing the lockfile is a fair side-task; flag it.)
- **Pre-existing `Accessibility.test.ts` failure** — `App.tsx` aria-label `"Copy AI Recommendation:"` vs the test's expected pattern. Predates this work; fix only if you touch that area (or as a tracked side-task).
- **Open brand decision — canonical body-text hex:** P0-01 made `theme.py`'s `#E5E5E5` canonical (aligned `dopemux.tcss $text` to it) so `sync_brand_tokens` passes; **D3 §10's contrast table cites `#E2E8F0`.** Ask the operator which is canonical before changing it; if `#E2E8F0` wins, flip `theme.py` (1 line) and re-verify contrast.
- **`PredictionPanel.tsx` has 4 raw hex literals** with a `TODO(P4-03)` — `brand_lint` does NOT cover TSX yet (that's packet P5-04); fold the token replacement into P4-03.
- **`render.py` is a linear emitter, not a grid framebuffer** — the grid lives in the Textual layer (P2-01 `Frame`/`Rule`). The mode pane-builders (`render_implementer/services/overview/events`) mirror `render_pm`'s pattern (deterministic text), so they can be built in parallel; `app.py` dispatch (P2-08) is what consumes them + the primitives.
- **D2 research is partial** (1 of 5 streams; the other four were web-rate-limited and are marked `NOT_SYNTHESIZED`/`PENDING`). The design leaned on the doctrine + runtime + the complete dataviz/Textual stream. Re-running the exemplar-TUI/ADHD/tmux/a11y streams is optional polish — **not** a blocker for any packet.
- **Don't over-claim.** `safe_for_claude_design` flips only via the GATE-FLIP packet after all 8 conditions are genuinely evidenced.

## 10. What "done" looks like for the whole initiative

The final packet (`TP-COCKPIT-UI-P5-06`) is the acceptance gate: D3 §11 checklist all green, the AGENTS.md proof bundle complete, the gate flipped, all duplicate surfaces converged/deprecated, `brand_lint` + `sync_brand_tokens` + the full cockpit/web suites green, and the cockpit runs live in tmux across the three viewports. Log the consolidation decision to ConPort and update the docs index when accepted.
