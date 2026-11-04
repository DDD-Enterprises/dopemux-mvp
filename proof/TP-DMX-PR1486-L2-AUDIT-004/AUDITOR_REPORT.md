# AUDITOR REPORT — PR #1486 L2 embedded audit (TP-DMX-PR1486-L2-AUDIT-004)

- **Auditor**: AGY CLI 1.4.12, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5 supervisor; claude-sonnet-5-5 subagent lanes for two earlier fix commits), a different runner and model family
- **Audited head**: `682a4711d0464cc9dd166a267e9743b6ee2e55ba` · **Base**: `75dacb43f651f0326a3c0146aae0c5301d6c08da` (main, the merge-base)
- **Supersedes**: `TP-DMX-PR1486-L2-AUDIT-003` (head `aaa2d1ae0`), kept unchanged as the round-7 record
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw AGY stream, stderr and wrapper exit lines are in `review_bundle/`

## Why this round

The operator asked to squash-merge after round 7 was signed, but #1483 had landed on main (75dacb43f) and main requires
an up-to-date branch. The operator chose "Update, fix, re-audit": main was merged in (87ebb3fbd) and `682a4711d` fixes
round-7 Grok G-1 (a GET landing after a live update lost its forecast) and G-2 (the 15-minute forecast expiry ran only on
the next snapshot). This audit covers the whole PR diff against main at that head; the 89 proof-only files of rounds
5-7 are excluded from the prompt (`review_bundle/EXCLUDED_PROOF_FILES.txt`).

## Operator approval of the audit route

Route request 2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too"; round-8 request "Update,
fix, re-audit" 2026-11-04T09:04:47Z (Claude Code session d3cf0485). Recorded per
docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input, no-secret
constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "ok",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "id": "F-01",
      "severity": "low",
      "title": "Late GET forecast backfill does not distinguish omitted vs explicitly cleared WS forecast",
      "file": "ui-dashboard/src/App.tsx",
      "lines": "250-254",
      "description": "When the initial GET /api/adhd-state resolves after a live WebSocket state_update, App.tsx backfills readingRef.current.prediction whenever it is null. If a prior state_update explicitly carried an invalid or null predicted_load_15min, the older GET forecast still overwrites it and updates lastUpdated. Because the backend engine currently omits predicted_load_15min from state_update events, this is benign today but could surface if the WS payload contract is extended."
    },
    {
      "id": "F-02",
      "severity": "low",
      "title": "Timezone test mutates process.env.TZ in-process without restoring or isolating TZ",
      "file": "ui-dashboard/src/time.test.ts",
      "lines": "5-6",
      "description": "time.test.ts sets process.env.TZ = 'America/Los_Angeles' at module scope after imports. If Vitest reuses a worker process where Date local timezone caching was already initialized by a prior test suite, local-time assertions at lines 30-33 can become execution-order dependent."
    }
  ],
  "risks": [
    "Pre-existing ESLint violations remain in untouched parts of ui-dashboard (documented in claudedocs/design/ui-dashboard-audit-2026-10-30.md as 16 errors and 2 warnings), and no CI workflow currently enforces ui-dashboard lint or unit tests.",
    "TaskSequencer and TeamDashboard remain backed by static sample data; although now honestly labelled '[SAMPLE] not connected' instead of '[LIVE]', live endpoint wiring is deferred to follow-up work.",
    "Validation was not executed in this embedded audit because candidate code execution and tools are disabled by policy (validation_status=NOT_RUN)."
  ],
  "rationale": "The diff for PR #1486 (head 682a4711d0464cc9dd166a267e9743b6ee2e55ba over base 75dacb43f651f0326a3c0146aae0c5301d6c08da) replaces fabricated fallback telemetry in ui-dashboard with explicit nullable readings (EMPTY_READING in cognitiveReading.ts) that render as 'unknown' when backend data is missing or out of range. Misleading status claims are corrected ('[LIVE]' -> '[SAMPLE] not connected' in TaskSequencer.tsx and TeamDashboard.tsx; verified consent claim -> '[CONSENT: UNKNOWN]' in App.tsx). Race conditions between initial HTTP state fetches and WebSocket state_update messages, partial upstream error reporting, and 15-minute forecast TTL carry-over/expiry are cleanly handled and covered by unit/component tests. Accessibility and visual clarity are improved by replacing CognitiveLoadGauge and PredictionPanel with LoadInstrument (with edge-safe rounding and ARIA meter semantics), AttentionStatePanel, and SignalFeed (persistent ARIA live log), while removing the scanline overlay and global CSS transition:all. Minor residual risks remain around pre-existing lint debt, lack of CI gating for ui-dashboard, and a minor late-GET forecast backfill edge case.",
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
    ".gitignore:441-442",
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md:118-153",
    "src/dopemux/ui/theme.py:302-303",
    "ui-dashboard/eslint.config.js:6-31",
    "ui-dashboard/src/cognitiveReading.ts:33-141",
    "ui-dashboard/src/App.tsx:86-326",
    "ui-dashboard/src/App.tsx:388-545",
    "ui-dashboard/src/App.test.tsx:44-554",
    "ui-dashboard/src/components/LoadInstrument.tsx:56-256",
    "ui-dashboard/src/components/AttentionStatePanel.tsx:37-118",
    "ui-dashboard/src/components/SignalFeed.tsx:33-198",
    "ui-dashboard/src/components/TaskSequencer.tsx:47-49",
    "ui-dashboard/src/components/TaskSequencer.tsx:552-563",
    "ui-dashboard/src/components/TaskSequencer.tsx:1158-1161",
    "ui-dashboard/src/components/TeamDashboard.tsx:99-113",
    "ui-dashboard/src/index.css:5-63",
    "ui-dashboard/src/theme.ts:5-116",
    "ui-dashboard/src/time.ts:3-23",
    "ui-dashboard/src/time.test.ts:5-33",
    "ui-dashboard/src/realtimeStateMapping.test.ts:13-176",
    "ui-dashboard/src/components/__tests__/LoadInstrument.test.tsx:10-136",
    "ui-dashboard/src/components/__tests__/SignalFeed.test.tsx:22-44"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| AGY-F-01 | LOW | Late GET forecast backfill does not distinguish omitted vs explicitly cleared WS forecast | OPEN |
