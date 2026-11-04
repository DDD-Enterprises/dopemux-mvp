# AUDITOR REPORT — PR #1486 L2 embedded audit (TP-DMX-PR1486-L2-AUDIT-003)

- **Auditor**: AGY CLI 1.4.12, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5 supervisor, claude-sonnet-5-5 subagent lanes for the fix commits), a different runner and model family
- **Audited head**: `aaa2d1ae05048443da7e0e68104f54bbc53075c2` · **Base**: `6fb9d81798cbcca7f99c96f1b9fd07b6d3c7db68` (main, the merge-base)
- **Supersedes**: `TP-DMX-PR1486-L2-AUDIT-002` (head `0c031b265`), kept unchanged as the round-6 record
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw AGY stream, stderr and wrapper exit lines are in `review_bundle/`

## Why this round

The operator asked to merge after round 6 was signed, but #1482 had landed on main (6fb9d8179) and main requires an
up-to-date branch. The operator chose "Update and re-audit" and option 2: main was merged in (636b543c7) and `aaa2d1ae0`
fixes round-6 AGY F-01 (socket snapshot blanked the GET forecast and cleared the GET upstream warning) and Grok G-2 (load
markers at exactly 60%/80% sat in the next zone). This audit covers the whole PR diff against main at that head; the
58 proof-only files of rounds 5-6 are excluded from the prompt (`review_bundle/EXCLUDED_PROOF_FILES.txt`).

## Operator approval of the audit route

Route request 2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too"; round-7 request "Update and
re-audit" 2026-11-01T06:30:33Z and scope "22" (option 2) 06:30:40Z (Claude Code session d3cf0485). Recorded per
docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input, no-secret
constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "id": "F-1",
      "severity": "low",
      "path": "ui-dashboard/src/time.test.ts",
      "lines": "5-6",
      "title": "Module-level process.env.TZ mutation is not restored after tests",
      "detail": "ui-dashboard/src/time.test.ts sets process.env.TZ = 'America/Los_Angeles' at module scope without restoring the original TZ value in afterAll. While safe when Vitest isolates each test file, running tests in a shared worker (--no-isolate) could leak the timezone override to subsequent test files."
    },
    {
      "id": "F-2",
      "severity": "low",
      "path": "claudedocs/design/ui-dashboard-audit-2026-10-30.md",
      "lines": "135-136",
      "title": "ESLint flat config restored but pre-existing lint errors and missing CI gate remain",
      "detail": "ui-dashboard/eslint.config.js restores a working ESLint 10 flat configuration, but the audit report notes 16 errors and 2 warnings remain in untouched files and no CI workflow currently runs ui-dashboard lint or unit tests."
    }
  ],
  "risks": [
    "Validation commands (tsc, vitest, eslint, vite build) were not executed during this audit because tools and MCP are disabled by the embedded-audit contract (validation_status=NOT_RUN).",
    "TaskSequencer and TeamDashboard remain backed by static sample data rather than live backend endpoints, though both surfaces now explicitly render '[SAMPLE] not connected' instead of '[LIVE]'.",
    "Pre-existing lint violations in untouched ui-dashboard files (16 errors, 2 warnings per claudedocs/design/ui-dashboard-audit-2026-10-30.md) and the absence of a CI job for ui-dashboard leave lint/test regressions unguarded in automation."
  ],
  "rationale": "Provenance checks match across trusted authority and candidate metadata for DDD-Enterprises/dopemux-mvp PR #1486 at head SHA aaa2d1ae05048443da7e0e68104f54bbc53075c2 and base SHA 6fb9d81798cbcca7f99c96f1b9fd07b6d3c7db68, with no instruction-like content detected. The diff eliminates fabricated fallback metrics (0.7/0.6/0.5) by introducing nullable CognitiveReading mappers in ui-dashboard/src/cognitiveReading.ts, surfaces partial HTTP 200 upstream section errors and WebSocket failures accurately in ui-dashboard/src/App.tsx, preserves 15-minute forecast TTL across partial state_update messages via carryForecast, replaces CognitiveLoadGauge and PredictionPanel with LoadInstrument (with boundary-safe percentage rounding) and AttentionStatePanel, relabels static task/team boards as '[SAMPLE] not connected', removes the global '* { transition: all 0.25s ease }' rule and scanline overlay in ui-dashboard/src/index.css, and adds unit/integration test coverage across App.test.tsx, LoadInstrument.test.tsx, SignalFeed.test.tsx, realtimeStateMapping.test.ts, and time.test.ts. Verdict is PASS_WITH_RISKS due to unexecuted runtime validation in this tool-disabled audit context and documented follow-up items.",
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
    "ui-dashboard/src/cognitiveReading.ts:12-141 (nullable CognitiveReading model, enum/ratio validators, upstreamErrorSections, mapAggregateState, mapRealtimeState, carryForecast with 15-min FORECAST_TTL_MS, remainingUpstreamSections)",
    "ui-dashboard/src/App.tsx:84-291 (EMPTY_READING initial state, race-safe loadInitialState with liveReadingSeenRef guard, WebSocket state_update forecast carry and partial upstream error clearing, handler detachment on socket cleanup)",
    "ui-dashboard/src/components/LoadInstrument.tsx:56-63 (toPercent zone-edge-aware rounding preventing status/percentage band contradiction)",
    "ui-dashboard/src/components/AttentionStatePanel.tsx:37-118 (definition-list rendering of energyLevel and attentionState with explicit unknown fallback)",
    "ui-dashboard/src/components/SignalFeed.tsx:135-195 (persistent role='log' aria-live='polite' ordered list with empty-state text outside the log region and Escape-cancelable two-step clear confirmation)",
    "ui-dashboard/src/components/TaskSequencer.tsx:552-563,1158-1162 ('[SAMPLE] not connected' chip and unknown load status handling)",
    "ui-dashboard/src/components/TeamDashboard.tsx:99-113 ('[SAMPLE] not connected' badge)",
    "ui-dashboard/src/index.css:24-38 (removal of global transition:all, scanline body::after overlay, and external Google Fonts import)",
    "ui-dashboard/src/time.ts:3-23 (asUtcIso zone-less UTC normalization with 3-digit millisecond truncation and formatClockTime)",
    "ui-dashboard/src/App.test.tsx:44-464 (integration tests covering unreachable backend, HTTP 500, invalid JSON, malformed state_update, slow GET race against live socket update, partial upstream errors, and 15-min forecast TTL expiry)"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| AGY-F-1 | LOW | Module-level process.env.TZ mutation is not restored after tests | OPEN |
