---
id: brand-rollout-plan-2026-04-21
title: Dopemux Brand Rollout Plan — 2026-04-21
type: how-to
owner: brand-system
date: 2026-04-21
status: proposed
complements: design-system-audit-2026-04-21
---

# Dopemux Brand Rollout Plan — 2026-04-21

## Goals

1. **Every operator-facing surface** — CLI, TUI, React dashboard, Ink TUI, FastAPI HTML, bash scripts, Smarty templates — reads from a single, token-backed brand source.
2. **Onboarding a new surface takes <2 hours** — documented pattern, helper available per stack, lint covers the file type on day one.
3. **`brand_lint.py` passes repo-wide** with extended coverage (Python, TSX, HTML, Smarty, bash).

## Success Criteria

- No `#[0-9A-F]{6}` literals outside the four canonical token files and `splash.py` gradient block.
- No raw Ink `color="..."` props in `services/conport_kg_ui/`.
- Leantime plugin exists in exactly one canonical location (+ a docker copy produced by build, not checked in).
- Every unbranded surface from the audit report has a corresponding wave entry below.
- React token layer supports the same three palettes Python does (`mint-mojo`, `pastel-neon-dreamscape`, `pastel-neon-dreams`).

## Summary Table

| Wave | Focus | Effort | Blocking dependencies |
|---|---|---|---|
| 0 | Enablers (React palette parity, Ink theme, bash helper, lint extension, how-to) | L (2–3 days) | None |
| 1 | Python scripts and auxiliary dashboards | M (4–6h total, across 5 files) | Wave 0 how-to |
| 2 | Shell surfaces | S (2–3h) | Wave 0 bash helper |
| 3 | FastAPI inline HTML | M (3–5h) | Wave 0 brand CSS partial |
| 4 | Leantime plugin dedupe + brand CSS | M–L (1–2 days) | Wave 0 brand CSS partial |
| 5 | Ink TUI (ConPort KG UI) | M (1 day) | Wave 0 Ink theme helper |
| 6 | proof/epic-rte/ triage | S (1h) | None |
| 7 | RTE (repo-truth-extractor) greenfield | M (1 day) | None |
| 8 | Hardening — lint, CI gate, docs, metrics | M (1 day) | All prior waves |

## Wave 0 — Enablers

**Scope:** Build the foundations that let every subsequent wave ship small, safe PRs.

Tasks:

1. **React palette parity.** Refactor [ui-dashboard/src/theme.ts](../ui-dashboard/src/theme.ts) so `brandTokens` becomes `brandPalettes[paletteName]` and the exported `brandTokens` resolves against `DOPEMUX_THEME` (env var or app setting). Emit CSS custom properties for each palette in [ui-dashboard/src/index.css](../ui-dashboard/src/index.css) under `[data-palette="..."]` selectors. Add `--saint-gold` (currently missing). Update [scripts/sync_brand_tokens.py](../scripts/sync_brand_tokens.py) to sync all three palettes.
2. **Ink theme helper.** Create `services/conport_kg_ui/src/theme.ts` that re-exports the same anchor hexes and a typed `InkColor` helper (`ink('ritualCyan')`). Matches the mint-mojo palette by default; downstream surfaces never import hex.
3. **Bash brand helper.** Add `scripts/lib/brand.sh` with named ANSI color variables matching the mint-mojo palette (`BRAND_CYAN`, `BRAND_MINT`, `BRAND_GOLD`, `BRAND_PINK`, `BRAND_VIOLET`, `BRAND_RESET`), a `brand::chip LIVE "message"` function, and a `brand::section "title"` helper. Respect `NO_COLOR`.
4. **Shared brand CSS partial.** Add `docs/templates/brand.css` that declares the same custom properties as `ui-dashboard/src/index.css` but stand-alone (no dashboard coupling). Used by monitoring-dashboard, Leantime, and any future HTML surface. Include a minimal typography scale and chip utility classes.
5. **Lint extension groundwork.** Add Python helpers to `scripts/brand_lint.py`:
   - `_iter_palette_violations` widened to recurse over a configurable directory set instead of a fixed allow-list.
   - New `_iter_ink_color_violations` that flags `color="<named>"` in `*.tsx` under `services/*_ui/`.
   - New `_iter_html_template_violations` that flags inline `<style>` blocks with hex literals in `*.py` and `*.html` templates.
   - Do not flip CI gating on yet — only emit warnings until every wave has landed.
