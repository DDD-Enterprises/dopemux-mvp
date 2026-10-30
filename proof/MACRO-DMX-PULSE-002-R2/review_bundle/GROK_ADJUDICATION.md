# MACRO-DMX-PULSE-002-R2 - adjudication of the Grok final audit

Subject: content head `b5dc04dd7d9560ed31a2dc0fd2192218c727ea01`, cumulative base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`. Auditor `grok-cli` / `grok-4.5` (self-reported `grok-4`), tool-less (`init.tools == []`), 1 turn, exit 0.
**Verdict (verbatim, not relabelled): `PASS_WITH_RISKS`.** Q1-Q10 PASS; Q11 `PASS_WITH_RISKS`. The predecessor audit of PR #1472 (head `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`, `PASS_WITH_RISKS`, Q3 FAIL on F1) is preserved unchanged under `proof/MACRO-DMX-PULSE-001/`; this verdict is a separate, new record on a different subject.
Adjudicator: coordinator (Claude Sonnet 5.5). Authority NONE. Nothing pushed, signed or merged.

## Predecessor findings

| Finding | Auditor disposition | Coordinator adjudication | Evidence checked |
|---|---|---|---|
| F1 / old Q3 orphaned `$.http.fetch` | REPAIRED | CONFIRMED REPAIRED under the mocked test kit: `isFetching` is cleared only when the fetch chain settles, `poll` returns while it is set, the late answer is discarded. Host behaviour (does the host ever settle an abandoned request) stays UNKNOWN. | `register.tsx` `fetchState`, `poll`; tests T1-T4; coordinator's own mutation (drop `|| s.isFetching`) failed T1-T3 and was restored byte-identical; `tsc` PASS |
| F2 never run live | OUT_OF_SCOPE | AGREED, still OPEN (operator step, NOT_RUN) | README and how-to "Not verified" |
| F3 `/done` wording | REPAIRED | CONFIRMED REPAIRED | README and how-to diffs at C; `stopContinuous` runs on `/break` and `/done` |
| F4 commit SHA | REPAIRED | CONFIRMED REPAIRED | no-hash/no-PR-number grep PASS at C |
| F5 engine suite failures | OUT_OF_SCOPE | AGREED; the engine is untouched by this macro (closure check 4) and the earlier base-versus-head comparison stands | `CLOSURE_CHECKS.txt` |
| F6 swallowed registration failure | REPAIRED | CONFIRMED REPAIRED under the mock (`deny` -> toast). Whether production `$.command.register` rejects when it refuses a name is UNKNOWN: the declaration says only "a built-in's name is refused"; if it does not reject, no toast would show. | `registerCommand`; T5; declaration text |
| F7 fallback answers HTTP 200 | OUT_OF_SCOPE | AGREED, pre-existing and documented | how-to section 5 |

## New findings

| ID | Severity | Adjudication | Evidence | Status |
|---|---|---|---|---|
| N1 | HIGH | CONFIRMED; same fact as F2, no new information | "Not verified" sections; live run NOT_RUN | OPEN (operator step) |
| N2 | MEDIUM | CONFIRMED, by design, disclosed in the code comment, README and how-to: if the host never settles an abandoned request, polling pauses and the status stays `unreachable`. Not an operator-accepted risk yet; the operator may accept or ask for a bounded design | `fetchState` comment; host timeout UNKNOWN | OPEN |
| N3 | LOW | CONFIRMED: only `/break` has a test that resets the 90-minute clock (`a break resets the 90-minute continuous-focus clock`); `/done` calls `stopContinuous` in the code but no test asserts it. Frozen head is not changed to add one | `register.test.ts` lines 372-382; `stopContinuous` in the done handler | OPEN |
| N4 | LOW | CONFIRMED and PRE-EXISTING (logic unchanged since the audited PULSE-001 head): after a first failed poll `wasUp` is `false`, so the first success toasts `ADHD engine is back` although the engine was never up in the session; the README says the toast fires when a reachable engine "comes back". T2 pins this under the timeout-then-healthy case. A wording or logic nit, not introduced by the repair | `register.tsx` lines 188-195; README lines 16-18; how-to section 6 | OPEN |
| N5 | INFO | CONFIRMED, pre-existing, same as F7 | `routes.py` except branch | OPEN |

## Auditor's needs_more_evidence

1. Full `get_adhd_state` body: not re-checked here; `routes.py` is unchanged since the audited PULSE-001 head (closure check 4), and that audit asked the same.
2. A live session transcript: NOT_RUN.
3. Whether production `$.command.register` rejects or returns a deny: UNKNOWN (see F6).
4. Host timeout for an abandoned fetch: UNKNOWN (see N2).

## Format notes

The auditor's Q11 field carried `PASS_WITH_RISKS`, outside the prompt's per-question enum. The top-level `status` is valid. `model_self_reported` is `grok-4` while the init event shows `grok-4.5`. No instruction-like content was reported or found.

## Operator decisions left

1. Attest `audit_identity.independence` (left `UNATTESTED-OPERATOR-MUST-SET-PROVEN-BEFORE-SIGNING`). Containment is now machine-evidenced in `GROK_AUDIT_STREAM.txt` and `GROK_PROBE2_STREAM.txt`.
2. Accept or reject N2 (and the carried F2, F7) as disclosed residual risks.
3. Delivery vehicle: fast-forward `feat/pulse-001` so PR #1472 carries the successor head, or a stacked draft PR based on `feat/pulse-001`. Push, signing and merge are not granted by this macro.
