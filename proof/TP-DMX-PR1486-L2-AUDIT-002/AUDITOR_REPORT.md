# AUDITOR REPORT — PR #1486 L2 embedded audit (TP-DMX-PR1486-L2-AUDIT-002)

- **Auditor**: AGY CLI 1.4.12, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5 supervisor, claude-sonnet-5-5 subagent lanes for the last commit), a different runner and model family
- **Audited head**: `0c031b26589f5ae07bc1a6801387b7c02f8e73ff` · **Base**: `97b6d5040496e2271c41d24c339d039303bbe6b1` (main)
- **Supersedes**: `TP-DMX-PR1486-L2-AUDIT-001` (head `962434ad`), kept unchanged as the round-5 record
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: raw streams, stderr and wrapper exit lines are in `review_bundle/`

## Why this round

After the round-5 proof was signed, Copilot review raised five code findings (C3-C7). The operator chose "Fix and re-audit"
(2026-11-01T03:10:28Z) and added r5 Grok F1 to the scope (03:13:03Z). Commit `0c031b265` fixes all six; this audit covers the
whole PR diff at that head. The 29 round-5 proof-only files are excluded from the prompt (`review_bundle/EXCLUDED_PROOF_FILES.txt`).

## Operator approval of the audit route

Route request 2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too"; re-audit request "Fix and re-audit"
2026-11-01T03:10:28Z (Claude Code session d3cf0485). Recorded per docs/ops/embedded-audit.md "Packet-specific supervisor-approved
fallback auditors": approval, bounded input, no-secret constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "id": "F-01",
      "severity": "low",
      "title": "WebSocket state_update snapshots overwrite initial HTTP 15-minute forecast with null and clear upstream HTTP error banners unconditionally",
      "path": "ui-dashboard/src/App.tsx",
      "lines": "211-221",
      "details": "In App.tsx, onmessage treats every valid 'state_update' WebSocket message as a complete reading replacement via applyReading(nextReading) and clears httpError. As documented in claudedocs/design/ui-dashboard-audit-2026-10-30.md:120-125, the backend state_update event does not include predicted_load_15min, so any forecast obtained from GET /api/adhd-state drops to null ('unknown') on the first live socket event. Additionally, setHttpError(null) clears partial upstream error warnings from the initial GET even if the socket update also omits those fields."
    },
    {
      "id": "F-02",
      "severity": "low",
      "title": "Restored ESLint flat config leaves pre-existing lint errors unresolved and unguarded in CI",
      "path": "ui-dashboard/eslint.config.js",
      "lines": "1-31",
      "details": "ui-dashboard/eslint.config.js restores ESLint v9/v10 flat configuration, but claudedocs/design/ui-dashboard-audit-2026-10-30.md:27-37 and 131-132 document that linting still fails with 16 errors and 2 warnings on pre-existing code in ui-dashboard/src and that no GitHub Actions workflow runs ui-dashboard lint or unit tests."
    },
    {
      "id": "F-03",
      "severity": "low",
      "title": "TaskSequencer and TeamDashboard remain backed by static sample data",
      "path": "ui-dashboard/src/components/TaskSequencer.tsx",
      "lines": "46-50, 552-563",
      "details": "TaskSequencer.tsx and TeamDashboard.tsx (lines 99-113) relabel their headers to '[SAMPLE] not connected' instead of '[LIVE]', resolving the false live-sync claim, but both components remain unwired to live backend task/team endpoints."
    }
  ],
  "risks": [
    "Candidate validation (tsc, eslint, vitest, vite build) was not executed in this embedded audit because tools and candidate execution are disabled by audit policy (validation_status=NOT_RUN).",
    "No CI workflow currently enforces ui-dashboard typecheck, lint, or vitest suites on pull requests, and 16 pre-existing lint errors remain in untouched component regions.",
    "Live WebSocket state_update payloads reset the 15-minute load prediction readout to 'unknown' until the backend includes predicted_load_15min in ws/state messages."
  ],
  "rationale": "Repository (DDD-Enterprises/dopemux-mvp), PR (1486), head SHA (0c031b26589f5ae07bc1a6801387b7c02f8e73ff), and base SHA (97b6d5040496e2271c41d24c339d039303bbe6b1) match trusted authority metadata, and the deterministic scanner detected no instruction-like content. The candidate diff across 22 files replaces fabricated fallback cognitive state readings (0.7/0.6/0.5) with explicit nullable readings in cognitiveReading.ts, guards against out-of-range ratios and invalid enum values, suppresses leaked upstream recommender error strings when task_recommendations contains an error object, prevents slow initial HTTP GET responses or errors from clobbering newer WebSocket state updates via liveReadingSeenRef in App.tsx, detaches WebSocket event handlers before closing sockets on effect cleanup, normalizes zone-less UTC timestamps in time.ts, and replaces CognitiveLoadGauge and PredictionPanel with LoadInstrument, AttentionStatePanel, and SignalFeed backed by new unit and integration test suites. Remaining issues are non-blocking follow-up items and unexecuted runtime validation.",
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
    "ui-dashboard/src/components/__tests__/SignalFeed.test.tsx",
    "ui-dashboard/src/features/repository-planner/PortfolioTable.tsx",
    "ui-dashboard/src/index.css",
    "ui-dashboard/src/realtimeStateMapping.test.ts",
    "ui-dashboard/src/theme.ts",
    "ui-dashboard/src/time.test.ts",
    "ui-dashboard/src/time.ts"
  ],
  "evidence_refs": [
    "repo:DDD-Enterprises/dopemux-mvp",
    "pr:1486",
    "head_sha:0c031b26589f5ae07bc1a6801387b7c02f8e73ff",
    "base_sha:97b6d5040496e2271c41d24c339d039303bbe6b1",
    "ui-dashboard/src/cognitiveReading.ts:12-105",
    "ui-dashboard/src/App.tsx:76-265",
    "ui-dashboard/src/App.test.tsx:43-355",
    "ui-dashboard/src/components/LoadInstrument.tsx:43-239",
    "ui-dashboard/src/components/__tests__/LoadInstrument.test.tsx:10-105",
    "ui-dashboard/src/components/AttentionStatePanel.tsx:37-120",
    "ui-dashboard/src/components/SignalFeed.tsx:33-200",
    "ui-dashboard/src/components/__tests__/SignalFeed.test.tsx:22-44",
    "ui-dashboard/src/components/TaskSequencer.tsx:46-50,552-563,1158-1162",
    "ui-dashboard/src/components/TeamDashboard.tsx:99-113",
    "ui-dashboard/src/time.ts:1-23",
    "ui-dashboard/src/time.test.ts:1-33",
    "ui-dashboard/eslint.config.js:1-31",
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md:118-148"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| AGY-F-01 | LOW | WebSocket state_update snapshots overwrite initial HTTP 15-minute forecast with null and clear upstream HTTP error banners unconditionally | OPEN |
| AGY-F-02 | LOW | Restored ESLint flat config leaves pre-existing lint errors unresolved and unguarded in CI | OPEN |
| AGY-F-03 | LOW | TaskSequencer and TeamDashboard remain backed by static sample data | OPEN |

## Corroboration (does not govern)

- **Grok** (grok-4.7, receipt `grok-4.7-build`, `init.tools == []`): PASS_WITH_RISKS; see `review_bundle/GROK_CORROBORATION.md`.
- **Codex** (advisory): not run this round.

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

The embedded-audit gate and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local tsc, vitest (91/91) and vite build pass at the audited head.
- ui-dashboard eslint exits 1 with 18 pre-existing problems in files this round did not touch; no CI job runs ui-dashboard lint or tests (AGY F-02).
- A state_update is a full snapshot: the GET forecast goes unknown on the first socket update, and a good update also clears the GET upstream-error warning (AGY F-01).
- TaskSequencer and TeamDashboard still render sample data labelled '[SAMPLE] not connected' (AGY F-03).
- Corroborating Grok G-1 (LOW, OPEN): Overtime text still uses brandTokens.colors.gremlinPink on the timer line this diff edits. theme.ts and index.css both define that token as a brand accent and not a status color.
- Corroborating Grok G-2 (LOW, OPEN): Zone geometry and deriveStatus disagree at the exact 0.6 and 0.8 edges. The needle at 60% and 80% sits on the next zone (PRESSURE, BREAK) while the text stays in the previous band (Flow Ritual, Pressure Build).
- Corroborating Grok risk (LOW): time.test.ts sets process.env.TZ at module load; runtime TZ changes may not hold on every Node/Vitest worker.
- Corroborating Grok risk (LOW): handleRetry resets liveReadingSeenRef before the old socket's handlers detach, so a queued message could make the retry GET ignored.
- Audit scope: the diff excluded the 29 round-5 proof-only files (EXCLUDED_PROOF_FILES.txt); those are unchanged since the r5 packet and no code.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Codex (advisory route from the original request) was not run this round.
