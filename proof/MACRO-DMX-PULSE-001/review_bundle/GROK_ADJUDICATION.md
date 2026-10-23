# MACRO-DMX-PULSE-001 — adjudication of the Grok final audit

Subject: `feat/pulse-001` @ `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`, base `95e95bee8`.
Auditor: grok-cli / grok-4.5, tool-less (`init.tools == []`), 1 turn, exit 0. Verdict `PASS_WITH_RISKS`; Q3 = FAIL.
Prior attempt: agy `gemini-4-argon-high` failed at start, `RESOURCE_EXHAUSTED` 429, 0 tokens (launched 2026-10-22T10:59:37Z). Record it in the proof; do not hide it.
Adjudicator: coordinator (Claude Sonnet 5.5). Authority NONE. Nothing pushed, signed or merged.

| Finding | Auditor sev | Adjudication | Evidence |
|---|---|---|---|
| F1 / Q3 orphaned `$.http.fetch` after the 2 s race | MEDIUM | CONFIRMED, real. `fetchState` cancels only the timer; `poll` releases `isPolling` after the race, so a hung engine leaves one pending GET per 60 s poll. Bounded only by the host's own network timeout (UNKNOWN). Needs an operator decision: accept, or repair (keep the guard until the fetch settles) and re-audit. | `register.tsx` `fetchState`, `poll` |
| F2 never run live | HIGH | CONFIRMED, disclosed. Operator step NOT_RUN: engine on 127.0.0.1:3025, then `claude --plugin-dir plugins/dopemux-pulse`. | README and how-to "Not verified" |
| F3 continuous-focus wording | LOW | PARTLY. The code comment matches the code (the count starts at the first `/pulse-focus`). Real gap: the README says only `/break` resets the count, but `/done` also does. | README lines 23-28 vs `stopContinuous` |
| F4 registry and SHA claims | LOW | Port claim VERIFIED: `services/registry.yaml` has adhd-engine `port: 3025`, `container_port: 8095`. Commit SHA `3dbced397` will not survive a squash merge (still true). | `services/registry.yaml:183-186` |
| F5 28 failures and 4 collection errors | MEDIUM | RESOLVED. Same command on base and head with `--continue-on-collection-errors`: base 28 failed, 88 passed, 4 errors; head 28 failed, 92 passed, 4 errors. Failing ID sets are identical, so the head adds only the 4 new passing tests. | `F5_BASE_RUN.txt`, `F5_HEAD_RUN.txt` |
| F6 swallowed `command.register` failure | LOW | CONFIRMED. `.catch(() => undefined)` at `register.tsx:227-233`. | source |
| F7 fallback answers HTTP 200 | INFO | CONFIRMED, pre-existing and documented. | how-to §5 |

Any fix to F1, F3 or F4 changes the audited subject, so it needs a new audit. A new audit needs an operator-approved route (agy quota resets about 2026-10-24T03:30Z).

## Evidence note
The raw Grok and agy streams and the first F5 outputs were lost when the session scratchpad was deleted. The frozen diff (sha256 matches), the audit prompt (52805 bytes, sha256 `3e0510fe...ce69`) and the F5 comparison (re-run, same result) were regenerated. The Grok response is a transcription whose length matches the original (11435 bytes). See `GROK_RUN_RECORD.md`.

## Operator decisions left
1. F1: DECIDED. The operator accepted it as a disclosed residual risk on 2026-10-22 and kept the audited head `1d2219e8c`. No repair or re-audit.
2. Attest `audit_identity.independence` (left `UNATTESTED-OPERATOR-MUST-SET-PROVEN-BEFORE-SIGNING`), knowing the containment streams are lost.
3. Push, PR and signing, all still ungranted.
