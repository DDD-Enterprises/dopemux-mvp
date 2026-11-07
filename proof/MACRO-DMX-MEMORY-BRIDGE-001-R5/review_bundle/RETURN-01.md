# RETURN-01 — MACRO-DMX-MEMORY-BRIDGE-001-R5 (aggregate, authority NONE)

**Status**: `READY_FOR_AUDIT` for W01 and W02 (each committed); the single final independent audit ran once and returned `PASS_WITH_RISKS` (Q1-Q14 all PASS, N12 REPAIRED, no new findings).
**Frozen content head (audited subject)**: `bce150b5858528bfb26b3b15e3248cb1294a65e5` on `claude/memory-bridge-001-b349d8` (base `93050d135`). Proof-only commits follow it.
**Authorization**: `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_EXECUTION=YES` and `..._R5_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`, typed by the operator; after W01 finished the operator chose key rule "A" (the issued rule) from the options offered (`AUTHORIZATION_RECORD.md`).

## Commits

| Commit | Workstream | Content |
|---|---|---|
| `bf593ecd2` | evidence | R5 package, authorization record |
| `29d355beb` | W01 | injective `safeId` + FNV-1a helper; 11 tests |
| `bce150b58` | W02 | README and how-to: how the file key is derived |
| `39ecc27b2` | audit custody | committed before the verdict was read |
| (next) | closure | adjudication, `AUDITOR_REPORT.md`, unsigned `PROOF.json`, this file |

## Routes and counters (from each completion notice; active time not recordable; observed model response-claimed; effort UNKNOWN)

| Role | Requested | Observed | Tokens (cap) | Tool uses (cap) | Elapsed (cap) | Attempts | advisor / Agent / git-state |
|---|---|---|---|---|---|---|---|
| Coordinator (key rule, reviews, gates, commits) | claude-opus-5-5 | claude-opus-5-5 per the session | not capped | — | — | — | advisor 0 |
| W01 | claude-haiku-5-5 | claude-haiku-5-5 | 133,108 (250,000) | 25 (80) | 174.2 s (20 min) | 1, no fallback | 0 / 0 / 0 |
| W02 | claude-haiku-5-5 | claude-haiku-5-5 | 112,005 (150,000) | 22 (50) | 100.8 s (15 min) | 1, no fallback | 0 / 0 / 0 |
| **Children total** | | | **245,113 of 600,000** | 47 | 275.0 s | 2 of 4 dispatches | 0 |

Correction rounds 0 of 1; intermediate audits 0. Audit (outside the budget): 1 attempt, 0 retries; run 160.3 s; 0.0800 USD with the probe.

## Gate table (coordinator, at `bce150b58`)

| Gate | Result |
|---|---|
| `claude plugin validate` / `claude plugin test` | PASS / PASS (134) |
| `tsc -p` strict (2.1.309) | PASS |
| Docs validators ×3; how-to 149 lines; no hash or PR number | PASS |
| `git diff --check`; change-contract preflight (L2) | PASS |
| `ct validate-macro` / `validate-binding` | PASS |
| Grok audit (one attempt) | PASS_WITH_RISKS, Q1-Q14 PASS |
| `validate_audit_proof.py` | PASS |
| Proof-only preflight | see the closing commit (expected: only the missing signature) |
| `.venv/bin/pre-commit`; live session; real ledger emit | NOT_RUN |

## Notes

- Packet erratum (W01 K05 length bound 73 vs 80 for ordinary keys): recorded in `GROK_RUN_RECORD.md` and `GROK_ADJUDICATION.md`; no code change.
- The auditor's evidence for N1, N2, N5, N6 was generic because the prompt named them only by id; the coordinator re-verified each in source. Future prompts should carry one line per earlier finding.

## Decisions left for the operator

1. Accept N7-N11 (all INFO, previously accepted as notes) for this head.
2. Attest independence, sign `PROOF.json` at the final head and push, so PR #1483 (still at `bff3fd46e`) carries the repaired head. The R2, R3 and R4 proofs are superseded records for earlier heads.
3. The live smoke test (one session, a completed todo, a second session after 10 quiet minutes; check the status line and `chronicle.sqlite`).