| AGY-F-2 | LOW | ESLint flat config restored but pre-existing lint errors and missing CI gate remain | OPEN |

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

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local tsc, vitest (102/102) and vite build pass at the audited head.
- AGY AGY-F-1 (LOW, OPEN): Module-level process.env.TZ mutation is not restored after tests
- AGY AGY-F-2 (LOW, OPEN): ESLint flat config restored but pre-existing lint errors and missing CI gate remain
- Corroborating Grok G-1 (MEDIUM, OPEN): In-flight GET is discarded entirely once any state_update arrives, including the only forecast source
- Corroborating Grok G-2 (MEDIUM, OPEN): Forecast 15-minute TTL is checked only when another state_update arrives
- Corroborating Grok G-3 (LOW, OPEN): Critical load is not a live announcement
- Round-6 AGY F-03 is unchanged: TaskSequencer and TeamDashboard still render sample data labelled '[SAMPLE] not connected' (also a Grok round-7 risk).
- Supervisor check of Grok G-1/G-2 against the code: both are accurate. G-1 predates round 7 (liveReadingSeenRef discards a GET that lands after a state_update), but the forecast now depends on that GET landing first; G-2 is introduced by the F-01 carry-over (expiry is evaluated only on the next snapshot).
- Audit scope: the diff is main (6fb9d8179, the merge-base) to aaa2d1ae0 minus the 58 proof-only files of rounds 5-6 (EXCLUDED_PROOF_FILES.txt); the #1482 files brought in by merge 636b543c7 are main's and not in that diff.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Codex (advisory route from the original request) was not run this round.