6. **How-to.** Write `docs/02-how-to/brand-a-new-surface.md` with one section per stack (Python Rich, Python Textual, React/MUI, Ink, FastAPI+HTML, bash, Smarty). Each section: imports, minimal example, lint expectation.

Acceptance criteria:

- `DOPEMUX_THEME=pastel-neon-dreamscape npm run build -- ui-dashboard` produces a dashboard with the dreamscape palette.
- `source scripts/lib/brand.sh && brand::chip LIVE "hello"` prints the expected ANSI sequence.
- `scripts/brand_lint.py --warn-only` runs end-to-end with new checks emitting warnings.
- `docs/02-how-to/brand-a-new-surface.md` exists and links from [BRAND_SYSTEM.md](../BRAND_SYSTEM.md).

Risks:

- Parameterising `brandTokens` without breaking existing imports. Mitigation: the old `brandTokens` export stays; the new API is additive. Verify with `tsc --noEmit` and a visual regression check of the dashboard.
- `sync_brand_tokens.py` contract expansion could drift. Mitigation: keep it idempotent, gate on `git diff --quiet` in CI.

Rollback: each enabler lives behind its own PR; revert in reverse order.

## Wave 1 — Python scripts & auxiliary dashboards

**Scope:** Five Python files that print to the terminal with foreign or missing palettes.

Targets & tasks:

- [scripts/dopemux_dashboard.py](../scripts/dopemux_dashboard.py) — delete the `THEMES` dict (Catppuccin/Nord). Import `from dopemux.ui.theme import DOPEMUX_THEME, styled_panel, styled_gauge, StatusChip`. Replace raw `console.print(..., style="#xxxxxx")` with theme style names. (~27 hex literals to remove.)
- `scripts/ui/realtime_status_updater.py` — same treatment; use `StatusChip.LIVE.render(...)` for status lines.
- `scripts/ui/metamcp_status.py` — same treatment.
- [services/serena/metrics_dashboard.py](../services/serena/metrics_dashboard.py) — keep the dict-based data path, but add an optional `render()` that wraps the dict in `styled_table("Serena Metrics", ...)`. CLI consumers get branding; programmatic consumers get the same dict.
- [services/serena/multi_session_dashboard.py](../services/serena/multi_session_dashboard.py) — replace `─` line-drawing and emoji literals with `styled_panel` + `Glyphs`.
- [services/task-orchestrator/observability/adhd_dashboard.py](../services/task-orchestrator/observability/adhd_dashboard.py) — generates Grafana JSON. Replace literal panel colors with constants sourced from `brandTokens` (export a machine-readable JSON of the palette from sync_brand_tokens.py if needed).

Effort: M — 45–90 min per file, 5–6 files, one PR per file.

Acceptance criteria:

- `brand_lint.py` (with Wave 0 checks enabled) reports zero palette violations for each file.
- `python scripts/dopemux_dashboard.py` renders with the mint-mojo palette (or whichever `DOPEMUX_THEME` says).
- Unit tests (where present) still pass.

Risks: visual regression — Catppuccin was popular. Ship a migration note ("this uses the dopemux palette now; use `DOPEMUX_THEME` to switch").

Rollback: revert each PR independently.

## Wave 2 — Shell surfaces

**Scope:** `scripts/mobile/status-dashboard.sh` and any sibling bash dashboards.

Tasks:
- Source `scripts/lib/brand.sh` (from Wave 0) at the top of the file.
- Replace plain `echo` section headers with `brand::section "Status"`.
- Add `brand::chip OK`, `brand::chip BLOCKER`, `brand::chip LIVE` for status rows.
- Respect `NO_COLOR` automatically via the helper.
- Repeat for any other bash scripts in `scripts/` that emit human-readable status output (audit with `grep -l 'echo ===' scripts/`).

Effort: S — 2–3h.

Acceptance:
- `NO_COLOR=1 ./scripts/mobile/status-dashboard.sh` produces plain text.
- Default run shows branded chips matching the CLI's StatusChip output.

Risks: locale / terminfo differences. Mitigation: the helper falls back to `printf` with hardcoded ANSI when `tput` is missing.

