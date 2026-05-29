---
id: ui-consolidation-audit-2026-05-29
title: "Dopemux UI Consolidation & Audit (D1) — 2026-05-29"
type: reference
owner: brand-system
author: '@hu3mann'
date: 2026-05-29
last_review: '2026-05-29'
next_review: '2026-08-29'
audit_scope: repo-wide UI surfaces (delta vs 2026-04-21)
status: current
prelude: "Delta audit of dopemux UI surfaces vs the 2026-04-21 design-system audit; canonical-surface recommendation and gap list feeding the cockpit redesign (D1)."
---

# Dopemux UI Consolidation & Audit Report (D1)

**Type:** DELTA vs `design-system-audit-2026-04-21.md` (baseline 62/100)
**Date:** 2026-05-29 | **HEAD:** `755bf38460` | **Mode:** read-only audit
**Evidence basis:** All headline claims independently verified at HEAD; sub-scores and unverified counts attributed to source Reports A–E.

---

## 1. Summary

**What changed since 2026-04-21:** One regression in the original surface set, one newly-discovered unbranded surface, zero rollout-wave enablers started. UI engineering momentum was real but narrow — ~30 commits, all in the React dashboard (the "Palette" series: a11y, iconography, copy-to-clipboard, signal-feed scannability). No commits touched `theme.py`, shell layers, Leantime, the Ink TUI, or any Wave 0–8 enabler.

**Brand-score delta:** Decomposed, not a single number (scope-dependent, INFERRED — sub-scores are judgment per Reports A/C/D):

| Scope | Score | Driver |
|---|---|---|
| Original audit surface set | 62 → **~61** | Single regression: TCSS drift (`TEXT_PRIMARY` ≠ `$text`) fails `sync_brand_tokens`, knocks core CLI 9→8. All other original surfaces flat. |
| + newly-inventoried `neon_dashboard` | **~56** | Re-baseline, not regression: ~2,239 LOC of zero-brand Rich TUI that did not exist in the April scope. |

**Verdict:** The brand system has not advanced; it has slightly regressed and gained a debt surface. The April roadmap remains well-scoped but unstaffed — Wave 0 enablers (which gate Waves 1–8) are untouched, so the design system cannot expand. Meanwhile the React dashboard **will not build** (INFERRED: three components imported but deleted from disk) and a separate, unrelated regression deleted the orchestrator config/docs on `main`. The hero — a data-wired live cockpit — has a working deterministic PM shell but is entirely static demo data with no live wiring and 4 of 5 modes stubbed. Priority is stabilization (fix build, fix TCSS drift) before any redesign.

---

## 2. Surface Inventory & Maturity / Overlap Matrix

Seven surfaces. Brand scores carried from baseline/Reports (INFERRED where noted); maturity verified at HEAD.

