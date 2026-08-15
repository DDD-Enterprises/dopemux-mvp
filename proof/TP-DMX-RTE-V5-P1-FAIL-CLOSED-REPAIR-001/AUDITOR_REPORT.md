# Embedded Audit Report — TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001

**Audited head**: `1c59dafd19817d7af7033245d3e1342927c38af5` (branch `tp/DMX-RTE-V5-TERMINAL-PROVENANCE-001`, parent `492208f4684f1b7660be26deda7c29161ea50070` = PR #1232 frozen content head)
**Auditor**: `claude-code-cli` / `opus` (Claude Opus 5, self-identified), invoked as an independent subagent with no memory of the implementation session. Implementer session ran on Claude Sonnet 5 (see commit trailer); supervisor ruling required a different tier for the auditor, which routed Sonnet out and Opus in.
**Route**: Tier 1 route #1 (AGY / `gemini-3.1-pro-high`) was attempted, retried once, and confirmed materially unavailable (transport-level timeout on the inference path twice, plus a hung diagnostic probe, while `agy --version` responded normally). Per supervisor ruling, fell through to Tier 1 route #3 (Claude Code CLI, Opus — Sonnet skipped for implementer-independence).
**Worktree**: isolated git worktree, detached HEAD, created fresh for this audit, verified pinned to the audited head both before invocation and by the auditor itself as its first action (`C1R_HEAD_MISMATCH` stop condition, not triggered).

## Verdict

**PASS_WITH_RISKS**

## Blocking findings

None.

## Non-blocking risks

See `PROOF.json` → `embedded_audit.findings` (F-001-MEDIUM-1, F-002-LOW-1, F-003-LOW-2) for the full structured record. Summary:

- **F-001-MEDIUM-1**: `--phase S_INT` is a pre-existing, out-of-scope, pre-gate live-execution path (confirmed identical position at the parent head, not introduced or moved by this commit). It cannot forge top-level RUN_MANIFEST/RUNNER_IDENTITY/certification evidence. The new gate-relocation comment's claim that *no* live/provider-mutating dispatch can precede the gate is an overclaim once S_INT (and a few other pre-existing, non-authoritative pre-gate writes) are counted — the comment should be corrected in a follow-up; the S_INT gap itself is deferred by design rather than reopening the just-audited head.
- **F-002-LOW-1**: The implementer's disclosed concern about `except Exception` swallowing the async/finalize gate-bypass tests was partially wrong: `test_s10_finalize_blocked_before_dispatch` is in fact mutation-sensitive (empirically proven). `test_s10_async_provider_submit_blocked_before_dispatch` is mutation-insensitive, but for a different reason than disclosed — it's intercepted by an unrelated pre-existing live-execution consent gate ~575 lines before the identity gate, not by the `except Exception` swallow. Structural source-order pinning (`test_s7`) plus five sibling mutation-sensitive tests adequately close the gap for merge purposes; a dedicated runtime proof for that one specific dispatch path remains a follow-up.
- **F-003-LOW-2**: Minor telemetry nuances in the batch-outcome fix (integrated-count semantics, reason-code precedence when multiple failure modes coexist, an incomplete `test_s7` marker tuple, and pre-existing manifest-merge behavior on reused run directories). None affect `success`/`exit_code` correctness.

## Files reviewed

- `services/repo-truth-extractor/run_extraction_v5.py` (full `main()`, `run_batch_retrieval_and_integration_detailed`, `update_run_manifest_startup_failure`)
- `services/repo-truth-extractor/lib/batch_retriever.py`
- `services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py`
- `services/repo-truth-extractor/tests/test_batch_retriever.py`
- `services/repo-truth-extractor/s_int/run_s_int.py` (read to assess F-001; not part of the diff)
- Parent-head `run_extraction_v5.py` at `492208f4` (for pre-existence checks)

## Validation evidence reviewed

All offline pytest, Python 3.12.13, in the isolated audit worktree:

| Run | Result |
|---|---|
| `pytest tests/test_rte_v5_terminal_provenance_fail_closed.py tests/test_batch_retriever.py` | 73 passed in 9.13s |
| `pytest tests/` (full suite) | 1304 passed, 1 skipped, 8 xfailed in 186.92s, exit 0 |
| Mutation probe (gate neutralized via an out-of-tree pytest plugin), `-k s10` | 5 of 7 failed as expected (gate proven load-bearing); worktree confirmed unmodified before/after |

The 1 skip requires a real `OPENROUTER_API_KEY`; the 8 xfails are pre-existing deferrals unrelated to this packet. No live-provider execution occurred at any point.

## Authority-boundary / scope concerns

Clean. `git show 1c59dafd19 --stat` confirms exactly the four allowed files (per the supervisor-amended allowlist), no v3/v4, schema, workflow, CI, or `proof/pr_merge/embedded-audit/pr-1232/**` changes. The `run_extraction_v5.py` change was confirmed to be a pure relocation of an identical 15-line gate block, not a rewrite.

## The 13 attack-list claims

See `PROOF.json` for the finding/risk record; the full per-claim confirmation table (all 13 confirmed, with the S_INT/prescan nuances noted above) is preserved verbatim in `review_bundle/AUDITOR_RAW_RESPONSE.md`.

## Declared identity

`auditor_tool: claude-code-cli`
`auditor_model: opus`
`audited_head: 1c59dafd19817d7af7033245d3e1342927c38af5`
