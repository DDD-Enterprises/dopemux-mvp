# Coordinator adjudication of the Grok re-audit - MACRO-DMX-MEMORY-BRIDGE-001-R3

Written after the raw artifacts were committed (`4988d5ee0`) and after reading the verdict. Findings were checked against the committed source at the repaired content head `c71e7c1f436349f477037d28ce479218c63a53a4`.

**Overall**: I concur with `PASS_WITH_RISKS`. All 13 questions are PASS (Q9, the docs-accuracy question that failed in the first audit, now passes). N1, N2 and N5 are REPAIRED. The four deliberately unrepaired findings (N3, N4, N6, N7) are STILL_PRESENT exactly as accepted before. One new INFO finding (N8) is a design note without a demonstrated defect. No BLOCKING, HIGH or MEDIUM finding remains. The auditor self-reported `grok-4.7` while the CLI init event shows `grok-4.5`: provider-attested identity is UNKNOWN, and `audit_identity.independence` stays unattested.

## Closure of the first audit's findings

| Id | Auditor disposition | Coordinator adjudication |
|---|---|---|
| N1 | REPAIRED | REPAIRED (concur) |
| N2 | REPAIRED | REPAIRED (concur) |
| N3 | STILL_PRESENT | STILL_PRESENT, accepted follow-up; severity LOW stands |
| N4 | STILL_PRESENT | STILL_PRESENT, accepted follow-up; severity LOW; no ReDoS |
| N5 | REPAIRED | REPAIRED (concur) |
| N6 | STILL_PRESENT | STILL_PRESENT, accepted follow-up; INFO |
| N7 | STILL_PRESENT | STILL_PRESENT, disclosure; INFO |

## Findings the auditor lists as open at this head

| Id | Auditor severity | Adjudication |
|---|---|---|
| N3 | LOW | STILL_PRESENT, accepted follow-up; severity LOW stands |
| N4 | LOW | STILL_PRESENT, accepted follow-up; severity LOW; no ReDoS |
| N6 | INFO | STILL_PRESENT, accepted follow-up; INFO |
| N7 | INFO | STILL_PRESENT, disclosure; INFO |
| N8 | INFO | CONFIRMED as a design note; severity INFO; no defect shown |

### N3 (LOW) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Status pending includes other sessions' replayable rows that this mod never sends, so 📮 N pending may not clear for those N.

**Adjudication**: STILL_PRESENT, accepted follow-up; severity LOW stands.

Unchanged by the repair and deliberately out of scope. `readPrior` adds other sessions' replayable rows to `foldedPending` while replay walks only this process's rings; documented in the README and the how-to. The operator accepted this finding on 2026-10-24 for the predecessor head; it is not re-accepted for this head.

### N4 (LOW) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Decision regex runs on unbounded assistant answer text.

**Adjudication**: STILL_PRESENT, accepted follow-up; severity LOW; no ReDoS.

Unchanged and out of scope. `decisionsOf` runs `matchAll` on the whole answer with no pre-bound; the regex is line-anchored without nested quantifiers, so cost is linear per finished turn. Accepted for the predecessor head on 2026-10-24; not re-accepted for this head.

### N6 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Dead branch in /clear fold increments foldedPending for isReplayable inside a block that requires none.

**Adjudication**: STILL_PRESENT, accepted follow-up; INFO.

Unreachable `isReplayable` branch in the `/clear` fold; harmless. Accepted for the predecessor head; not re-accepted for this head.

### N7 (INFO) - docs/02-how-to/memory-bridge.md

**Auditor**: Mod has never run in a real Claude Code session; proof is test-kit only.

**Adjudication**: STILL_PRESENT, disclosure; INFO.

Live behaviour, a real `dopemux capture emit`, the desktop `$.process`, `$.fs.write` atomicity and the pre-commit hooks are NOT_RUN / UNKNOWN, as the README and how-to say. The operator's live smoke test remains the clearing action.

### N8 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Observing tool.call intentionally does not await observeTool before returning, relying on host microtask ordering so turn digests stay complete.

**Adjudication**: CONFIRMED as a design note; severity INFO; no defect shown.

`register.tsx:1273-1281`: the `tool.call` hook awaits `next(e)`, then starts `observeTool` with `void` and returns the result unchanged, so the host's tool call is never delayed. A turn's `turn.complete` follows at least one model round-trip, and `observeTool` only awaits a cached root lookup and an append, so the digest is complete in practice; the tests settle the mock clock. Production interleaving is UNKNOWN, which is the auditor's own wording. New finding, not a regression: the pattern was in the first audited head and the first audit did not raise it.

## What the audit does not settle

- The auditor had no tools; it judged the diff text only. Its `needs_more_evidence` list (live session, real process calls on CLI and desktop, `$.fs.write` atomicity, plugin order relative to Pulse, independent re-run receipts) is NOT_RUN. The coordinator's own gate run at this head (validate exit 0, 105 tests, `tsc` 2.1.309 exit 0, docs validators, change-contract preflight PASS) is recorded in `PROOF.json`.
- The repair was verified by the coordinator, not only by the children: the W01 and W02 diffs were re-read line by line (exactly the intended 5 insertions and 7 deletions against the first audited head `52855fb35ea40f420bdacdcab9e092f8d15292c6`).
- Nothing was repaired after this audit. No second audit of this head was run. Signing, attestation, push and the PR stay with the operator.