| # | Surface | Path | Type | Maturity | Brand score | Overlap | Disposition |
|---|---|---|---|---|---|---|---|
| 1 | **Cockpit TUI** (hero) | `src/dopemux/ui/cockpit/` | Textual app + deterministic render | **WIP** — live shell, PM-only, static demo data, 4/5 modes stubbed | UNKNOWN (out of `brand_lint` allow-list) | Canonical PM flight-deck; consumes `theme.py` chips | **KEEP** (canonical TUI target) |
| 2 | **UI render layer** | `src/dopemux/ui/theme.py`, `dashboard.py`, `service_endpoints.py`, `dashboard_detail.py` | Branded Rich/Textual primitives | **Working** — well-factored, themed | 8/10 (was 9, TCSS drift) | Source of truth for chips/glyphs/styled\_\* | **KEEP** (canonical token + primitive source) |
| 3 | **neon_dashboard** | `scripts/ui/neon_dashboard/` | Alt Textual split-pane TUI | **WIP** — richer data layer (cache/dedup/rate-limit); tests broken | ~0/10 (zero `theme.py` imports; hardcoded `style="red"`) | Parallel to #2; independent data pipeline | **ABSORB** (rebrand into #2's token system; reuse collectors) |
| 4 | **dashboard.py (ADHD)** | `src/dopemux/ui/dashboard.py` backend path | Branded CLI "light" TUI | **Working** | 9/10 core / 5/10 ADHD backend | Functional overlap w/ cockpit + neon | **KEEP standalone** (disputed — see §7) |
| 5 | **web / Palette** | `ui-dashboard/` | React + Vite + MUI dashboard | **WIP** — build broken (INFERRED); a11y polished | 9/10 (design+a11y), mint-mojo only | None (only web surface) | **KEEP + rebrand** (palette parity + build fix) |
| 6 | **ConPort-Ink** (KG UI) | `services/conport_kg_ui/` | Ink/React TUI | **Stub/raw** — `theme.ts` ABSENT; raw `color="cyan"` | 2/10 | None | **REBRAND** (Wave 5) |
| 7 | **tmux** | `.tmux.conf`, `scripts/ui/tmux_metamcp_controller.py`, `test_tmux_integration.sh` | tmux↔MetaMCP role-switch control plane | UNKNOWN (not audited by any report) | UNKNOWN | Hosts/launches other TUIs | **KEEP** (chrome/control plane; not a brand surface per se) — *needs dedicated audit* |

*Adjacent unbranded surfaces from baseline (not re-scored, all flat): monitoring-dashboard FastAPI HTML (2/10), `dopemux_dashboard.py` foreign palette (2/10), mobile status dashboard (1/10), Leantime plugin (2/10, triplicated).*

---

## 3. Live Cockpit Shell State (the hero)

### Implemented vs gap to data-wired live cockpit

| Aspect | State | Evidence (HEAD-verified) |
|---|---|---|
| Live Textual app | OBSERVED | `app.py:68 class CockpitApp(App)` |
| PM mode render | OBSERVED (real structure) | `render.py:299 def render_pm`; 6 panes |
| Data | **Static demo only** | `render.py:41 STATIC_DEMO_BANNER = "STATIC DEMO  NO WRITES  no live PM mutations"`; fake IDs (`DMX-COCKPIT-PM-TEXTUAL-001`) |
| Implementer/Overview/Services/Events | **STUBBED** | `app.py:113-114 if mode != "pm": raise ValueError`. No `render_implementer/overview/services/events` functions exist. |
| Viewport law | OBSERVED | `viewport_supported` (`render.py:263`); tiers 120×40 / 100×32 / 80×24; `TOO_SMALL_MESSAGE` (`render.py:43`) |
| Live data wiring | **NOT OBSERVED** | No API calls, no task-orchestrator/ConPort integration, no refresh loop (`render_pm` called once at construction) |

**Gap to live:** wire 6 panes to live services (task-orchestrator blockers/queue, ConPort decisions, Leantime, bridge `transport_ref`); add Textual refresh (`on_mount`/`watch_*`); implement the 4 stubbed modes; add the 4 remaining global surfaces defined in `runtime_contract.py:30-35` (Command Palette, Settings/Admin/Runtime, Safe Actions/Proof Gate, Drift Queue) — currently declared, not rendered.

### Doc-vs-runtime divergence (CONFIRMED at HEAD)

The v0 design doc references modules and an enforcement function that **do not exist**:

| Doc reference | Runtime reality at HEAD |
|---|---|
| `cockpit/tokens.py` | **ABSENT** — dir contains only `__init__.py`, `app.py`, `render.py`, `runtime_contract.py` |
| `cockpit/frame.py` | **ABSENT** |
| `cockpit/model.py` | **ABSENT** |
| `cockpit/tokens.py::validate_rendered_text` | **ABSENT** — `grep` returns zero hits repo-wide |

