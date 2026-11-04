# AUDITOR REPORT — PR #1486 L2 embedded audit (TP-DMX-PR1486-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.4.11, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5), a different runner and model family
- **Audited head**: `962434ad61bde3efdd6bd938f81ffdfbe358e71c` · **Base**: `97b6d5040496e2271c41d24c339d039303bbe6b1` (main)
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Containment**: two conversation steps (user input, agent response), no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **TRANSCRIPT_RECOVERED_NOT_AUDITOR_WRITTEN** (see below)

## Operator approval of the audit route

The operator asked on 2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too" (queued user message in Claude Code
session d3cf0485). This is the last round of that route, run on the final head after earlier rounds and their fixes. Recorded per
docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input, no-secret constraints,
exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Evidence recovery

A disk cleanup deleted the session scratchpad that held the raw AGY stream, stderr, invocation file and prompt. This bundle rests on:

- the AGY conversation store and CLI log, copied byte-identically into off-repo custody (`review_bundle/CUSTODY.md`, `CUSTODY_SHA256SUMS.txt`);
- the session transcript, which kept the exact command, the exit notice and the verdict parsed at audit time;
- a rebuilt prompt that equals the prompt both auditors received, apart from a trailing newline the runners strip.

Details and the inferred exit code: `review_bundle/AGY_RUN_RECORD.md`, `AUDIT_INVOCATION.txt`.

## Auditor return (recovered, verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "id": "F-1",
      "severity": "low",
      "path": "ui-dashboard/src/App.tsx",
      "lines": "195-203",
      "summary": "WebSocket state_update messages overwrite reading state as a full snapshot, clearing the initial HTTP 15-minute forecast to null ('unknown') when the backend WebSocket payload omits predicted_load_15min.",
      "details": "In ui-dashboard/src/App.tsx:195-203 and ui-dashboard/src/cognitiveReading.ts:61-74, mapRealtimeState treats every state_update message as a complete snapshot rather than merging partial fields. As documented in claudedocs/design/ui-dashboard-audit-2026-10-30.md:118-125, services/adhd_engine/core/engine.py does not currently publish predicted_load_15min in state_update payloads, so the 15-minute forecast displays after the initial GET /api/adhd-state and then transitions to 'unknown' on the first WebSocket update."
    },
    {
      "id": "F-2",
      "severity": "low",
      "path": "ui-dashboard/eslint.config.js",
      "lines": "1-31",
      "summary": "ESLint flat configuration is restored, but pre-existing lint errors in untouched files and missing CI enforcement remain.",
      "details": "ui-dashboard/eslint.config.js restores a working ESLint 10 flat config, but claudedocs/design/ui-dashboard-audit-2026-10-30.md:27-37 and :131-132 note that 16 errors and 2 warnings remain in untouched files and no GitHub Actions workflow runs ui-dashboard lint or unit tests."
    }
  ],
  "risks": [
    "Validation commands (tsc, eslint, vitest, vite build) were not executed during this embedded audit because tools and candidate code execution are disabled by policy (validation_status=NOT_RUN).",
    "Pre-existing ESLint errors (16 errors, 2 warnings) in untouched ui-dashboard files and the absence of a CI workflow gating ui-dashboard mean lint/test regressions are not automatically blocked in CI.",
    "TaskSequencer (ui-dashboard/src/components/TaskSequencer.tsx:553-563) and TeamDashboard (ui-dashboard/src/components/TeamDashboard.tsx:99-113) still render static seeded data, though they are now explicitly labeled '[SAMPLE] not connected' instead of '[LIVE]'.",
    "Candidate file claudedocs/design/ui-dashboard-audit-2026-10-30.md contains audit terminology (role names, PASS/FAIL tables) which was treated strictly as untrusted candidate data."
  ],
  "rationale": "The diff for PR #1486 (head 962434ad61bde3efdd6bd938f81ffdfbe358e71c against base 97b6d5040496e2271c41d24c339d039303bbe6b1 in DDD-Enterprises/dopemux-mvp) remediates fabricated telemetry and UI/accessibility defects in ui-dashboard. Specifically: (1) ui-dashboard/src/cognitiveReading.ts and ui-dashboard/src/App.tsx replace hardcoded fallback metrics (0.7 energy, 0.6 attention, 0.5 load) with nullable CognitiveReading fields so unmeasured or out-of-range values render as 'unknown'; (2) App.tsx tracks HTTP and WebSocket failures separately, prevents slow initial GET responses from overwriting newer live WebSocket updates via liveReadingSeenRef, detaches socket handlers on cleanup, and surfaces actionable failure alerts; (3) LoadInstrument, AttentionStatePanel, and SignalFeed replace CognitiveLoadGauge and PredictionPanel with accessible semantics (role='meter', role='log', two-step clear confirmation) and honest '[CONSENT: UNKNOWN]' and '[SAMPLE] not connected' labels; (4) index.css and theme.ts remove the contrast-reducing body::after scanline overlay, global '* { transition: all 0.25s ease }', and external Google Fonts import in favor of Direction B tokens and local Dopemux font stacks; and (5) unit/integration tests in App.test.tsx, LoadInstrument.test.tsx, and realtimeStateMapping.test.ts cover failure, race-condition, and boundary cases. Residual risks around unexecuted validation in this embedded environment, remaining lint issues in untouched files, and backend WebSocket forecast parity justify PASS_WITH_RISKS.",
  "inspected_paths": [
    ".gitignore",
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md",
    "src/dopemux/ui/theme.py",
    "ui-dashboard/eslint.config.js",
    "ui-dashboard/src/App.test.tsx",
    "ui-dashboard/src/App.tsx",
    "ui-dashboard/src/cognitiveReading.ts",
    "ui-dashboard/src/components/AttentionStatePanel.tsx",
    "ui-dashboard/src/components/CognitiveLoadGauge.tsx",
    "ui-dashboard/src/components/LoadInstrument.tsx",
    "ui-dashboard/src/components/PredictionPanel.tsx",
    "ui-dashboard/src/components/SignalFeed.tsx",
    "ui-dashboard/src/components/TaskSequencer.tsx",
    "ui-dashboard/src/components/TeamDashboard.tsx",
    "ui-dashboard/src/components/__tests__/Accessibility.test.tsx",
    "ui-dashboard/src/components/__tests__/LoadInstrument.test.tsx",
    "ui-dashboard/src/features/repository-planner/PortfolioTable.tsx",
    "ui-dashboard/src/index.css",
    "ui-dashboard/src/realtimeStateMapping.test.ts",
    "ui-dashboard/src/theme.ts",
    "ui-dashboard/src/time.ts"
  ],
  "evidence_refs": [
    ".gitignore:441-442",
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md:118-148",
    "src/dopemux/ui/theme.py:302-303",
    "ui-dashboard/eslint.config.js:1-31",
    "ui-dashboard/src/cognitiveReading.ts:26-74",
    "ui-dashboard/src/App.tsx:73-253",
    "ui-dashboard/src/App.tsx:316-393",
    "ui-dashboard/src/App.tsx:416-470",
    "ui-dashboard/src/App.test.tsx:43-286",
    "ui-dashboard/src/components/LoadInstrument.tsx:41-231",
    "ui-dashboard/src/components/__tests__/LoadInstrument.test.tsx:10-63",
    "ui-dashboard/src/components/AttentionStatePanel.tsx:39-120",
    "ui-dashboard/src/components/SignalFeed.tsx:33-196",
    "ui-dashboard/src/components/TaskSequencer.tsx:46-49",
    "ui-dashboard/src/components/TaskSequencer.tsx:552-563",
    "ui-dashboard/src/components/TaskSequencer.tsx:1158-1161",
    "ui-dashboard/src/components/TeamDashboard.tsx:99-113",
    "ui-dashboard/src/components/__tests__/Accessibility.test.tsx:104-105",
    "ui-dashboard/src/features/repository-planner/PortfolioTable.tsx:104",
    "ui-dashboard/src/index.css:5-38",
    "ui-dashboard/src/realtimeStateMapping.test.ts:5-87",
    "ui-dashboard/src/theme.ts:5-79",
    "ui-dashboard/src/time.ts:2-8"
  ],
  "validation_status": "NOT_RUN",
  "instruction_like_acknowledged": true
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| AGY-F-1 | LOW | WebSocket state_update messages overwrite reading state as a full snapshot, clearing the initial HTTP 15-minute forecast to null ('unknown') when the backend WebSocket payload omits predicted_load_15min. | OPEN |
| AGY-F-2 | LOW | ESLint flat configuration is restored, but pre-existing lint errors in untouched files and missing CI enforcement remain. | OPEN |

