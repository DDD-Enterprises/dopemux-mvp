# AUDITOR REPORT — PR #1509 L2 embedded audit (TP-DMX-PR1509-L2-AUDIT-001)

- **Auditor**: Grok CLI 1.0.77, `grok-4.7` (receipt grok-4.7-build), contained with `init.tools == []`; prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5, no subagents), a different runner and model family
- **Audited head**: `eb5b6a1dd2f6d0927b19046818aecd389dd5b5fe` · **Base**: `264c97b23ec1b3e007e62079d4f6d2632ad71775` (main, the merge-base)
- **Follows up**: `TP-DMX-PR1486-L2-AUDIT-004` (PR #1486, audited head `682a4711d`, merged as `4cd889877`)
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw Grok stream (emails redacted), stderr and wrapper exit line are in `review_bundle/`

## Why this audit

PR #1486 merged with findings open from its last audit (TP-DMX-PR1486-L2-AUDIT-004). This PR fixes four of them: AGY F-01 / Grok G-1
(a late GET could restore a forecast a snapshot cleared), Grok G-4 (Retry dropped a live socket), Grok G-3 (overtime used the
gremlinPink brand accent) and AGY F-02 (time.test.ts left TZ changed). Copilot found that a later snapshot without the key
reset the guard; a2ca0ee4b fixed that, and Codex reported no findings on it. At a2ca0ee4b AGY returned a 429 quota error and
Grok one LOW (a constant between imports); `eb5b6a1dd` fixes that and this fresh Grok run governs (`review_bundle/PRIOR_ATTEMPTS.md`).

## Operator approval of the audit route

Route request 2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too" (cockpit work, reused for this
follow-up); "Yes, do it here" 2026-11-12T12:27:23Z; "Fix, Grok governs" 2026-11-12T13:18:49Z (Claude Code session d3cf0485).
Recorded per docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input,
no-secret constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "complete",
  "verdict": "PASS_WITH_RISKS",
  "findings": [],
  "risks": [
    "Retry still assigns liveReadingSeenRef false while an open socket keeps the last state_update and the [LIVE] indicator. The GET effect patches forecast only on the else-if (isMounted) path, and the comment on that effect says the other path may apply the GET reading and its failure. handleRetry takes that other path for a fast refetch because it clears the latch and, when socketState is open, leaves the socket effect mounted. The new retry test asserts forecast text 50% and a single FakeSocket, and leaves load, attention, recommendation, and a failed refetch unasserted, so a newer live reading can be replaced by the aggregate GET until the next state_update.",
    "snapshotSentForecastRef is cleared when the GET effect runs, after the retry click has already committed. A state_update handled in that gap can record an explicit predicted_load_15min and then lose that block when the effect resets the ref before fetch resolves.",
    "The design note's 'lands after a snapshot' sentence allows a late GET to fill an unknown forecast only when the snapshot omitted the key. The retry test requires a later GET to restore 50% after a snapshot that sent predicted_load_15min null. The code follows the test by resetting the flag for each new GET. Those two readings of the same doc edit need to stay aligned.",
    "clickRetry uses within and fireEvent, and the App.test.tsx diff has no import change. That compiles when those names are already in scope. theme.ts is outside the diff, so the claim that giltEdge is the status warning color is carried by the new comment and by the existing >80% bar use. Overtime and progressPercent > 80 now share giltEdge; the OVERTIME label still separates overrun. Runtime TZ assignment in beforeAll is checked only by the new getHours assertion, and this audit did not run Vitest."
  ],
  "rationale": "At eb5b6a1dd2f6d0927b19046818aecd389dd5b5fe the candidate diff matches the updated forecast note and the new tests. sendsForecast is true when message.data contains predicted_load_15min, including null, and carryForecast's early return uses that helper in place of the previous inline key check, so a snapshot that includes the key still keeps its own mapped value. snapshotSentForecastRef starts false on each GET effect and is set with ||= on every state_update, so a later snapshot that omits the key preserves an earlier explicit clear. The late GET writes prediction only when the mapped forecast is non-null, the current prediction is null, and that flag is clear. handleRetry always increments httpRetry and increments socketRetry, setting socketState to connecting, only when socketState is not open; the socket effect depends on socketRetry, so an open socket stays up. The added App tests cover a null forecast key, a following keyless snapshot that leaves unknown and shows 46%, retry with one socket and [LIVE], retry after onclose with a second socket and [CONNECTING], and a retry GET that shows 50%. TaskSequencer routes overtime through OVERTIME_COLOR = brandTokens.colors.giltEdge, and the accessibility source test requires that token and excludes gremlinPink on the overtime lines. time.test.ts sets America/Los_Angeles in beforeAll, restores the captured TZ in afterAll, and expects getHours() === 7 for 2026-10-30T14:01:55Z. The candidate scanner reported instruction-like content detected false with match_count 0; the diff was treated as data. Checkout, execution, and tools were forbidden, so the suite is NOT_RUN and the verdict rests on the diff.",
  "inspected_paths": [
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md",
    "ui-dashboard/src/App.test.tsx",
    "ui-dashboard/src/App.tsx",
    "ui-dashboard/src/cognitiveReading.ts",
    "ui-dashboard/src/components/TaskSequencer.tsx",
    "ui-dashboard/src/components/__tests__/Accessibility.test.tsx",
    "ui-dashboard/src/time.test.ts"
  ],
  "evidence_refs": [
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md: late GET fills an unknown forecast only when the snapshot omitted predicted_load_15min; Retry refetches and reopens the socket only when it is not open",
    "ui-dashboard/src/App.tsx handleRetry: setHttpRetry always; setSocketState('connecting') and setSocketRetry only inside if (socketState !== 'open'); liveReadingSeenRef set false on every retry",
    "ui-dashboard/src/App.tsx GET effect: snapshotSentForecastRef.current = false; forecast apply condition adds && !snapshotSentForecastRef.current; dependency array [httpRetry, applyReading]",
    "ui-dashboard/src/App.tsx socket handler: snapshotSentForecastRef.current ||= sendsForecast(message) before applyReading; effect dependency array [socketRetry, applyReading, reportSocketError]",
    "ui-dashboard/src/cognitiveReading.ts: sendsForecast checks isMessageObject(message), isMessageObject(message.data), and 'predicted_load_15min' in message.data; carryForecast returns next when sendsForecast(message) is true",
    "ui-dashboard/src/App.test.tsx: 'a late GET does not bring back a forecast the socket cleared'; 'a later snapshot without the key does not let a late GET restore a cleared forecast'; 'Retry after a failed GET keeps an open socket'; 'Retry reopens a closed socket'; 'Retry is a new GET: its forecast replaces one an earlier snapshot cleared'",
    "ui-dashboard/src/components/TaskSequencer.tsx: OVERTIME_COLOR = brandTokens.colors.giltEdge applied to the overtime timer, OVERTIME caption, and overtime progress bar",
    "ui-dashboard/src/components/__tests__/Accessibility.test.tsx: source expects OVERTIME_COLOR and brandTokens.colors.giltEdge, and expects overtime lines to exclude gremlinPink",
    "ui-dashboard/src/time.test.ts: beforeAll assigns America/Los_Angeles; afterAll deletes or restores originalTz; test expects new Date('2026-10-30T14:01:55Z').getHours() to be 7"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| none | | | |

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
| audit: validation inside the sealed Grok session | NOT_RUN |

The embedded-audit gate, recheck and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit session (validation_status=NOT_RUN); local tsc, vitest (114/114) and vite build pass at the audited head.
- Grok risk: Retry still assigns liveReadingSeenRef false while an open socket keeps the last state_update and the [LIVE] indicator. The GET effect patches forecast only on the else-if (isMounted) path, and the comment on that effect says the other path may apply the GET reading and its failure. handleRetry takes that other path for a fast refetch because it clears the latch and, when socketState is open, leaves the socket effect mounted. The new retry test asserts forecast text 50% and a single FakeSocket, and leaves load, attention, recommendation, and a failed refetch unasserted, so a newer live reading can be replaced by the aggregate GET until the next state_update.
- Grok risk: snapshotSentForecastRef is cleared when the GET effect runs, after the retry click has already committed. A state_update handled in that gap can record an explicit predicted_load_15min and then lose that block when the effect resets the ref before fetch resolves.
- Grok risk: The design note's 'lands after a snapshot' sentence allows a late GET to fill an unknown forecast only when the snapshot omitted the key. The retry test requires a later GET to restore 50% after a snapshot that sent predicted_load_15min null. The code follows the test by resetting the flag for each new GET. Those two readings of the same doc edit need to stay aligned.
- Grok risk: clickRetry uses within and fireEvent, and the App.test.tsx diff has no import change. That compiles when those names are already in scope. theme.ts is outside the diff, so the claim that giltEdge is the status warning color is carried by the new comment and by the existing >80% bar use. Overtime and progressPercent > 80 now share giltEdge; the OVERTIME label still separates overrun. Runtime TZ assignment in beforeAll is checked only by the new getHours assertion, and this audit did not run Vitest.
- Supervisor check of Grok's risks against the code: the second one is accurate. snapshotSentForecastRef is reset when the GET effect runs, which is after the Retry click commits; a state_update handled in that gap that sends predicted_load_15min is forgotten, so the retried GET could fill a forecast that snapshot cleared. Resetting the ref inside handleRetry would close the gap. Not fixed here (follow-up).
- Grok's first and third risks describe intended behaviour: a Retry GET is sent after the earlier snapshots, so it applies in full; the design note's late-GET rule covers a GET that was already in flight when a snapshot landed.
- Audit scope: the whole PR diff, main (264c97b23, the merge-base) to eb5b6a1dd.
- Auditor model identity: requested grok-4.7; receipt grok-4.7-build; provider-attested identity beyond the receipt UNKNOWN.
- AGY, the planned governing auditor, returned no verdict (429 quota) at the earlier head; no AGY corroboration exists for this packet.
- Codex (advisory) reviewed a2ca0ee4b and the audited head eb5b6a1dd on GitHub with no findings; it is advisory, not an embedded auditor.
