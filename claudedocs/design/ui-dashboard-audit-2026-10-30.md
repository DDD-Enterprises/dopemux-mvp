# Audit — dopemux web cockpit (`ui-dashboard/`), 2026-10-30

**Base:** `main` @ `93050d135` · **Branch:** `feat/ui-dashboard-cockpit-refresh`
**Auditor:** Claude Opus 5.5 (supervisor) + one read-only Sonnet worker (component pass)
**Brief:** "audit dopemux-ui and then use Claude Design to improve it"
**Design authority used:** `BRAND_SYSTEM.md` §6, `claudedocs/design/tokens.json` (Direction B, v0.3.0),
and the DØPEMÜX Design System in Claude Design (built from this repo; its README cites both files).

## Status

The web cockpit builds, type-checks and passes its 54 tests, but it **misreports state**.
With the backend down it shows invented numbers (70% energy, 60% focus, 50% load), a
`[LIVE]` task list of seeded tasks, and a "team" of three fixed members. The
visual layer contradicts the brand's own rules (scanline overlay, global
`transition: all`, personality copy on status surfaces, three disagreeing palettes).
Lint is dead.

## What "dopemux-ui" is

| Package | Path | State |
|---|---|---|
| `dopemux-ui` (Next.js 15) | repo root `package.json` + `components/` | **FACT: shell only.** 6 Radix/shadcn-style files, no `app/` or `pages/`, no `next.config`, no Tailwind config. `next build` has nothing to build. No importer. |
| `ultra-ui-dashboard` (Vite 8 + React 18 + MUI 5) | `ui-dashboard/` | **The live web cockpit** ("Dopemux Ultra UI"). Recent feature PRs: #1399, #1408. |
| `ui-dashboard-backend/` (FastAPI, :3001) | repo root | **FACT: orphaned.** Serves `/api/cognitive-state`, `/api/team-members`, `/api/tasks`, `/api/dashboard`; the frontend calls none of them. |
| `services/adhd-dashboard/backend.py` (:8097) | compose `adhd-dashboard` | **The real backend.** Serves `/api/adhd-state`, `/ws/state`, `/api/task-recommendations`, `/api/sessions/today`. |

CI: `.github/workflows/containers.yml:49` says "Removed - ui-dashboard deprecated" (container
build only). No workflow runs `ui-dashboard` lint or tests. **UNKNOWN:** whether the owner
considers the cockpit deprecated; its recent PR activity says no.

## Deterministic checks (main @ 93050d135)

| Check | Command | Result |
|---|---|---|
| Typecheck | `npx tsc --noEmit -p .` | PASS |
| Lint | `npx eslint src --ext ts,tsx --max-warnings 0` | **FAIL** — ESLint 10 installed, no `eslint.config.js`; exits 2 before linting anything |
| Tests | `npx vitest run` | PASS — 7 files, 54 tests |
| Build | `npx vite build` | PASS — one 437 KB chunk (136 KB gzip); `dist/` is not gitignored |

## Findings

### HIGH

1. **Invented state shown as measured.** `App.tsx:164-170` seeds energy 0.7, attention 0.6,
   load 0.5. On fetch failure the cards keep showing them. `mapAggregateState` /
   `mapRealtimeState` (`App.tsx:98-126`) turn any missing or unrecognised field into 0.5.
   Breaks BRAND_SYSTEM §7: "If a surface cannot prove status, label it `unknown`."
2. **Mock data labelled live.** `TaskSequencer.tsx:59-84` seeds tasks; its `[LIVE]` chip
   (`:555-558`) says "Real-time task synchronization active"; nothing syncs.
   `TeamDashboard.tsx:8-17` renders three fixed members plus "Queue: Stable" and "Handoff: Clear".
   The real backend already exposes `/api/task-recommendations`.
3. **Unprovable consent claim.** The `[CONSENT CHECK? y/N]` chip asks a question, while its
   tooltip and aria-label say "User consent verified". It is static and focusable.
4. **Scanline overlay on top of content.** `index.css` `body::after` draws 2px stripes at
   25% black plus an RGB column tint at `z-index: 2`, above every panel. It cuts the
   contrast of all text. BRAND_SYSTEM §6 and the design system both say: no textures, no noise.
5. **Global `* { transition: all 0.25s ease }`** (`index.css:25-28`) animates every property
   on every element, including layout on resize and 1 Hz timer repaints. Screenshots
   taken right after a viewport change caught the grid mid-animation. It breaks "motion
   means something changed."
6. **Lint gate is dead** (above). With no CI job either, nothing guards this package.

### MEDIUM

7. **Three palettes disagree.** `index.css` CSS vars (`#7DFBF6` cyan, `#94FADB` mint,
   `#FF8BD1` pink, `#9B78FF` violet) vs `theme.ts` (`#2FFFF0`, `#00FF85`, `#FF00CC`,
   `#C07BFF`) vs `tokens.json`. `theme.ts` also uses the retired Direction A surface
   `#1A0520` (Direction B overlay is `#081832`) and saint gold `#FFCF78` (design system
   `#FFC85C`). Its `#F6F7FB` text is **not** drift: the design system declares
   `--text-web: #F6F7FB` for the web cockpit. `.dopemux-roast` renders in a pink that
   matches neither palette.