Rollback: revert the one file.

## Wave 3 — FastAPI inline HTML

**Scope:** [services/monitoring-dashboard/server.py](../services/monitoring-dashboard/server.py) and any sibling service shipping inline HTML.

Tasks:
- Move the inline HTML out of `server.py` into `services/monitoring-dashboard/templates/dashboard.html` (Jinja or f-string, whichever is already in use).
- `<link rel="stylesheet" href="/static/brand.css">` — served from `docs/templates/brand.css` (Wave 0) copied or mounted into the service's `static/` directory at build time.
- Replace literal `#667eea`, `#764ba2`, `#e1f5fe`, `#0277bd`, `#f9f9f9` with `var(--ritual-cyan)`, `var(--serum-mint)`, etc. Map the old gradient to `linear-gradient(135deg, var(--ritual-cyan), var(--aftercare-violet))` for closest intent match.
- Wrap error strings in `brand_error()` from [services/shared/brand_voice.py](../services/shared/brand_voice.py) to align with BRAND_SYSTEM error style.

Effort: M — 3–5h.

Acceptance:
- Page source contains no raw hex (all via CSS custom properties).
- Dashboard passes visual spot-check against the main React dashboard's color language.
- Extended `brand_lint.py` HTML check reports clean.

Risks: visual identity shift for monitoring operators. Mitigation: ship a side-by-side screenshot in the PR description.

Rollback: single revert.

## Wave 4 — Leantime plugin

**Scope:** [plugins/Dopemux/Views/dashboard.tpl](../plugins/Dopemux/Views/dashboard.tpl) + `docker/leantime/app/Plugins/Dopemux/Views/dashboard.tpl` + `docker/leantime/docker/leantime/plugins/Dopemux/Views/dashboard.tpl` + three copies of `dopemux-adhd.css`.

Phase 4a — dedupe:
- Establish `plugins/Dopemux/` as canonical.
- Replace the docker copies with build-time COPY directives in the Dockerfile. Delete the checked-in duplicates.
- Verify with `diff -r plugins/Dopemux/ docker/leantime/app/Plugins/Dopemux/` before and after.

Phase 4b — rebrand:
- Rewrite `plugins/Dopemux/Assets/css/dopemux-adhd.css` to import `brand.css` (from Wave 0) and redefine all 52 hex literals in terms of `var(--*)`. Classes `attention-{state}` and `load-{level}` stay; their color rules reference tokens.
- Update `dashboard.tpl` to include `brand.css` before `dopemux-adhd.css`.
- Map Bootstrap semantic classes to brand tokens via CSS overrides (`.btn-primary { background: var(--ritual-cyan); color: var(--ink-black); }`).

Effort: M–L — 1–2 days (the dedupe is the risky part).

Acceptance:
- Exactly one source-of-truth copy of the plugin in the repo.
- `docker build` produces a working Leantime image with brand-aligned colors.
- Smoke test: render the dashboard in a dev Leantime instance, verify chip colors match the main React dashboard.

Risks: Dockerfile changes break the Leantime image. Mitigation: stage in a feature branch, run the existing Leantime smoke tests before merge.

Rollback: revert dedupe commit first, then rebrand commit.

## Wave 5 — Ink TUI (ConPort KG UI)

**Scope:** `services/conport_kg_ui/src/` — `DecisionBrowser.tsx`, `DeepContextViewer.tsx`, `GenealogyExplorer.tsx`, and siblings.

Tasks:
- Consume the Wave 0 Ink theme helper (`services/conport_kg_ui/src/theme.ts`).
- Replace every `<Text color="cyan">` / `"green"` / `"magenta"` with `<Text color={ink('ritualCyan')}>` etc.
- Add a reusable `<Chip variant="live" />` component that mirrors the Python `StatusChip` labels (`[LIVE]`, `[BLOCKER]`, etc.) using Ink primitives.
- Factor status-tone logic out into `useBrandStatus()` so future Ink surfaces share it.

Effort: M — 1 day.

Acceptance:
- Zero raw Ink color-string literals in the service (lint rule from Wave 0 gates this).
- Visual parity with the dashboard's chip styling (manual spot-check).

