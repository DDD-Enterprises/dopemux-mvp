# Coordinator adjudication of the Grok final audit (MACRO-DMX-ROUTE-LEDGER-001-R2)

Written AFTER the custody commit `03844022e1eedb4495b9e24104428c02851758a2` that preserved every raw artifact; the verdict was first read after that commit.
Audited content head `93969e7a3ca2775c7b435e1ce1b6528ad2173c4a`, base `93050d135ffc2592000c1d0edef82b2912935525`. Auditor verdict: `PASS_WITH_RISKS`; Q1-Q11 all PASS; no BLOCKING finding; ten findings N1-N10 (1 HIGH, 4 MEDIUM, 4 LOW, 1 INFO).
Each finding below was checked against the committed source (file and line named). Severities are the auditor's, unchanged. Adjudication never raises the verdict and never marks a risk accepted: acceptance is the operator's.

| Id | Auditor severity | Adjudication | Evidence and disposition |
|---|---|---|---|
| N1 | HIGH | CONFIRMED | No real session has loaded the mod: the coordinator's gates are all mock-engine, and the README and how-to say so. Not fixable inside this macro. Operator step: `claude --plugin-dir plugins/dopemux-route-ledger` with `.control-tower/state` present, one pinned and one unpinned Agent call, one advisor use in a child, then read the receipt file and run `/route-ledger`. |
| N2 | MEDIUM | CONFIRMED | register.tsx checks only for a `..` segment, an empty or root path, and the default directory's parent `.control-tower/state`; it never calls `$.fs.stat`, so a symlink at or under an explicit `receiptDir` is followed. The setting is the operator's own plugin config and the mod writes only `<dir>/<sanitized id>[.n].jsonl`, so the blast radius is that of the host process's own file permissions. Disclosed (limitation vii). Residual risk, no repair in this macro; a possible follow-up is a `$.fs.stat` check that refuses a symlinked directory. |
| N3 | MEDIUM | CONFIRMED | `s.segments` is appended at register.tsx lines 643 and 788 and reset only on init; a rolled-over segment stays in memory with all its receipts. Growth is linear in receipts for the process lifetime (roughly half a kilobyte to a kilobyte per receipt), so a very long session grows by megabytes, not unboundedly fast. Flush rewrites only dirty segments, so write cost does not grow with it. Residual; a follow-up could keep only counters and the last main step for closed segments. |
| N4 | MEDIUM | CONFIRMED | `flushSegments` counts a failed write in `receiptsFailed` and leaves the segment dirty, and `session.end` schedules one flush and awaits the chain once; after `isEnded` nothing records again, so a failed final flush loses the dirty tail (earlier flushed segments stay on disk). The status line shows ` · receipts ✗` after the first failure, so the loss is visible while the session runs. Failure of a local file write is exceptional. Residual; by design no tight retry loop. |
| N5 | MEDIUM | CONFIRMED, BY DESIGN | `session.end` with reason `clear` returns `next(e)` untouched (the W01 packet requires it, as in Pulse), so after `/clear` receipts continue to the old session id's file. Disclosed as limitation (v) and in the code comment. It keeps counting rather than losing data; a later change could re-resolve the session id lazily. |
| N6 | LOW | CONFIRMED | The unpinned-agent toast at register.tsx line 889 passes only a message (the host default duration); budget toasts pass `timeoutMs: 8000`. Cosmetic inconsistency; no repair after freeze. |
| N7 | LOW | CONFIRMED | `statusText` prints the session advisor total over the child budget when only a child is over it (`advisor 1/0 ⚠`); the README says only `advisor N/B ⚠` once a budget B applies and is exceeded. Flagged to the operator at freeze as an open design call. Follow-up wording or semantics change. |
| N8 | LOW | CONFIRMED | register.test.ts advances 1000 ms (`DEBOUNCE_MS`, line 290) while the code debounces 500 ms (`STATUS_DEBOUNCE_MS`, line 41), so a regression to a value up to 1000 ms would still pass. Test hygiene only. |
| N9 | LOW | CONFIRMED | Receipts and the unpinned toast carry the Agent call's `description`, truncated to 80 characters, unredacted. The prompt is never recorded (a test asserts it). Disclosed (limitation viii). Receipts live in the gitignored `.control-tower/state/` by default. |
| N10 | INFO | ACKNOWLEDGED | The declaration drifted from 2.1.304 (implementers) to 2.1.308 (this session's reload) while the CLI is 2.1.309. The audited files type-check against the 2.1.308 declaration with the default engine options (GATES.txt), which is extra evidence against drift but is not the in-tree `tsc -p` (NOT_RUN). Pulse status-line coexistence is unverified and disclosed. |

Additional notes from the auditor's other fields:

- **README wording nit (auditor's Q8 note)**: CONFIRMED, trivial. README says receipts are 'one file (segment) per session' and then describes the `.1.jsonl` roll-over. Wording only; no repair after freeze.
- **needs_more_evidence: ct validate-binding evidence is not in the diff**: ANSWERED. Correct: it is coordinator evidence, not code. It is in `review_bundle/GATES.txt` (three receipt `binding_fields` samples merged into a copy of a valid binding pass `ct validate-binding`; `ct bind-record` was not run).

## What this adjudication does not do

- No repair was made after the freeze: the macro allows 0 post-freeze repair rounds and 0 further audits without the operator. Every finding is OPEN in the proof.
- The auditor had no tools and judged the diff text only; it could not run the code. Its self-reported identity `grok-4` differs from the CLI's `grok-4.5`; provider-attested identity is UNKNOWN.
- The questions' own verdict fields all used the contract enum (`PASS`), unlike the Pulse R2 run; the top-level status is the contract-valid `PASS_WITH_RISKS`.
