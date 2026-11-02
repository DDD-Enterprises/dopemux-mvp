# RETURN-01 — MACRO-DMX-MEMORY-BRIDGE-001-R4 (amended v2; aggregate, authority NONE)

**Status**: `READY_FOR_AUDIT` for W01 and W02 (each committed); the single final independent audit ran once and returned `PASS_WITH_RISKS` (Q1-Q14 all PASS).
**Frozen content head (audited subject)**: `88e7b7de3a43b50b4c4cdac7fc340f21bda03e40` on `claude/memory-bridge-001-b349d8` (base `93050d135`). Proof-only commits follow it.
**Authorization**: `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R4_EXECUTION=YES`, `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R4_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`, then "redesign N3 with opus and complete fixes" (all typed by the operator; `AUTHORIZATION_AND_AMENDMENT.md`).

## Commits

| Commit | Workstream | Content |
|---|---|---|
| `60c53d7e6` | evidence | R4 issued v1 (preserved), amended v2 with the Opus N3 redesign, authorization record |
| `81a23478d` | W01 | relay of quiet earlier sessions' undelivered rows (N3), 200,000-character decision scan (N4), `foldedPending` and its dead branch removed (N6); 18 new tests |
| `88e7b7de3` | W02 | README and how-to: the relay, the scan bound, the 'Not built' row for other sessions' rows removed |
| `01ac4dc6f` | audit custody | prompt, raw Grok streams, probe, invocation, hashes (before the verdict was read) |
| (next) | closure | adjudication, `AUDITOR_REPORT.md`, unsigned `PROOF.json`, this file |

## Route and measured counters against the PROPOSED allowances

Counters from each completion notice; active time not recordable; observed model response-claimed; effort UNKNOWN.

| Role | Requested | Observed | Tokens (cap) | Tool uses (cap) | Elapsed (cap) | Attempts | advisor / Agent / git-state calls |
|---|---|---|---|---|---|---|---|
| Coordinator (N3 design, reviews, gates, commits) | claude-opus-5-5 (operator `/model`) | claude-opus-5-5 per the session | not capped | — | — | — | advisor 0 |
| W01 | claude-sonnet-5-5 | claude-sonnet-5-5 | 160,289 (500,000) | 20 (120) | 207.8 s (45 min) | 1, no retry | 0 / 0 / 0 |
| W02 | claude-haiku-5-5 | claude-haiku-5-5 | 132,201 (200,000) | 30 (60) | 141.9 s (20 min) | 1, no fallback | 0 / 0 / 0 |
| **Children total** | | | **292,490 of 1,000,000** | 50 | 349.6 s | 2 of 4 dispatches | 0 |

- Team-lead correction rounds: 0 of 1. Intermediate model audits: 0.
- Audit (outside the budget): 1 attempt, 0 retries; probe 07:56:05Z, run 07:56:21Z to 07:59:08Z (164.9 s), cost 0.0805 USD in all; model `grok-4.5` per the init event (self-reported `grok-4`).

## Gate table (coordinator, at `88e7b7de3`)

| Gate | Result |
|---|---|
| `claude plugin validate` | PASS (advisory warnings only) |
| `claude plugin test` | PASS, 123 / 0 |
| `tsc -p` strict, 2.1.309 declaration | PASS |
| Docs validators ×3; how-to 149 lines; no hash or PR number | PASS |
| `git diff --check`; change-contract preflight (L2) | PASS |
| `ct validate-macro` / `validate-binding` (v2 + 2 child bindings) | PASS |
| Grok audit (one attempt) | PASS_WITH_RISKS, Q1-Q14 PASS |
| `validate_audit_proof.py` | PASS |
| Proof-only preflight | see the closing commit (expected: only the missing signature) |
| `.venv/bin/pre-commit`; live session; real `dopemux capture emit` | NOT_RUN |

## Decisions left for the operator

1. Accept the open findings for this head (N7-N11 INFO, N12 LOW) or ask for N12 (a collision-proof file key) as one more small repair.
2. Attest independence, sign `PROOF.json` at the final head, and push so PR #1483 carries the repaired head (it is still at `bff3fd46e`). R2 and R3 proofs are superseded records for earlier heads.
3. The live smoke test: two sessions in one checkout with `.dopemux/`, complete a todo in the first and end it, wait 10 minutes, start the second, and check the status line and `chronicle.sqlite`.
