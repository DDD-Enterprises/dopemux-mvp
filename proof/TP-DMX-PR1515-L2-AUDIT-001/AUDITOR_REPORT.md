# AUDITOR REPORT — PR #1515 L2 embedded audit (TP-DMX-PR1515-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.5.9, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-opus-5-5, no subagents), a different runner and model family
- **Audited head**: `7e1b129347efa21540bca4feacb3aa8120b4487f` · **Base**: `589bb0519424b84338ca2fcb7ae68f8607ef8b74` (main, the merge-base)
- **Follows up**: `TP-DMX-PR1509-L2-AUDIT-001` (PR #1509, audited head `eb5b6a1dd`, merged as `589bb0519`)
- **Verdict**: **PASS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw AGY stream, stderr and wrapper exit lines are in `review_bundle/`

## Why this audit

PR #1509 merged with one accurate risk from its governing Grok audit (TP-DMX-PR1509-L2-AUDIT-001): `snapshotSentForecastRef` was reset
when the GET effect ran, after the Retry click committed, so a state_update handled in that gap that sent
`predicted_load_15min` was forgotten and the retried GET could restore a forecast that snapshot cleared. `7e1b12934` resets the
flag in `handleRetry` beside `liveReadingSeenRef` and adds a regression test that failed before the fix. This audit covers
the whole PR diff.

## Operator approval of the audit route

Route request 2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too" (cockpit work, reused for
this follow-up); "Yes, do it here" 2026-11-15T17:47:47Z (Claude Code session d3cf0485). Recorded per
docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input, no-secret
constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "ok",
  "verdict": "PASS",
  "findings": [],
  "risks": [
    "Candidate test suite was not executed within this embedded audit session because tools and code execution are disabled by audit policy; verification of runtime test execution relies on CI for head SHA 7e1b129347efa21540bca4feacb3aa8120b4487f."
  ],
  "rationale": "Audited PR #1515 in DDD-Enterprises/dopemux-mvp comparing base SHA 589bb0519424b84338ca2fcb7ae68f8607ef8b74 to head SHA 7e1b129347efa21540bca4feacb3aa8120b4487f. In ui-dashboard/src/App.tsx, snapshotSentForecastRef.current was previously reset to false inside the GET useEffect rather than synchronously in handleRetry alongside liveReadingSeenRef.current. If a WebSocket state_update message carrying predicted_load_15min (including null) arrived after the Retry click handler ran but before the resulting GET useEffect executed, the useEffect reset snapshotSentForecastRef.current back to false and allowed a late-resolving GET forecast to overwrite the newer WebSocket snapshot state. Moving snapshotSentForecastRef.current = false into handleRetry (while relying on useRef(false) for initial mount) aligns its lifecycle with liveReadingSeenRef.current and closes this race condition. ui-dashboard/src/App.test.tsx adds a targeted regression test reproducing a state_update with predicted_load_15min: null between the Retry click and GET effect execution and asserting that a subsequent forecastGet(0.5) resolution does not overwrite the 'unknown' forecast state.",
  "inspected_paths": [
    "ui-dashboard/src/App.tsx",
    "ui-dashboard/src/App.test.tsx"
  ],
  "evidence_refs": [
    "repo:DDD-Enterprises/dopemux-mvp#1515",
    "base_sha:589bb0519424b84338ca2fcb7ae68f8607ef8b74",
    "head_sha:7e1b129347efa21540bca4feacb3aa8120b4487f",
    "ui-dashboard/src/App.tsx:105-115",
    "ui-dashboard/src/App.tsx:185-190",
    "ui-dashboard/src/App.test.tsx:502-529",
    "instruction_like_scan_summary:detected=false,match_count=0"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| none | | | |

## Corroboration (does not govern)

- **Grok** (grok-4.7, receipt `grok-4.7-build`, `init.tools == []`): PASS_WITH_RISKS; see `review_bundle/GROK_CORROBORATION.md`.
- **Codex** and **Copilot** (advisory GitHub reviews of `7e1b12934`): no findings.

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

The embedded-audit gate, recheck and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local tsc, vitest (115/115) and vite build pass at the audited head.
- Supervisor check of Grok's first risk against the code: the GET effect depends on [httpRetry, applyReading]; applyReading is a useCallback over two stable callbacks, and httpRetry changes only in handleRetry, which now resets the flag. So no current path re-runs the GET without the reset (StrictMode's mount re-run starts from false). A future refetch path must reset the flag too; not reachable today.
- Grok's second risk is about what the sealed audit could not run: the new race test was run locally, failed before the fix (forecast 50%) and passes after (LOCAL_VALIDATION.txt, 115/115).
- Audit scope: the whole PR diff, merge-base 589bb0519 to 7e1b12934; main has since moved (#1503) without touching this PR's files.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Codex and Copilot (advisory GitHub reviews) reviewed 7e1b12934 with no findings; they are not embedded auditors.