**The REAL enforcement path** (OBSERVED — runtime outranks doc):
1. `services/shared/brand_voice.py:55 brand_text()` → `validate_or_fallback(...)` — service-layer voice gate.
2. `src/dopemux/voice/core.py:182 validate_output()` — lexical + UI-tone gates (`_UI_TONE_RE` at line 100 blocks "public shame|roast escalation|shame you").
3. `scripts/brand_lint.py` — static AST lint over an allow-list.
4. `StatusChip` enum in `src/dopemux/ui/theme.py` — six chips (LIVE/BLOCKER/OVERRIDE/LOGGED/AFTERCARE/EDGE).

**Critical gap:** the cockpit module is **NOT** in `brand_lint.py`'s `AUDITED_PYTHON_FILES`. Cockpit demo text hardcodes `[LIVE]`/`[LOGGED]`/`[EDGE]` strings with no automated validation. Voice enforcement flows at the service layer; cockpit render text passes through neither `validate_output()` nor `brand_lint`.

---

## 4. Rollout-Wave Status (8 waves from 2026-04-21)

| Wave | Focus | Status | What remains (verified) |
|---|---|---|---|
| **0** | Enablers (React palette parity, Ink theme, bash helper, brand CSS, lint ext, how-to) | **PARTIAL** | Python multi-palette engine DONE (`theme.py:52-65 _PALETTES` = mint-mojo, pastel-neon-dreamscape, pastel-neon-dreams). React: single mint-mojo only, no `brandPalettes`/`DOPEMUX_THEME`. Bash helper, Ink theme, brand CSS partial, how-to, warn-only lint ext: all NOT_FOUND. |
| **1** | Python scripts (`dopemux_dashboard.py`, `realtime_status_updater.py`) | **NOT_STARTED** | Foreign `COLORS` dict persists; no `theme.py` import. (Add `neon_dashboard` here — see §6.) |
| **2** | Shell surfaces (`status-dashboard.sh`) | **NOT_STARTED** | No `brand.sh`; blocked on Wave 0 bash helper. |
| **3** | FastAPI inline HTML (monitoring-dashboard) | **NOT_STARTED** | No brand CSS; HTML not extracted. |
| **4** | Leantime dedupe + rebrand | **NOT_STARTED** | Triplication CONFIRMED at HEAD: `plugins/Dopemux`, `docker/leantime/app/Plugins/Dopemux`, `docker/leantime/docker/leantime/plugins/Dopemux` all present. |
| **5** | Ink TUI (ConPort KG UI) | **NOT_STARTED** | `services/conport_kg_ui/src/theme.ts` ABSENT (confirmed); raw Ink colors persist. |
| **6** | `proof/epic-rte/` triage | **NOT_STARTED** | Not triaged; no status README (per Report A). |
| **7** | RTE greenfield (repo-truth-extractor) | **NOT_STARTED** | No `ui_output.py` / Rich progress panel (per Report A). |
| **8** | Hardening (CI gate, docs, metrics) | **NOT_STARTED** | `brand_lint` not flipped to fail-on-error; no visual regression test; `BRAND_SYSTEM.md` surfaces table not updated. |

---

## 5. Instrument Readings

| Instrument | Bucket | Output | Caveat |
|---|---|---|---|
| `python scripts/brand_lint.py` | **PASS** (exit 0) | `0 errors, 0 warnings` | Coverage = allow-list only (core CLI). Cockpit, neon, scripts, HTML, Ink **excluded**. PASS ≠ codebase brand-clean. |
| `python scripts/sync_brand_tokens.py` | **FAIL** (exit 1) | `❌ Brand token drift detected: • TCSS drift: TEXT_PRIMARY=#E5E5E5 but $text=#E2E8F0` | `theme.py:81 TEXT_PRIMARY="#E5E5E5"` vs `dopemux.tcss:10 $text: #E2E8F0`. Stale TCSS not regenerated after dynamic-palette refactor. |
| `pytest scripts/ui/neon_dashboard/tests/` | **NOT_RUN** | 4 collection errors, 0 tests collected | `ModuleNotFoundError: No module named 'scripts.neon_dashboard'` — tests import a path (`scripts.neon_dashboard`) that does not match the real package (`scripts.ui.neon_dashboard`). Orphaned, not in CI. *(Report D attributed one error to missing `textual`; at HEAD all 4 are collection-time import-path errors.)* |
| `ui-dashboard` build (`tsc`/vite) | **NOT_RUN** | — | `node_modules` absent, no local `tsc`. Build-failure claim is INFERRED (see §6). |

