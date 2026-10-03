# Auditor Report: TP-DMX-MD-R5-UI-CONVERGENCE-001

- **Auditor**: Anthropic Claude (`claude-opus-5-5` via `claude-code`)
- **Implementer**: Google Gemini (`gemini-3.8-flash-high` via `agy`)
- **Base SHA**: `e9c34acdf741975508ea02a5fc2dfa229fe498db`
- **Candidate Head**: `c0e000336f4e8d8be1922234454c3768218f0a4a`
- **Verdict**: `FAIL`

## Verdict: FAIL
The UI source changes are mostly sound. The lockfile change is not. The packet states that the lockfile change is an `@humanfs/node` convergence, but there is no `@humanfs` change in it. What it actually does is revert security pins that were added in #1215.

## Findings

### [AUDIT-001] Lockfile regeneration reverts #1215 security overrides and downgrades ws 8.21.0 to 8.18.3 (BLOCKING - OPEN)
`ui-dashboard/pnpm-lock.yaml` deletes the whole overrides block (nanoid, @babel/core, postcss, brace-expansion, socket.io-parser, undici, ws 8.21.0, esbuild, yaml@^1.0.0). It re-resolves ws to 8.18.3 on the production path socket.io-client -> engine.io-client -> ws, and loosens pinned peer specs (@babel/core to ^7.0.0, esbuild to ^0.27.0 || ^0.28.0). package.json still pins ws 8.21.0. git log -S traces that pin to 5d694cc98 fix(security): close Dependabot vulnerability floors (#1215).

### [AUDIT-002] Lockfile change does not match its stated purpose (@humanfs/node convergence) (HIGH - OPEN)
`@humanfs/core@0.19.1` and `@humanfs/node@0.16.7` are identical at base and candidate, so the diff has no @humanfs change. The real content is the override removal and peer re-resolution in AUDIT-001.

### [AUDIT-003] Stale-promise tests are vacuous for PredictionPanel, TaskSequencer and CandidateShaChip (MEDIUM - OPEN)
Removing each stale-promise guard (currentPredictionRef, currentTaskIdRef, activeShaRef) still leaves all 53 tests passing. The PredictionPanel stale test resolves the promise and asserts outside act(), so the state update never flushes before the assertion. When the resolution is wrapped in await act(...), the test passes with the guard and fails without it.

### [AUDIT-004] RepositoryPlannerPage does not pass onError to PortfolioTable (LOW - OPEN)
PortfolioTable gained an optional onError, but RepositoryPlannerPage.tsx:165 renders PortfolioTable without it. Copy failures on the page only show as a 2-second visual chip state.

### [AUDIT-005] CandidateShaChip aria-label does not reflect the copyFailed state (LOW - OPEN)
In the failed state the visible label reads 'Copy failed: <sha>' but aria-label stays 'Copy candidate SHA <sha>'. The aria-label overrides the visible label, so screen-reader users get no failure feedback.

### [AUDIT-006] Step badges are focusable non-interactive spans with aria-label (INFO - ACCEPTED_RISK)
The Typography caption renders a span with tabIndex 0 and aria-label. This adds a tab stop per task with no action. Tooltip and label wording are redundant.

### [AUDIT-007] Ritual Complete aria-live is redundant and may not announce (INFO - ACCEPTED_RISK)
role=status already implies polite. The banner is mounted conditionally with its content already present, so many screen readers will not announce it whether or not aria-live is set.

### [AUDIT-008] UI source changes are otherwise correct; build, typecheck and tests verified independently (INFO - RESOLVED)
The review bundle matches git diff base..candidate. Independently re-ran in a clean worktree: frozen install OK, vitest 53/53, tsc 0 errors, vite build OK. Copy state and timer resets, onError propagation, timer cleanup on SHA change and unmount, and MUI Chip's single-trigger keyboard handling all behave as described.

## Remaining Risks
- Merging as-is ships ws 8.18.3 instead of the security-pinned 8.21.0 and leaves pnpm-lock.yaml inconsistent with package.json overrides.
- Under pnpm 12 the package.json pnpm.overrides block appears to be ignored, so any future lockfile regeneration will drop the security floors again unless the overrides move to pnpm-workspace.yaml.
- Stale-promise guards in three components have no test that would catch their removal.
- The audit ran on claude-opus-5-5, not the claude-sonnet-4-6 requested in ADMISSION_RECEIPT.json.