| AGY-F-02 | LOW | Timezone test mutates process.env.TZ in-process without restoring or isolating TZ | OPEN |

## Corroboration (does not govern)

- **Grok** (grok-4.7, receipt `grok-4.7-build`, `init.tools == []`): PASS_WITH_RISKS; see `review_bundle/GROK_CORROBORATION.md`.
- **Codex** (advisory): not run this round.

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | NOT_RUN |
| 🧪 Unit Tests | NOT_RUN |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local: npx tsc --noEmit (ui-dashboard) | PASS |
| local: npx vitest run (ui-dashboard) | PASS |
| local: npx vite build (ui-dashboard) | PASS |
| local: npx eslint src (ui-dashboard) | FAIL |
| audit: validation inside the sealed AGY session | NOT_RUN |

The embedded-audit gate and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local tsc, vitest (107/107) and vite build pass at the audited head.
- AGY AGY-F-01 (LOW, OPEN): Late GET forecast backfill does not distinguish omitted vs explicitly cleared WS forecast
- AGY AGY-F-02 (LOW, OPEN): Timezone test mutates process.env.TZ in-process without restoring or isolating TZ
- Corroborating Grok G-1 (MEDIUM, OPEN): After any live state_update, a still-in-flight GET is ignored for load, energy, attention, recommendation, and upstream errors, then still applied when its mapped prediction is non-null and the current prediction is null. That branch calls applyReading without forecastCarried, so the late body becomes a new forecast arrival: forecastReceivedAtRef is set to Date.now(), the 15-minute expiry timer restarts, and lastUpdated advances. A socket snapshot that included predicted_load_15min and mapped it to null is treated the same as a snapshot that never had a forecast, so the older GET can put a number back on screen.
- Corroborating Grok G-2 (MEDIUM, OPEN): The task queue and team board are still local sample data with the sequencer controls left in place. The chip text is now [SAMPLE] not connected, and TeamDashboard has the same label. A known load band still runs the sample sequence and the footer says the sequencer is calibrated for that band.
- Corroborating Grok G-3 (LOW, OPEN): The overtime clock still uses brandTokens.colors.gremlinPink. theme.ts labels that token as a brand accent that is never a status color, and this refresh edited the same timer style block while leaving the color in place.
- Corroborating Grok G-4 (LOW, OPEN): Retry always clears liveReadingSeenRef, sets the socket to connecting, and bumps retryTrigger, which closes the current WebSocket and opens another. A retry for an HTTP failure while the socket is open drops a live socket.
- Supervisor check of AGY F-01 and Grok G-1 against the code: both accurate. The late-GET branch fills any null prediction, so it cannot tell a snapshot that omitted predicted_load_15min from one that sent it as null or invalid. Not reachable with today's engine, whose state_update never includes the key.
- Grok G-2 is the same sample-data state as round-6 AGY F-03: TaskSequencer and TeamDashboard still render data labelled '[SAMPLE] not connected'.
- Grok G-3 (gremlinPink overtime clock) and G-4 (Retry always reopens the socket) are in code this round did not change.
- Audit scope: the diff is main (75dacb43f, the merge-base) to 682a4711d minus the 89 proof-only files of rounds 5-7 (EXCLUDED_PROOF_FILES.txt); the #1483 files brought in by merge 87ebb3fbd are main's and not in that diff.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Codex (advisory route from the original request) was not run this round.
