# ui-dashboard build proof - 2026-05-31

## Scope

- Task Packet: `task-packets/generated/TP-UI-DASHBOARD-BUILD-001.json`
- Branch: `fix/ui-dashboard-build`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-ui-dashboard-build`
- Base branch: `main`
- Target: restore `ui-dashboard` `npm install`, tests, and `npm run build` without force or legacy peer dependency flags.

## Observed failure

`npm install` failed in `ui-dashboard` because `eslint-plugin-react-hooks@4.6.2` did not declare peer support for `eslint@10.1.0`.

After updating the peer-compatible plugin, `npm run build` exposed missing project wiring/source files:

- `tsconfig.json`
- `index.html`
- `src/main.tsx`
- `src/components/CognitiveLoadGauge.tsx`
- `src/components/PredictionPanel.tsx`
- `src/components/TeamDashboard.tsx`

## Change

- Updated `eslint-plugin-react-hooks` to `^7.1.1`, which declares peer support for ESLint 10.
- Added the missing Vite entrypoint files required by the existing `build` script.
- Added the missing dashboard components imported by `src/App.tsx`.
- Kept generated `dist/` output untracked.

## Validation

PASS:

- `python -m json.tool task-packets/generated/TP-UI-DASHBOARD-BUILD-001.json >/dev/null`
- `python -m jsonschema -i task-packets/generated/TP-UI-DASHBOARD-BUILD-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `git diff --check`
- `cd ui-dashboard && npm install`
  - Result: up to date, audited 395 packages, 0 vulnerabilities.
- `cd ui-dashboard && npm test -- --run`
  - Result: 3 test files passed, 16 tests passed.
- `cd ui-dashboard && npm run build`
  - Result: `tsc && vite build` exited 0 and emitted `dist/index.html`, CSS, and JS assets.
- Browser smoke at `http://127.0.0.1:5174/`
  - Result: rendered `Dopemux Ultra UI` with `main` content and no Vite error overlay.
  - Backend was not running, so the dashboard correctly rendered degraded state with `Failed to fetch`.
  - Alert close interaction removed the visible alert text.
- PAL codereview with `gpt-5-codex`
  - Result: no issues found.
- `pre-commit run --files ui-dashboard/package.json ui-dashboard/package-lock.json ui-dashboard/tsconfig.json ui-dashboard/index.html ui-dashboard/src/main.tsx ui-dashboard/src/components/CognitiveLoadGauge.tsx ui-dashboard/src/components/PredictionPanel.tsx ui-dashboard/src/components/TeamDashboard.tsx task-packets/INDEX.md task-packets/generated/TP-UI-DASHBOARD-BUILD-001.json claudedocs/ui-dashboard-build-proof-2026-05-31.md`
  - Result: passed.

WARN:

- Vite build logs existing MUI package-level `"use client"` directive warnings but exits 0.
- Browser console logs a React `validateDOMNesting` warning rooted in existing `TaskSequencer`; this is outside the TP build-fix scope.
- Clipboard copy interaction was blocked by browser permission during smoke validation; the app surfaced the failure as an alert.

NOT_RUN:

- Full repository test suite.
- Backend integration with live ADHD engine/API.

## Residual risk

- The added dashboard components are minimal implementations inferred from existing `App.tsx` imports and static accessibility tests.
- Runtime data behavior remains dependent on the backend API/WebSocket service, which was not started for this build-focused slice.
