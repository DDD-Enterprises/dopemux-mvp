# RETURN-01 — MACRO-DMX-MEMORY-BRIDGE-001-R3 (aggregate, authority NONE)

**Status**: `READY_FOR_AUDIT` for W01 and W02 (each committed); the single final independent audit ran once and returned `PASS_WITH_RISKS`.
**Frozen content head (audited subject)**: `c71e7c1f436349f477037d28ce479218c63a53a4` on `claude/memory-bridge-001-b349d8` (base `93050d135ffc2592000c1d0edef82b2912935525`). Proof-only commits follow it.
**Authorization**: `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R3_EXECUTION=YES` and `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R3_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`, both typed by the operator in chat (`AUTHORIZATION_RECORD.md`).

## Commits

| Commit | Workstream | Files |
|---|---|---|
| `1d9b08ced` | evidence | flat proof copy of the R3 package and authorization record |
| `be4cfb654` | W01 (N2) | `register.tsx`, `register.test.ts` (1 line each) |
| `c71e7c1f4` | W02 (N1, N5) | `docs/02-how-to/memory-bridge.md`, `plugins/dopemux-memory-bridge/README.md` |
| `4988d5ee0` | audit custody | prompt, raw Grok streams, probe, invocation, hashes (committed before the verdict was read) |
| (next) | closure | `GROK_ADJUDICATION.md`, `AUDITOR_REPORT.md`, `PROOF.json` (unsigned), this file |

## Route and measured counters against the PROPOSED allowances

Counters are from each completion notice. Active (model-working) time is not recordable: UNKNOWN. "Observed" is the model named in each child's API responses (response-claimed, not provider-attested); effort UNKNOWN; no runtime receipt.

| WS | Requested | Observed | Tokens (cap) | Tool uses (cap) | Elapsed (cap) | Attempts | advisor / Agent / git-state calls (transcript) |
|---|---|---|---|---|---|---|---|
| W01 | claude-haiku-5-5 | claude-haiku-5-5 | 90,907 (200,000) | 8 (60) | 31.7 s (20 min) | 1, no fallback | 0 / 0 / 0 |
| W02 | claude-haiku-5-5 | claude-haiku-5-5 | 97,384 (200,000) | 12 (60) | 33.2 s (20 min) | 1, no fallback | 0 / 0 / 0 |
| **Total** | | | **188,291 of 500,000** | 20 | 64.9 s of child time | 2 of 4 dispatches | 0 |

- Team-lead correction rounds used: 0 of 1. Intermediate model audits: 0. Coordinator advisor calls during execution: 0. The Sonnet fallback was not needed.
- Audit (outside the budget): 1 attempt, 0 retries, no fallback. Probe 2026-10-30T07:21:30Z, run 07:21:44Z to 07:25:01Z (195.7 s), cost 0.0780 USD in all as reported by the streams. Model `grok-4.5` per the CLI init event; the auditor self-reported `grok-4.7`.

## Gate table (run by the coordinator at `c71e7c1f4`)

| Gate | Result |
|---|---|
| `claude plugin validate plugins/dopemux-memory-bridge` | PASS, exit 0 (advisory warnings only) |
| `claude plugin test plugins/dopemux-memory-bridge` | PASS, 105 pass / 0 fail |
| `tsc -p` strict, Claude Code 2.1.309 declaration | PASS, exit 0 (see deviations) |
| Docs gates (`docs_frontmatter_guard.py`, `docs_prohibited_patterns.sh`, `docs_validator.py`) | PASS ×3; how-to 147 lines |
| grep for commit hashes and PR numbers in the how-to and README | PASS: none |
| Repair diff vs `52855fb35` | PASS: 4 files, 5 insertions, 7 deletions, exactly the intended lines |
| `git diff --check origin/main..HEAD` | PASS |
| `validate_change_contract.py --base origin/main --head HEAD` | PASS (L2) |
| `ct validate-macro`, `ct validate-binding` (R3 coordinator + 2 child bindings) | PASS |
| Independent audit (Grok, one attempt) | PASS_WITH_RISKS; Q1-Q13 all PASS |
| `validate_audit_proof.py` on `PROOF.json` | PASS (see the closing commit for the proof-only preflight) |
| `.venv/bin/pre-commit` | NOT_RUN: no `.venv` or `pre-commit` here |
| Live session, real `dopemux capture emit`, any service | NOT_RUN |
| DCP route, Task Orchestrator state | NOT_RUN |

## Deviations recorded

- The `tsc` gate used the Claude Code 2.1.309 declaration (sha256 `c1ae9e374c7b541111f35e6a65a152878aeb01a05a859e2e55c3638f6de70723`): the 2.1.304 file named in the packets disappeared when the session restarted. The pre-repair head passed with it as well.
- The scratchpad was wiped by the restart; the audit recipe files were re-read from the first audit's committed custody copies and hash-checked.
- The worktree holds unrelated changes by other sessions (`.codex/config.toml`, `.agents/`), excluded from every commit.

## Remaining uncertainty and the decisions left for the operator

1. Nothing has run live; `$.process` on the desktop surface, the Pulse band order and `$.fs.write` atomicity are UNKNOWN.
2. N3, N4, N6 (and N7) are unrepaired by decision; your 2026-10-24 acceptance covers the predecessor head, so they are listed OPEN here until you accept them for this head. New N8 (INFO) is a design note.
3. PR #1483 (draft) still carries `bff3fd46e`. To use the repair you need to re-attest and re-sign `PROOF.json` at the final proof head and push. I did none of that. Merge-train caveat: see your note on strict up-to-date versus signed proofs.
4. Optionally repair N3, N4, N6 as another small successor (they are code changes; N3 needs a one-line design choice).