The operator chose on 2026-10-30 to leave them as they are. That is a decision not to fix, not an acceptance of risk.

## Corroboration (does not govern)

- **Grok** (grok-4.7, receipt `grok-4.7-build`, tool-less): PASS_WITH_RISKS. F1 MEDIUM: socket errors are not cleared by a later valid
  update. F2 LOW: the design memo's base and results were not re-run for this head. `review_bundle/GROK_CORROBORATION.md`.
- **Codex** (gpt-6-astra, advisory only): NEEDS_SUPERVISOR on provenance plus one MEDIUM: a load between 0.8000 and 0.8005 can show
  "80%" beside "Break. Now.". Raw output not retained.

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | PASS |
| 🧪 Unit Tests | PASS |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local: npx tsc --noEmit (ui-dashboard) | PASS |
| local: npx vitest run (ui-dashboard) | PASS |
| local: npx vite build (ui-dashboard) | PASS |
| local: npx eslint src (ui-dashboard) | FAIL |
| audit: validation inside the sealed AGY session | NOT_RUN |

The embedded-audit gate and PR Steward fail because this signed proof does not exist yet.

## Remaining risks

- Validation was not run inside the sealed audit session (validation_status=NOT_RUN); CI unit tests pass at the audited head and local tsc, vitest (75/75) and vite build pass.
- ui-dashboard lint (eslint) exits 1 with 16 errors and 2 warnings; blame puts every flagged line in commits that predate this PR (ESLINT_ATTRIBUTION.txt), though three of the files are edited elsewhere by the PR; no CI job runs ui-dashboard lint or tests.
- TaskSequencer and TeamDashboard still render seeded sample data, now labelled '[SAMPLE] not connected'.
- Corroborating Grok F1 (MEDIUM, OPEN): a socket parse, unexpected-message or malformed-update error stays on screen after a later valid state_update; only Retry clears it.
- Corroborating Grok F2 (LOW, OPEN): the design memo records base 93050d135 and reports check results that were not re-run for this head.
- Advisory Codex (not an auditor): a load between 0.8000 and 0.8005 can show '80%' beside 'Break. Now.'.
- Auditor model identity: requested gemini-4-argon-high; AGY client metadata records 'Gemini 4 Argon (High)'; provider-attested identity UNKNOWN; recorded as the schema's family value 'gemini'.
- Evidence is TRANSCRIPT_RECOVERED_NOT_AUDITOR_WRITTEN: the raw AGY stream was deleted before bundling; the verdict was recovered from AGY's own conversation store and matches the parse recorded in the session transcript at audit time; exit_code 0 is inferred from the final result event and the harness notice.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