Risks: Ink's color support is terminal-capability-dependent. Mitigation: the helper falls back to named Ink colors when `NO_COLOR` is set.

Rollback: single revert of the wave PR.

## Wave 6 — proof/epic-rte/ triage

**Scope:** [proof/epic-rte/](../proof/epic-rte/).

Tasks:
- Confirm with the extraction owner that the directory is an archive of proof runs, not a planned TUI surface.
- Add `proof/epic-rte/README.md` documenting its status: "proof-run artifact archive — no operator UI. Do not brand."
- If the owner disagrees, defer to a later scoping session.

Effort: S — 1h.

Acceptance: README in place, rollout doc updated to link it.

Risks: trivial.

## Wave 7 — RTE (repo-truth-extractor) greenfield

**Scope:** [services/repo-truth-extractor/](../services/repo-truth-extractor/).

**Design proposal (greenfield, branded from day one):**

Stack: Python Rich (consistent with the rest of the CLI).

Surface: a live progress panel shown while `run_extraction_v5.py`, `run_prescan.py`, and `run_probe.py` execute. Suppressed in non-TTY contexts; falls back to `brand_log` lines.

Primitives used (all from `src/dopemux/ui/theme.py`):
- `styled_panel("Repo Truth Extraction", …)` — outer frame, shows run ID, workspace, phase.
- `styled_gauge(phase_progress, width=40)` — visible progress for each phase.
- `StatusChip.LIVE` while a phase is running; `StatusChip.LOGGED` when committed; `StatusChip.BLOCKER` on error.
- `Glyphs.SUCCESS` / `Glyphs.ERROR` / `Glyphs.RUNNING` for per-step lines.
- `brand_log(...)` for terminal logs via `services/shared/brand_voice.py`.
- `brand_error(...)` (wrapping the extractor's structured error) for failure modes.

Layout sketch:
```
━━━◆ Ø ◆━━━ Repo Truth Extraction
┌─ run 2026-04-21T14:32Z ──────────────────────┐
│ workspace: /Users/…/dopemux-mvp              │
│ phase:     prescan                           │
│ [LIVE] scanning 1,247 files                  │
│ [████████████████░░░░] 80%                   │
│                                              │
│ [LOGGED] extractor:ingest         12.4s      │
│ [LOGGED] extractor:normalize       3.1s      │
│ [LIVE]   extractor:prescan         running   │
│                                              │
│  press Ctrl-C for graceful stop              │
└──────────────────────────────────────────────┘
```

Tasks:
- Add `services/repo-truth-extractor/ui_output.py` exposing `progress_context()` as a `contextmanager` that wraps the extractor's existing logging hooks.
- Wire the runners (`run_extraction_v*.py`, `run_prescan.py`, `run_probe.py`) to emit events that the progress context consumes.
- Non-TTY detection: if `not sys.stdout.isatty()`, fall back to `brand_log` line-per-event output.

Effort: M — 1 day.

Acceptance:
- Running `run_extraction_v5.py` in a TTY shows the branded panel end-to-end.
- Running via CI (no TTY) produces ordered `[LIVE] …` / `[LOGGED] …` lines.
- Failure injection produces `[BLOCKER] …` with a branded error.

Risks: extractor ownership overlap with the cognitive plane. Mitigation: the UI layer is strictly additive — the existing extractor output contract does not change.

Rollback: trivial; delete `ui_output.py` and revert the runner wiring.

## Wave 8 — Hardening

**Scope:** Tests, CI gating, documentation, metrics.

Tasks:
1. Flip `scripts/brand_lint.py` from warn-only to fail-on-error for the new checks introduced in Wave 0. Add a CI step `make brand-lint` (or equivalent) that runs it and fails the build on violations.
2. Add a focused visual-regression smoke test for the main React dashboard (Playwright): loads the dashboard, screenshots the hero, diffs against a committed baseline.
3. Extend [BRAND_SYSTEM.md](../BRAND_SYSTEM.md) with a "Surfaces" section listing every operator surface and the primitive it uses. Cross-link `docs/02-how-to/brand-a-new-surface.md`.
4. Add a "new surface" PR template under `.github/PULL_REQUEST_TEMPLATE/new-surface.md` that enforces the checklist (imports tokens? uses StatusChip? lint passes? screenshots attached?).
5. Metrics — emit a weekly `brand-coverage.json` in CI with:
   - % of files matching `scripts/brand_lint.py` allow-lists
   - count of hardcoded hex literals outside canonical files
   - count of raw Ink color strings in TSX
   - lint pass/fail trend
   Publish to `claudedocs/metrics/` or wherever the team tracks health.

Effort: M — 1 day.

Acceptance:
- CI fails on a deliberately introduced hex literal.
- Visual regression test runs in <60s on the main React dashboard.
- `BRAND_SYSTEM.md` lists every surface and its primitive.

Risks: false-positive noise from the lint flip. Mitigation: run in warn-only for one week before flipping.

Rollback: set lint back to warn-only; visual regression can stay — it's additive.

## Dependencies Graph

```
Wave 0 (enablers)
  ├── React palette parity ─────────────► (enables future palette work)
  ├── Ink theme helper ─────────────────► Wave 5
  ├── Bash helper ──────────────────────► Wave 2
  ├── Brand CSS partial ────────────────► Wave 3, Wave 4
  ├── Lint extension (warn-only) ───────► Wave 8 (flip)
  └── How-to doc ───────────────────────► all waves reference it

Wave 1 ─ independent once Wave 0 lint/howto ship
Wave 2 ─ depends on Wave 0 bash helper
Wave 3 ─ depends on Wave 0 brand CSS partial
Wave 4 ─ depends on Wave 0 brand CSS partial; dedupe before rebrand
Wave 5 ─ depends on Wave 0 Ink theme helper
Wave 6 ─ independent
Wave 7 ─ independent (pure-Python Rich stack already branded)
Wave 8 ─ requires all prior waves to ship cleanly before CI flip
```

## Rollback Story

Every wave is scoped to a small, independently revertible PR set. Specific guidance:

- **Wave 0**: enabler PRs are additive (new files, additive exports). Safe to leave in place even if dependent waves are postponed.
- **Wave 1 / 2 / 5**: each target file is its own PR; revert that single PR.
- **Wave 3**: revert template extraction + CSS include as one unit.
- **Wave 4**: dedupe commit MUST land before rebrand; to roll back, reverse order (revert rebrand, then un-dedupe). Keep the Dockerfile change paired with the dedupe.
- **Wave 7**: pure additive UI layer — revert deletes `ui_output.py` and the runner wiring.
- **Wave 8**: CI lint flip is a one-line toggle in `make brand-lint`; can be reverted without touching code.

## Metrics

Track weekly:

| Metric | Source | Target |
|---|---|---|
| `hardcoded_hex_count` | `grep -R '#[0-9A-Fa-f]\{6\}' --exclude=<canonical>` | 0 (excluding canonical files + splash gradient) |
| `ink_raw_color_count` | `grep -R 'color="\(cyan\|green\|magenta\|yellow\|red\|white\|blue\)"' services/*_ui/` | 0 |
| `brand_lint_status` | CI exit code | pass |
| `surfaces_covered_pct` | (branded surfaces / total surfaces) from audit doc | 100% by end of Wave 7 |
| `onboarding_time` | qualitative — time to brand a new surface from scratch following `brand-a-new-surface.md` | <2h |

Baseline (today, 2026-04-21):
- `hardcoded_hex_count`: ~220 across 9 files (52 × 3 in Leantime CSS = 156; 27 + 24 + 18 + 13 + others in scripts/ and services/ = ~64).
- `ink_raw_color_count`: ~35 across `services/conport_kg_ui/src/*.tsx`.
- `brand_lint_status`: pass (scope: core CLI allow-list only).
- `surfaces_covered_pct`: 5/16 fully branded (31%), 1/16 partial (6%), 9/16 unbranded (56%), 1/16 greenfield (6%). Weighted by criticality: 62%.

## Out of Scope

- **Voice model/tone drift across services.** `brand_voice.py` already provides the primitives; enforcing their use in non-audit-listed services would be a separate initiative.
- **Rebranding marketing/website assets** outside `ui-dashboard/` and the operator surfaces above.
- **New palettes.** Wave 0 enables parameterising; choosing new palettes is a design decision owned outside this plan.

---

**Complements:** [design-system-audit-2026-04-21.md](design-system-audit-2026-04-21.md).
