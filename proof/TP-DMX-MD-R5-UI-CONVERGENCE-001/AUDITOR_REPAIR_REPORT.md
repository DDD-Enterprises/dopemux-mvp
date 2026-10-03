# Auditor Repair Report: TP-DMX-MD-R5-UI-CONVERGENCE-001 (re-audit)

- **Auditor**: Anthropic Claude (`claude-sonnet-5-5` via Claude Code CLI)
- **Implementer**: Google Gemini (`gemini-3.8-flash-high` via `agy`)
- **Base SHA**: `e9c34acdf741975508ea02a5fc2dfa229fe498db` (verified)
- **Candidate HEAD audited**: `6f86c4e5218b834ba604a3b1e8cf28d01d643dcd`
- **Verdict**: `PASS_WITH_RISKS`

## SHA discrepancy
The audit prompt names candidate `6f86c4e5254199c08605ee78fb6d766ce51b88e1`. That object does not exist in the repository (`bad object`). Only the first 8 hex characters match the real HEAD above. The audited content is HEAD, and the review bundle matches `git diff base..HEAD` byte-for-byte. The packet owner should correct the SHA in the dispatch record.

## Verification performed
- `CANDIDATE_UNIFIED_DIFF.txt` is identical to `git diff e9c34acdf HEAD`.
- `git diff --check`: clean.
- Six files changed, all under `ui-dashboard/src`. `package.json` and `pnpm-lock.yaml` diffs against base are 0 lines, and the lockfile diff against `origin/main` is 0 lines.
- vitest 54/54, `tsc --noEmit` clean, `vite build` OK (269ms).
- Mutation checks (guard removed, then restored with `git checkout`):
  - PredictionPanel stale guard removed: 1 test fails, so the guard is now tested.
  - TaskSequencer `currentTaskIdRef` guard removed: 54/54 still pass.
  - PortfolioTable `activeShaRef` guards removed: 54/54 still pass.
- Behavioral probe (temporary test, deleted afterward): in `CandidateShaChip`, a successful copy followed by a rejected copy within 2s leaves the chip on "Candidate SHA ... copied" permanently, even after the timers advance 10s.

## Findings
- AUDIT-001 BLOCKING, RESOLVED: lockfile restored, ws 8.21.0 and the #1215 overrides intact.
- AUDIT-002 HIGH, RESOLVED: the mismatched lockfile change is gone.
- AUDIT-003 MEDIUM, OPEN (partially resolved): the PredictionPanel test now wraps resolution in `act()` and fails without the guard. TaskSequencer and CandidateShaChip stale guards are still untested.
- AUDIT-004 LOW, RESOLVED: `copyError` state, error Alert and `onError={setCopyError}` are wired.
- AUDIT-005 LOW, RESOLVED: aria-label switches to the failure text on `copyFailed`, and a test covers it.
- AUDIT-006 INFO, ACCEPTED_RISK: focusable non-interactive step badges, unchanged.
- AUDIT-007 INFO, ACCEPTED_RISK: redundant `aria-live` on the Ritual Complete banner, unchanged.
- AUDIT-009 LOW, OPEN (new): `CandidateShaChip` failure path never clears `isCopied`, so success then failure within 2s leaves a stuck false-success state. The failure path also clears the timer that would have reset it. `onError` still fires, so the page Alert appears. Fix: call `setIsCopied(false)` in both failure branches.
- AUDIT-008 INFO, RESOLVED: UI source is otherwise correct and the build is verified.
- AUDIT-010 INFO, OPEN: prompt candidate SHA does not exist (see above).

## Remaining risks
See the JSON `remaining_risks`.
