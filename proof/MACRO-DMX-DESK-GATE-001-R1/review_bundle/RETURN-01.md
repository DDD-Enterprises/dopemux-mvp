# MACRO-DMX-DESK-GATE-001-R1 - Aggregate Return 01

**Status**: `RETURNED_FOR_SUPERVISOR`. The final independent audit returned `PASS` (grok-cli, `grok-4.7` requested, observed model UNKNOWN) on the frozen head. One closure gate is `FAIL` pending an operator action (signature) and several are `NOT_RUN`; see Gates.
**Authority**: NONE. This aggregate mints no PASS/READY/DONE. Nothing pushed, signed, merged or opened as a PR. Acceptance: NOT_GRANTED.
**Authorization consumed** (operator chat, 2026-11-15 and 2026-11-16): `AUTHORIZE_MACRO_DMX_DESK_GATE_001_EXECUTION=YES` (typed for the superseded package); "Reissue and execute" (base-drift reissue); "Use Codex" (review route); "Yes, repair" (repair round for F1–F3); "Grok CLI" (formal audit route).

## Custody
Worktree `/Users/hue/code/dopemux-mvp/.worktrees/desk-gate-001`, branch `feat/desk-gate-001`, base `365f70ce2edc907d14356d82d2843104dbdaa434`. The coordinator was the sole committer; children did not commit. Audited content head `79799cade6f2b73e98b5bc30889699a117fac979`; proof-only successor commits follow it.

## Children
| WS | Commit | Files | TP_ROUTE requested | Observed | Status |
|---|---|---|---|---|---|
| W01 gate client | `45c6000c6` | 2 | claude-sonnet-5-5, medium | UNKNOWN | PASS (coordinator re-run) |
| W02 hook call | `508a0418b` | 2 | claude-sonnet-5-5, medium | UNKNOWN | PASS (coordinator re-run), then advisory review FAIL |
| W01 repair (F1, F2) | `bce53a90e` | 2 | claude-sonnet-5-5, medium | UNKNOWN | PASS (coordinator re-run and red check) |
| W02 repair (F2, F3) | `79799cade` | 2 | claude-sonnet-5-5, medium | UNKNOWN | PASS (coordinator re-run and red check) |

## Deviations the operator should weigh
- **Gate for the reissue.** The `-R1` package was executed on the phrase typed for the superseded id plus the answer "Reissue and execute". No new phrase was typed for the `-R1` id. The base pin was the only change.
- **Two freezes.** The first frozen head `508a0418b` received an advisory Codex review that returned `FAIL` (two medium, one low). The operator authorised a repair; the repaired head `79799cade` was frozen and audited by the formal route. Record: `CODEX_ADVISORY_REVIEW.md`.
- **Model-call count exceeds the default L2 budget** (one implementer, one final auditor): three implementer runs (W01, W02, repair), one advisory review, one final audit. Each extra call was operator-selected or operator-authorised.
- **Supervisor error.** Finding F1 came from the coordinator's brief to the W01 child, which asked for a folder-name fallback that contradicts invariant I03. The packet text was correct.
- **Auditor had tools.** Earlier Grok audits in this repo used a tool-less recipe. This run enabled tools so the auditor could re-run the tests, against a sealed `git archive` export rather than the worktree. The worktree head and status were unchanged after the run.

## Gates
| Gate | Exit | Result |
|---|---|---|
| `ct validate-macro`, `ct validate-binding` ×3 | 0 | PASS |
| pytest, two changed test files, at `79799cade` (coordinator) | 0 | PASS, 43 passed |
| pytest, same command (auditor, sealed export) | 0 | PASS, 43 passed |
| flake8 new client and its tests | 0 | PASS |
| flake8 `native_hooks.py` | 1 | PASS: 76 = base 76, no new finding |
| black, new client and its tests | 0 | PASS |
| black, `native_hooks.py` and `tests/test_native_hooks_workflow.py` | 1 | FAIL, pre-existing at the base; not reformatted |
| `validate_change_contract.py --base 365f70ce2 --head 79799cade` | 0 | PASS, max lane L2, 4 paths |
| `validate_change_contract.py --base 365f70ce2 --head HEAD` | 0 | PASS |
| `validate_change_contract.py --proof-only` on the successor | 1 | FAIL: `proof_only_missing_signature` — `PROOF.json.sig` is absent. Signing is an operator gate and was not done. |
| `validate_audit_proof.py PROOF.json` | 0 | PASS |
| Full `pre-commit run` | | NOT_RUN: no hook is installed in the worktree, the hook cache is empty (remote hooks would be downloaded), and some hooks auto-fix files |
| `make test` (full suite) | | NOT_RUN |
| DCP route, Task Orchestrator state | | NOT_RUN |
| Live session against a real pause request | | NOT_RUN |
| `pr-steward gate --audit-proof` | | NOT_RUN (no PR) |

## Audit
Formal: `../AUDITOR_REPORT.md`, `GROK_AUDIT_PROMPT.txt`, `GROK_AUDIT_RESPONSE.txt`, `GROK_frozen.diff`. Status `PASS`, no findings, no auditor-listed risks. The residual risks in `PROOF.json` are the coordinator's, not the auditor's. Independence is by requested route (xAI vs Anthropic); observed identities are UNKNOWN. **Operator attestation (chat, 2026-11-16, "Yes, I attest both")**: auditor model `grok-4.7` and independence `PROVEN`. At the operator's instruction ("do it for me") the supervisor session ran the signing script with the operator's audit signing key; the attestation is the operator's, the keystroke was the session's.

## What this does and does not change
The code is on an unpushed local branch. Until it is merged and a session starts from a checkout that has it, nothing in dopemux-mvp calls the Dispatch desk gate. After merge the check is advisory, at session start only.

## Next step (operator)
Review the bundle, attest independence, then decide: sign `PROOF.json`, push the branch, open a draft PR. None of these has been done.