---

## 6. Off-Branch / Closed-PR Triage + Regression Verification

### Branch / PR triage (per Report E)

| Category | Finding | Action |
|---|---|---|
| Cockpit branches (`codex/cockpit-*`) | 5 branches, all MERGED (PR #535, #597, #585, #572, #587) — design system + docs/coordination | KEEP history; GC worktrees |
| Palette PRs | 40+ (Feb–May), all MERGED/CLOSED by design; work captured in `main` | Historical reference |
| `restore/orchestrator-infra-palette-clobber` | UNMERGED, untraced | INVESTIGATE — palette-revert risk |
| Dead/superseded | Stale `claude/*` worktrees; old Palette PRs (Feb/Apr) subsumed by May series; `feat/cockpit-reset-ritual...` (PR #580) landed elsewhere | Do not resurrect |

### Regression A — React build (INFERRED, stronger than Report C)

Three components are **statically** imported at top level but **deleted from disk**:
- `App.tsx:41/43/45` import `CognitiveLoadGauge`, `PredictionPanel`, `TeamDashboard`; rendered at `App.tsx:721/732/737`.
- Files ABSENT (`src/components/` contains only `TaskSequencer.tsx`). No vite alias / index shim.
- Deleted in **`87ea13440` ("ci: implement public image fallback for container builds", PR #357)** — *Report C's "Vite migration" label is wrong; this is the actual commit message.*

**Correction to Report C:** static top-level imports of missing modules fail at **build/bundle-resolution time**, not merely at runtime. Marked **INFERRED** (build NOT_RUN — no `node_modules`). Verification: `npm ci && npx tsc --noEmit` in `ui-dashboard/`.

### Regression B — orchestrator infra clobber (headline CONFIRMED)

- `.taskorchestrator/config.yaml`: **GONE at HEAD** (confirmed).
- Per Report E + project memory: commit `d8e0268d3` (stale Jules/Gemini PR #720) deleted ~629 lines of CS-SURFACE infra (config.yaml + 14 `/dx` command docs + note-filling protocol + ADR). UI React code NOT reverted. The 629-line count and specific doc files are attributed to Report E (not independently re-counted).
- **Recovery path (per project memory, not verified here):** infra recoverable from `origin/task-orchestrator-claude-surface`. PR #724 (Path B hooks) partially restores enforcement.

---

## 7. Canonical-Surface Recommendation

**Survives (canonical):**
- **`src/dopemux/ui/theme.py`** — single source of truth for tokens, `StatusChip`, `Glyphs`, `styled_*` primitives. Everything Python-side must import from here. *Fix TCSS drift first.*
- **Cockpit TUI** (`src/dopemux/ui/cockpit/`) — canonical operator flight-deck once data-wired. Add it to the `brand_lint` allow-list.
- **web/Palette** (`ui-dashboard/`) — sole web surface; canonical browser dashboard. *Fix build + add palette parity.*

**Absorb:**
- **neon_dashboard** → rebrand into `theme.py` tokens (swap `style="red"` → `StatusChip.BLOCKER`, adopt `styled_panel/gauge/table`). Its data layer (multi-tier cache, dedup, rate-limit) is more advanced than core `dashboard.py` and worth harvesting. Same Rich/Textual stack → low-effort merge.

**Deprecate / rebrand:**
- **ConPort-Ink** → rebrand (Wave 5; `theme.ts` must be created).
- **Leantime triplication** → dedupe to one source (Wave 4 prerequisite; needs Dockerfile coordination).
- Foreign-palette `dopemux_dashboard.py`, monitoring HTML, mobile dashboard → rebrand per Waves 1–3.

**Open dispute (surfaced, not resolved):** `dashboard.py` standalone vs cockpit absorption.
- *Report D:* KEEP standalone — well-factored "light" quick-check TUI vs cockpit's heavier flight-deck; no merge.
- *Implicit consolidation pressure:* three overlapping TUIs (cockpit, dashboard.py, neon) is the redundancy the consolidation effort exists to reduce.
- **Recommendation:** resolve via explicit role split — cockpit = stateful PM/live operator deck; `dashboard.py` = stateless health glance; neon = absorbed for data-layer reuse. Do not merge `dashboard.py` into cockpit until cockpit is data-wired.

---

## 8. Gap List for the Redesign

| Gap | State (verified) |
|---|---|
| **Spacing scale** | ABSENT both layers. `theme.py` has no spacing tokens (only a `COMPACT` enum value at line 371); `theme.ts` exposes MUI default spacing only, no explicit scale. |
| **Type scale** | PARTIAL React / ABSENT Python. `theme.ts:108-114` defines h1/h2/h3/h6 + base `fontSize:15` + `letterSpacing` (incomplete — no h4/h5/body scale). `theme.py` has no type scale. |
| **Motion policy** | ABSENT as tokens. CSS-level transitions/animations exist ad hoc in `App.tsx` (per Report C) but no token-level duration/easing policy in either theme. |
| **3 web components** | MISSING from disk: `CognitiveLoadGauge`, `PredictionPanel`, `TeamDashboard` (imported, breaks build). Decide: restore from `87ea13440^` or remove imports + conditional renders. |
| **React palette parity** (Drift #1) | UNRESOLVED. `theme.ts` hardcodes mint-mojo; no `brandPalettes[name]`, no `DOPEMUX_THEME` consumption. `DOPEMUX_THEME=pastel-neon-dreamscape` switches CLI, leaves React on mint-mojo. |
| **Saint Gold CSS var** (Drift #2) | In `theme.ts:12 saintGold:'#FFCF78'` but missing as a CSS custom property → blocks plain-HTML/Leantime CSS consumers. |
| **TCSS↔Python parity** | Broken (`TEXT_PRIMARY` ≠ `$text`); no generator keeps TCSS in sync — only `sync_brand_tokens` detects drift reactively. |
| **Cockpit lint coverage** | Cockpit out of `brand_lint` allow-list → no banned-vocab enforcement on the hero surface. |
| **neon brand integration** | Zero `theme.py` imports across ~2,239 LOC. |
| **CI gate** | `brand_lint` is warn/manual; not fail-on-error in CI (Wave 8). |
| **Drifts #3/#4/#5** | Unchanged: glyphs (Nerd Font) vs Lucide icons no 1:1 map; `INK_BLACK` vs `surface.black`; `StatusChip` consent label React-only. |

---

## 9. Open Questions / UNKNOWNs

- **tmux surface** (`.tmux.conf`, `tmux_metamcp_controller.py`): exists as a tmux↔MetaMCP role-switch control plane; never audited for brand/maturity. Score and disposition **UNKNOWN** — needs a dedicated pass.
- **React build status**: INFERRED-broken; not confirmed (`node_modules` absent). Resolve with `npm ci && npx tsc --noEmit`.
- **Missing-components decision**: restore vs remove vs stub — undecided; blocks any web work.
- **`ui-dashboard-backend/app.py`** (per Report C): exists but does not implement `/api/adhd-state` or `/ws/state` (real backend is `services/adhd-dashboard/backend.py`). Production, mock, or dead? Ownership UNKNOWN.
- **`restore/orchestrator-infra-palette-clobber` branch**: HEAD/contents untraced — does it revert or restore Palette? UNKNOWN.
- **629-line count + d8e0268d3 file list** (Report E): not independently re-counted at HEAD; only `config.yaml` deletion confirmed firsthand.
- **Per-surface baseline sub-scores** (S/V/A/D/T): carried from Reports A/C/D; the composite (~61 / ~56) is INFERRED judgment, not measurement.
- **`proof/epic-rte/` (Wave 6)**: not inspected; triage status UNKNOWN.