8. **Degraded is drawn red.** The connection chip uses `errorRed` / `color="error"` for
   `degraded`. Brand: yellow = degraded, red = failed or blocked.
9. **Personality register on status surfaces.** Every metric card carries a roast plus
   "Logged. Hydrate." (4×). The header tagline speaks as "I". The footer is marketing copy.
   The design system limits personality to banners and aftercare, never status lines.
10. **Errors miss the brand's error shape.** The alert shows the raw `Failed to fetch`.
    Brand rule: name the failing surface (endpoint, port) and the next action.
11. **Gremlin pink used as status.** `TaskSequencer.tsx` overtime, Skip, complexity
    (`:337-345`, `:629-675`, `:772`). `Accessibility.test.tsx:302` asserts it.
12. **Prediction panel never resolves.** With no prediction it shows "Loading..." and an
    indeterminate bar forever. Its roast copy "Data ghosting. Refreshing..." claims a refresh
    that does not exist.
13. **Tab-stop inflation.** Non-interactive `tabIndex=0` elements with `aria-label` on
    role-less boxes. About 20 tab stops for 3 tasks in TaskSequencer; the gauge card is
    `role="button"` wrapping a progressbar (`CognitiveLoadGauge.tsx:63`), so the progressbar
    semantics are lost.
14. **Chip-as-button double activation (INFERRED, to verify).** Clickable MUI Chips get a
    hand-written `onKeyDown` that calls the handler. MUI `ButtonBase` already fires `onClick`
    on Enter after `onKeyDown`, so Enter may fire twice.
15. **Notification colours collapse.** `notificationColors.ts:15-20` maps five types to mint.

### LOW

16. Google Fonts `@import` is render-blocking and external for a local-first tool. Only 400-600
    weights load, while 700 is used, so the browser fakes bold.
17. The reduced-motion rule also freezes MUI indeterminate progress, leaving no loading cue.
18. `extensionRegistry.ts:37` globs `./extensions/*.tsx`, which does not exist.
19. `ui-dashboard/dist` is not gitignored.
20. 11 tests read source files with `fs.readFileSync` and assert substrings. They pin
    implementation text (including finding 11), not behaviour.

## Design direction (Claude Design)

The DØPEMÜX Design System is the brief. Its own rules: dark only; colour = state;
calm by default, only danger shouts; operator register by default; mono carries the
voice; motion only on change; `unknown` when unproven. The redesign spends its one bold
move on the **load instrument**. Everything else goes quiet: flat ink plus one halo,
velvet panels that glow only when they are the active focus, a log-style signal feed,
and an explicit `unknown` treatment for every readout.

Font note (resolved by the owner, 2026-10-30): the product uses dopemux's own Iosevka builds,
**Dopemux Term** (mono and display) and **Dopemux Editor** (body), as defined in
`docs/03-reference/Dopemux Cockpit TUI Design System/fonts` (DMX-COCKPIT-FONTS-101..103).
Stacks name `Dopemux Term Nerd Font` first, then `DopemuxTerm Nerd Font Mono` (what older local
builds expose), then the plain build. Space Grotesk, Inter and JetBrains Mono are no longer used.

## Backend contract note (FACT)

`services/adhd_engine/core/engine.py:2031-2047` publishes `state_update` with
`energy_level`, `attention_state`, `cognitive_load` and `recommendation`, but never
`predicted_load_15min`. Only `GET /api/adhd-state` carries a forecast. The cockpit treats
each `state_update` as a full snapshot, so the forecast reads `unknown` after the first
live update. That reflects the backend, not a display bug. **TODO:** add the forecast to the
engine's `state_update` payload if a live forecast is wanted.

## Scope of this change vs follow-up

**Landed in this branch:**

- Lint gate (6): restored with a flat config. Lint still FAILs on pre-existing code:
  16 errors and 2 warnings, from a baseline of 23 and 3.
- Unknown state (1, 12): readings are nullable end to end; the instrument, attention panel
  and task sequencer say unknown.
- Labelling (2, partial): the seeded task queue and team board are labelled `[SAMPLE]`;
  they are not wired to endpoints.
- Remaining findings: 3, 4, 5, 7, 8, 9 (header, cards, task-queue roast line), 10, 19.
- New components: `LoadInstrument` (replaces `CognitiveLoadGauge` and `PredictionPanel`),
  `AttentionStatePanel`, `SignalFeed`.

**Follow-up (not in this branch):**

- Wire TaskSequencer to `/api/task-recommendations` and TeamDashboard to a real source (2).
- TaskSequencer timer, skip and finish-time defects from the component pass.
- Tab-stop cleanup in TaskSequencer and TeamDashboard (13, 14).
- Gremlin pink as status in TaskSequencer (11) and the notification palette (15).
- The canvas's "Now" task panel and "Start 5-min break" action.
- Root `dopemux-ui` shell and `ui-dashboard-backend/`: delete or revive (owner call).
