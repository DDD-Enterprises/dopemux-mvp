---
id: design-system-audit-2026-04-21
title: Dopemux Design System Audit — 2026-04-21
type: reference
owner: brand-system
date: 2026-04-21
audit_scope: repo-wide (16 surfaces)
status: current
---

# Dopemux Design System Audit — 2026-04-21

## Summary

**Surfaces reviewed:** 16
**Issues found:** 9 unbranded surfaces · 3 duplicated plugin assets · 1 service with no operator surface
**Score:** 62/100 (weighted by surface criticality)
**Verdict:** Core operator surfaces are tightly branded against a single source of truth. Peripheral dashboards (bash, FastAPI inline HTML, Ink TUI, Smarty templates) and auxiliary scripts still ship their own palettes or none at all. `brand_lint.py` passes on its current allow-list, but the lint does not cover the full surface area.

Audited against HEAD `491c981de` (main, fast-forwarded from worktree `claude/bold-mestorf-efe028`).

## Canonical Brand Sources

| Layer | File | Role |
|---|---|---|
| Operator voice & tone | [BRAND_SYSTEM.md](../BRAND_SYSTEM.md) | Authoritative voice, naming, error style, dashboard visual language |
| Python CLI/TUI tokens | [src/dopemux/ui/theme.py](../src/dopemux/ui/theme.py) | `DOPEMUX_THEME`, `StatusChip`, `Glyphs`, `styled_table/panel/gauge`, `RenderMode`, three palettes (mint-mojo default, pastel-neon-dreamscape, pastel-neon-dreams) |
| React/MUI tokens | [ui-dashboard/src/theme.ts](../ui-dashboard/src/theme.ts) | `brandTokens`, `statusStyles`, MUI theme |
| CSS custom properties | [ui-dashboard/src/index.css](../ui-dashboard/src/index.css) | `--ritual-cyan`, `--serum-mint`, `--gremlin-pink`, etc. |
| Textual stylesheet | [src/dopemux/ui/dopemux.tcss](../src/dopemux/ui/dopemux.tcss) | Shared Textual CSS, references same palette |
| Cross-service helpers | [services/shared/brand_voice.py](../services/shared/brand_voice.py) | `brand_log`, `brand_error`, `brand_payload`, `StatusChip`, `break_copy`, `hyperfocus_copy` |
| Lint | [scripts/brand_lint.py](../scripts/brand_lint.py) | AST-based checks for logger wrapping, HTTPException detail wrapping, palette hex, theme default, prohibited voice modes |
| Sync | [scripts/sync_brand_tokens.py](../scripts/sync_brand_tokens.py) | Keeps Python ↔ React token layers aligned |
| Notification helper | [ui-dashboard/src/notificationColors.ts](../ui-dashboard/src/notificationColors.ts) | New (#482 series), consumes `brandTokens` exclusively |

## Naming Consistency

| Area | Status | Notes |
|---|---|---|
| StatusChip names | ✅ Consistent | `LIVE`, `BLOCKER`, `OVERRIDE`, `LOGGED`, `AFTERCARE`, `EDGE` present in both [theme.py](../src/dopemux/ui/theme.py:330) and [theme.ts](../ui-dashboard/src/theme.ts:38) (React exposes `chips.live` etc., Python exposes the enum). Labels match verbatim including `[CONSENT CHECK? y/N]` present only on React side. |
| Color token names | ⚠️ Partial drift | Python uses UPPER_SNAKE module-level (`RITUAL_CYAN`, `GREMLIN_PINK`) and theme keys are semantic (`mint`, `magenta`, `gilt.edge`). React uses camelCase semantic keys (`ritualCyan`, `gremlinPink`, `giltEdge`). The CSS layer uses kebab-case (`--ritual-cyan`). All three reference the same hex anchor set; names only diverge by case convention. |
| Palette naming | ✅ | Three palettes defined in Python (`mint-mojo`, `pastel-neon-dreamscape`, `pastel-neon-dreams`). React/CSS currently encode only the `mint-mojo` anchor hexes; there is no React-side palette switcher. See Drift #1 below. |
| Voice header terms | ✅ | [brand_voice.py:17](../services/shared/brand_voice.py) maps each StatusChip to a tone string used across services for structured logging. |

## Token Coverage (Cross-Layer Reconciliation)

All three token layers agree on the `mint-mojo` palette, which is the production default.

| Token | theme.py (mint-mojo) | theme.ts | index.css | Status |
|---|---|---|---|---|
| Ritual Cyan | `#7DFBF6` (`RITUAL_CYAN`, [theme.py:69](../src/dopemux/ui/theme.py)) | `#7DFBF6` (`brandTokens.colors.ritualCyan`) | `--ritual-cyan-rgb: 125 251 246` | ✅ |
| Serum Mint | `#94FADB` (`SERUM_MINT`) | `#94FADB` (`serumMint`) | `148 250 219` | ✅ |
| Gilt Edge | `#F5F26D` (`GILT_EDGE`) | `#F5F26D` (`giltEdge`) | `245 242 109` | ✅ |
| Gremlin Pink | `#FF8BD1` (`GREMLIN_PINK`) | `#FF8BD1` (`gremlinPink`) | `255 139 209` | ✅ |
| Aftercare Violet | `#9B78FF` (`AFTERCARE_VIOLET`) | `#9B78FF` (`aftercareViolet`) | `155 120 255` | ✅ |
| Ink Black | `#020617` (`INK_BLACK`) | `#020617` (`inkBlack`) | `2 6 23` | ✅ |
| Void Navy | `#041628` (`VOID_NAVY`) | `#041628` (`voidNavy`) | `4 22 40` | ✅ |
| Velvet Plum | `#1A0520` (`VELVET_PLUM` — global constant) | `#1A0520` (`velvetPlum`) | `26 5 32` | ✅ |
| Saint Gold | `#FFCF78` (`SAINT_GOLD` — global constant) | `#FFCF78` (`saintGold`) | (not present) | ⚠️ Missing from CSS custom properties |

### Drift findings

1. **Palette parity:** `theme.py` knows three palettes; `theme.ts` and `index.css` only encode one. Switching to `pastel-neon-dreamscape` via `DOPEMUX_THEME` env var changes the CLI but leaves the React dashboard on mint-mojo. The React layer has no `brandTokens[paletteName]` structure today. Recommend parameterising React tokens the same way `build_theme(name)` does.
2. **Saint Gold:** Present in Python (global), present in React (`saintGold`), but not emitted as a `--saint-gold` CSS variable. Any plain CSS consumer that wants the gold has to import it via MUI/JS, which excludes Leantime or monitoring-dashboard HTML.
3. **Glyphs vs icons:** Python ships Nerd Font glyphs ([theme.py:262](../src/dopemux/ui/theme.py)) with an ASCII fallback map. React uses Lucide icons (verified via `App.tsx`); there is no published mapping from "SUCCESS = nf-fa-check_circle" to "CheckCircle (Lucide)". A surface that wants visual parity must choose ad-hoc.
4. **`INK_BLACK` vs `surface.black`:** theme.py exposes both a module global (`INK_BLACK = "#020617"`) and a theme style (`surface.black = "#020617"`). They agree today; the module globals act as a compatibility API for `src/dopemux/tmux/theme.py`.
5. **`StatusChip` consent label:** `brandTokens.chips.consent = "[CONSENT CHECK? y/N]"` has no equivalent Python chip. The operator-surface meaning is different (React treats it as a prompt; Python has no analogue). Either add `StatusChip.CONSENT` to Python or mark the React chip as a dashboard-only affordance.

## Surface-by-Surface Scorecards

Legend: **S**tates · **V**ariants · **A**ccessibility · **D**ocs · **T**oken coverage (each /2, total /10).

### ✅ Branded (canonical)

| # | Surface | Path | S | V | A | D | T | Score |
|---|---|---|---|---|---|---|---|---|
| 1 | Core CLI/TUI | [src/dopemux/ui/](../src/dopemux/ui/) | 2 | 2 | 1 | 2 | 2 | **9/10** |
| 2 | PR Merge Specialist (Flight Deck) | [src/dopemux_pr_merge_specialist/](../src/dopemux_pr_merge_specialist/) | 2 | 2 | 1 | 2 | 2 | **9/10** |
| 3 | Main React Dashboard | [ui-dashboard/](../ui-dashboard/) | 2 | 2 | 2 | 1 | 2 | **9/10** |
| 4 | Shared React primitives (theme-agnostic) | [components/](../components/) | 2 | 2 | 2 | 1 | N/A | **7/8 — by design** |
| 5 | notificationColors helper | [ui-dashboard/src/notificationColors.ts](../ui-dashboard/src/notificationColors.ts) | N/A | N/A | N/A | 1 | 2 | **3/3** |

Evidence:
- `src/dopemux/ui/dashboard.py:24` imports `Glyphs, StatusChip, styled_gauge, styled_panel, styled_table`. Every file in the directory consumes `DOPEMUX_THEME` directly or via helpers.
- `src/dopemux_pr_merge_specialist/dashboard.py:25` imports `DOPEMUX_THEME`; `ux_engine.py` owns the `RenderMode` dispatch; `interactive.py` assembles the 8-component cockpit documented in [task-packets/TP-PRMS-053-GRAND-ORCHESTRATOR-DASHBOARD.md](../task-packets/TP-PRMS-053-GRAND-ORCHESTRATOR-DASHBOARD.md).
- `ui-dashboard/src/App.tsx:30,262` wraps the entire tree with the MUI `theme` that reads `brandTokens`. Recent PRs (#491, #486, #482, #466) hardened focus rings, chip ARIA, and `TaskSequencer` accessibility.
- `components/*.tsx` deliberately consumes Tailwind primitives (`bg-primary`, `bg-secondary`) and stays theme-neutral — branding is applied by the consumer (the dashboard's ThemeProvider). This is the correct pattern and is scored as such.
- `ui-dashboard/src/notificationColors.ts:1-30` imports only `brandTokens`; zero raw hex.

Gaps (knock-off 1 point each):
- Core CLI/TUI: Textual stylesheet [dopemux.tcss](../src/dopemux/ui/dopemux.tcss) hardcodes the mint-mojo palette rather than reading it from `theme.py` (by nature — Textual CSS is static). Palette switching does not propagate to Textual screens.
- PR Merge Specialist: same Textual-CSS caveat; a11y contrast for `[BLOCKER]` pink on navy has not been formally measured.
- Main Dashboard: No cross-browser axe/WAVE run committed; accessibility confidence is high but unverified for this revision.
- `components/`: no README documenting the "primitives stay theme-agnostic" pattern.

### ⚠️ Partial

| # | Surface | Path | State | Notes |
|---|---|---|---|---|
| 6 | ADHD Dashboard (backend) | [services/adhd-dashboard/backend.py](../services/adhd-dashboard/backend.py) | Backend-only branded | `backend.py:39` imports `StatusChip, brand_log, brand_error, brand_payload, voice_header`. Every `HTTPException(..., detail=brand_error(...))` enforces branded API failure copy. No frontend. Score **5/10**. |
| 7 | Monitoring Dashboard | [services/monitoring-dashboard/server.py](../services/monitoring-dashboard/server.py) | Inline HTML, foreign palette | Hardcoded gradient hexes `#667eea`, `#764ba2`, badge hexes `#e1f5fe`, `#0277bd`, background `#f9f9f9`. No reference to brand tokens. Not Bootstrap-only — a bespoke inline stylesheet. Score **2/10**. |

### ❌ Unbranded

| # | Surface | Path | State | Notes |
|---|---|---|---|---|
| 8 | ConPort KG UI | [services/conport_kg_ui/](../services/conport_kg_ui/) | Ink TUI, raw color names | `DecisionBrowser.tsx`, `DeepContextViewer.tsx`, `GenealogyExplorer.tsx` use `<Text color="cyan">`, `color="green"`, `color="magenta"`, `color="yellow"`, etc. No brandTokens import. Score **2/10**. |
| 9 | Serena metrics dashboard | [services/serena/metrics_dashboard.py](../services/serena/metrics_dashboard.py) | Returns dicts, no rendering | Pure data aggregator. Score N/A for visual branding — but no `Rich` wrapper if it is printed anywhere. Score **3/10**. |
| 10 | Serena multi-session dashboard | [services/serena/multi_session_dashboard.py](../services/serena/multi_session_dashboard.py) | Plain text formatter | Uses `─` box-drawing and emoji literals. No `DOPEMUX_THEME`. Score **2/10**. |
| 11 | Task-orchestrator ADHD dashboard | [services/task-orchestrator/observability/adhd_dashboard.py](../services/task-orchestrator/observability/adhd_dashboard.py) | Generates Grafana JSON | Panel titles, colors, thresholds all literal strings/hex. Brand tokens not imported. Score **2/10**. |
| 12 | `dopemux_dashboard.py` | [scripts/dopemux_dashboard.py](../scripts/dopemux_dashboard.py) | Textual TUI, foreign palette | Hardcoded Catppuccin/Nord palettes (lines 79–120), 27 raw hex literals. Never imports `DOPEMUX_THEME`. Score **2/10**. |
| 13 | Mobile status dashboard | [scripts/mobile/status-dashboard.sh](../scripts/mobile/status-dashboard.sh) | Bash, plain echo | No ANSI escapes, no `tput`, no brand helpers. Score **1/10**. |
| 14 | Leantime plugin dashboard | [plugins/Dopemux/Views/dashboard.tpl](../plugins/Dopemux/Views/dashboard.tpl) + `docker/leantime/app/Plugins/Dopemux/Views/dashboard.tpl` | Bootstrap, duplicated | Byte-identical copies. Uses `attention-{state}` / `load-{level}` classes defined in [plugins/Dopemux/Assets/css/dopemux-adhd.css](../plugins/Dopemux/Assets/css/dopemux-adhd.css) (52 hex literals, disconnected from brand tokens). Score **2/10**. |

### ❓ Unknown → resolved

| # | Surface | Path | Resolution |
|---|---|---|---|
| 15 | `proof/epic-rte/` | [proof/epic-rte/](../proof/epic-rte/) | **Not a UI.** Contains one archived proof run (`TP-CODEX-RTE-PRELIVE-005A-PROOF-POLICY-COHERENCE`) — JSON manifests, checksums, markdown reports. No .py/.ts sources. Exclude from rollout plan, or confirm with owner before investing. |
| 16 | `services/repo-truth-extractor/` | [services/repo-truth-extractor/](../services/repo-truth-extractor/) | **No operator surface yet.** Entry points are CLI runners (`run_extraction_v5.py`, `run_prescan.py`, `run_probe.py`). Output is structured data/logs without Rich. Opportunity to design a branded progress surface greenfield. Captured in the rollout plan as Wave 7. |

## Hardcoded-Value Sweep

**Methodology:** Grep for `#[0-9A-Fa-f]{6}` across `*.py`, `*.ts`, `*.tsx`, `*.css`, `*.tcss`, excluding the four canonical token files.

| File | Hex count | Category | Action |
|---|---|---|---|
| `plugins/Dopemux/Assets/css/dopemux-adhd.css` | 52 | Leantime CSS (primary copy) | Fold into token-driven CSS in Wave 4 |
| `docker/leantime/docker/leantime/plugins/Dopemux/Assets/css/dopemux-adhd.css` | 52 | Docker-baked duplicate | Dedupe in Wave 4 |
| `docker/leantime/app/Plugins/Dopemux/Assets/css/dopemux-adhd.css` | 52 | Docker-baked duplicate | Dedupe in Wave 4 |
| [scripts/dopemux_dashboard.py](../scripts/dopemux_dashboard.py) | 27 | Foreign palette (Catppuccin/Nord) | Refactor onto `DOPEMUX_THEME` in Wave 1 |
| `scripts/ui/realtime_status_updater.py` | 24 | Ad-hoc status palette | Wave 1 |
| `scripts/ui/metamcp_status.py` | 18 | Ad-hoc status palette | Wave 1 |
| [src/dopemux/ui/splash.py](../src/dopemux/ui/splash.py) | 13 | **Legitimate** — brand-aligned gradient literals that are already the canonical hex values | No action |
| [services/monitoring-dashboard/server.py](../services/monitoring-dashboard/server.py) | 13 | Inline HTML | Wave 3 |
| Remaining files (misc tests/utilities) | 1 each | Isolated | Bundle into Wave 8 lint-extension |

ANSI / Ink color-string sweep:
- 0 raw `\033[` sequences in `scripts/mobile/status-dashboard.sh` (file currently emits no color at all — see Wave 2).
- ~35 `color="…"` string literals across `services/conport_kg_ui/src/*.tsx` pointing at Ink named colors (`"cyan"`, `"green"`, `"magenta"`, etc.). These need a replacement strategy — see Wave 5.

## brand_lint.py Findings

```
$ python scripts/brand_lint.py
0 errors, 0 warnings
```

**Exit code:** 0. All AST checks pass on the current allow-list.

Important caveats about coverage:
- The lint only inspects a fixed allow-list (`AUDITED_PYTHON_FILES`, `STRICT_LOG_FILES`, `HTTP_DETAIL_FILES`, `OPERATIONAL_UI_FILES`).
- It does not walk `scripts/`, `services/conport_kg_ui/`, `services/monitoring-dashboard/`, `plugins/`, or `docker/leantime/` to enforce palette rules.
- Palette hex checking is gated behind `OPERATIONAL_UI_FILES` only, and the set is explicitly scoped to core Dopemux UI files.
- Merge-marker detection runs against `AUTHORITATIVE_BRAND_DOCS` but not against ordinary UI files.

Net: passing brand_lint is necessary but not sufficient evidence of brand compliance across the repo. Wave 8 in the rollout plan extends the lint to cover TSX, HTML templates, Smarty, and bash.

## Documentation Gaps

- [BRAND_SYSTEM.md](../BRAND_SYSTEM.md) defines voice, tone, naming, CLI interaction, error style, and dashboard visual language, but says nothing about token names, palette switching, glyph sets, or the `brand_voice.py` helper contracts.
- No "how to brand a new surface" guide exists. The nearest artefacts are `llm-plans/BRAND_SYSTEM_IMPLEMENTATION.md` and `llm-plans/UX_UI_BRANDING_EXPANSION_PLAN.md`, both historical planning docs — not operator how-tos.
- `components/` has no README explaining the "primitives stay theme-agnostic" rule, which is a load-bearing convention for the whole dashboard.
- Authoritative brand docs referenced by brand_lint (`docs/04-explanation/branding/cli-ux-design-spec.md`, `docs/03-reference/brand-compliance-checklist.md`, `docs/04-explanation/branding/dopemux-brand-system.md`, `docs/04-explanation/ux/ux-style-guide.md`, `docs/ux/ux-style-guide.md`) exist and are merge-marker-free, but their relationship to BRAND_SYSTEM.md is not cross-linked.
- `dopemux_voice_branding_bundle/BRAND_VOICE_BIBLE.md` and [BRAND_SYSTEM.md](../BRAND_SYSTEM.md) are not cross-referenced. Confirm which is authoritative for voice.

## Priority Issues (top 5)

1. **`scripts/dopemux_dashboard.py` ships a foreign palette.** It is a frequently touched operator tool and silently diverges from the brand system with 27 hex literals across Catppuccin/Nord palettes. Highest single-file leverage. → Wave 1.
2. **Leantime plugin dashboard has three byte-identical copies** across `plugins/Dopemux/Views/`, `docker/leantime/app/Plugins/Dopemux/Views/`, and `docker/leantime/docker/leantime/plugins/Dopemux/Views/`. The same holds for the 52-hex `dopemux-adhd.css`. Every future brand change is triplicated. → Wave 4, with dedupe as the first step.
3. **React palette switching not supported.** Python has three palettes; React has one. If the product ever wants to ship a "pastel-neon-dreams" mode end-to-end, the React tokens must be parameterised. → Wave 0 enabler.
4. **ConPort KG UI uses raw Ink color names.** It's an operator surface that looks stylistically adjacent to the canonical CLI but shares zero brand DNA. Low-cost win once an Ink theme helper exists. → Wave 5.
5. **brand_lint.py doesn't cover most of the repo.** The allow-list approach made sense at inception but is now the main reason drift accumulates outside the core CLI. → Wave 8.

## Non-issues (stated honestly)

- The core CLI/TUI, PR Merge Specialist, main React dashboard, shared primitives, and notificationColors helper are in sound shape. No invented problems to pad the list.
- `brand_lint.py` itself is fine for its declared scope. Extending it is a scope increase, not a fix.
- `components/` correctly refuses to encode brand tokens. That is the pattern, not a bug.
- `services/adhd-dashboard/` is intentionally backend-only. Its partial score reflects that it brands the half it owns.

---

**Complements:** [brand-rollout-plan-2026-04-21.md](brand-rollout-plan-2026-04-21.md) — 8-wave plan that maps each priority above to a concrete wave.
