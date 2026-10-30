# Coordinator adjudication of the Grok audit - MACRO-DMX-MEMORY-BRIDGE-001-R2

Written after the raw artifacts were committed (`9ead56246`) and after reading the verdict. Each finding was checked against the committed source at content head `52855fb35ea40f420bdacdcab9e092f8d15292c6`.

**Overall**: I concur with `PASS_WITH_RISKS`. No BLOCKING or HIGH finding. The one failing question, Q9 (docs accuracy), rests on two confirmed documentation defects (N1 pinned commit SHA, N5 attempts wording); no finding shows a behavioural defect in the hook code. Q1-Q8 and Q10-Q12 are PASS. This audit's per-question verdicts all stay inside the PASS/FAIL/UNKNOWN enum (unlike the Pulse run).

| Id | Auditor severity | Adjudication |
|---|---|---|
| N1 | MEDIUM | CONFIRMED as a documentation defect; severity LOW, not MEDIUM |
| N2 | MEDIUM | CONFIRMED; severity LOW; the wording is a packet defect |
| N3 | LOW | CONFIRMED and disclosed; severity LOW stands; candidate for an accepted-risk ruling |
| N4 | LOW | PARTIALLY CONFIRMED; severity INFO; the ReDoS framing is not substantiated |
| N5 | LOW | CONFIRMED as a documentation inaccuracy; severity LOW |
| N6 | INFO | CONFIRMED; severity INFO |
| N7 | INFO | CONFIRMED; disclosure, not a defect; severity INFO |

### N1 (MEDIUM) - docs/02-how-to/memory-bridge.md

**Auditor**: How-to claims code HEAD `1ce149a76` and verification at that commit; frozen audit head is `52855fb35ea40f420bdacdcab9e092f8d15292c6`.

**Adjudication**: CONFIRMED as a documentation defect; severity LOW, not MEDIUM.

`docs/02-how-to/memory-bridge.md` lines 19 and 137 cite commit `1ce149a76`. `git diff 1ce149a76 52855fb35 -- plugins` is empty: the only change after it is the how-to itself, so the cited facts (code at that commit, 105 tests, validate pass) are true of the frozen tree. The defect is the pinned SHA: it reads as the delivered head and goes stale at the next commit, the same pattern the Pulse audit raised as F4 and repaired. Repair is a docs-only edit (drop the SHA) but it changes the audited subject, so it needs the operator's decision.

### N2 (MEDIUM) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Slash command description says 'Store a note in the capture ledger' while the command reply and intent require queued-not-stored messaging.

**Adjudication**: CONFIRMED; severity LOW; the wording is a packet defect.

`register.tsx:1208` registers the description `Store a note in the capture ledger`; `register.tsx:1240` replies `Queued your note ... Nothing is stored yet`. The description came from the issuance packet (W03 invariant L03) and the implementer followed it. Menu text overclaims relative to the queued-then-replayed behaviour. Repair is one string.

### N3 (LOW) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Status pending includes other sessions' replayable rows that this mod will never send, so 📮 N pending can stick until those files change outside this process.

**Adjudication**: CONFIRMED and disclosed; severity LOW stands; candidate for an accepted-risk ruling.

`readPrior` adds other sessions' replayable pending rows to `foldedPending`, while replay walks only this process's rings, so `📮 N pending` can stay non-zero for rows another (ended) session left. README lines 106, 151 and 184 and the how-to's Not built table say other sessions' rows are counted but not replayed. Behaviour is documented and intended as a limit, but the label `pending` is misleading for those rows. A proper fix is the undesigned adoption rule.

### N4 (LOW) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: decisionsOf runs RegExp matchAll on the full unbounded assistant answer before any size bound.

**Adjudication**: PARTIALLY CONFIRMED; severity INFO; the ReDoS framing is not substantiated.

`decisionsOf` calls `matchAll` on the whole `answer` with no pre-trim (`register.tsx:209-216`), unlike `clean()`. The regex is anchored per line with no nested quantifiers, so the cost is linear in the answer length per finished turn, not catastrophic. No stored content is affected.

### N5 (LOW) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: Successful ledger emit increments attempts; docs describe attempts as failed-delivery counters.

**Adjudication**: CONFIRMED as a documentation inaccuracy; severity LOW.

On exit 0 the code writes `attempts: row.attempts + 1` (a sent row has attempts 1; tested). `README.md:43` describes `attempts` as `a counter of failed delivery attempts`. Behaviour is harmless and tested; the README line is inaccurate.

### N6 (INFO) - plugins/dopemux-memory-bridge/hooks/register.tsx

**Auditor**: On /clear, fold path that increments foldedPending from isReplayable is unreachable.

**Adjudication**: CONFIRMED; severity INFO.

In the `/clear` branch (`register.tsx` about 1350-1366) the ring is deleted only when no entry is replayable, so the `if (isReplayable(entry.row)) s.foldedPending += 1` branch can never run. Dead code; behaviour is correct.

### N7 (INFO) - plugins/dopemux-memory-bridge/README.md

**Auditor**: Live behaviour, real ledger emit, desktop $.process, fs.write atomicity, and pre-commit hooks remain NOT_RUN / UNKNOWN as disclosed.

**Adjudication**: CONFIRMED; disclosure, not a defect; severity INFO.

Live behaviour, a real `dopemux capture emit`, the desktop `$.process`, `$.fs.write` atomicity and the pre-commit hooks are NOT_RUN / UNKNOWN, exactly as the README, how-to and `RETURN-01.md` state. The operator's live smoke test is the clearing action.

## What the audit does not settle

- The auditor had no tools; it judged the diff text only. Its `needs_more_evidence` list (live session, real ledger emit, desktop `$.process`, `$.fs.write` parent-directory behaviour, `.gitignore` lines, the 105-test count) is NOT_RUN or was verified here only by the coordinator's own gate run (105 pass; `.gitignore:140` and `:299` read at issuance).
- The auditor self-reported `grok-4` while the CLI init event shows `grok-4.5`: provider-attested identity is UNKNOWN. `audit_identity.independence` is left unattested.
- Nothing was repaired after the audit. Repairing N1, N2, N5 (and optionally N6) is a small docs-and-string change that would alter the audited subject; whether to repair and re-audit, or accept the risks, is the operator's call. This session did not run a second audit and made no content change.
