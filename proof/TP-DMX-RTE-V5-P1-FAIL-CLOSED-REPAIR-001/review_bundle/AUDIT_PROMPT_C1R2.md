# Independent embedded audit — C1R2 (focused, F-001 closure)

You are an independent auditor with no memory of the implementation session. Do not trust any
narrative you have not personally verified against the code and tests in this exact worktree.

## Precondition (verify FIRST, before anything else)

This worktree must be pinned to exactly this commit:

```
C1R2 = 8ce4866470
```

Run `git rev-parse HEAD` and `git log -1 --stat`. If the head does not match, STOP immediately
and report `C1R2_HEAD_MISMATCH` — do not proceed with any other step.

## Background

This is a narrow, focused re-audit. It is NOT a full re-audit of the whole repair. A prior
independent audit (Claude Opus, `claude-code-cli`) already reviewed the parent commit
`1c59dafd19` ("C1R") and returned `PASS_WITH_RISKS` with zero blocking findings. That audit
surfaced one accepted-as-non-blocking finding, **F-001-MEDIUM-1**: `--phase S_INT` was a
pre-existing, out-of-scope, pre-gate live-execution path that could dispatch to a provider
*before* `required_execution_source_identity()` ran, because the S_INT CLI branch dispatched and
`sys.exit()`ed entirely before main() ever reached the (then textually-later) identity gate. The
supervisor overseeing this repair rejected treating that as merely a documentation/comment issue
and required an actual code fix, since the repo's own live-operation-consent matrix classifies
S_INT phase execution as `provider-live`.

C1R2 (this commit, `8ce4866470`, parent `1c59dafd19`) is the fix for exactly that gap. Diff stat:
`git diff 1c59dafd19..8ce4866470 --stat`.

## What changed (for your own independent verification — do not just trust this list)

1. `services/repo-truth-extractor/run_extraction_v5.py`: the `--phase == "S_INT"` dispatch block
   was relocated (claimed: pure cut/paste, no logic changes) from before
   `required_execution_source_identity(root)` to after it. The gate's guarding comment was also
   edited to name S_INT explicitly instead of overclaiming completeness.
2. `services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py`: a new
   test `test_s10_s_int_blocked_before_dispatch` was added, plus an additional source-order marker
   assertion inside the existing structural guardrail test
   (`test_s7_required_execution_source_identity_gate_is_a_single_call_site`) for the S_INT branch.
3. `services/repo-truth-extractor/tests/test_s_int_runner.py`: an existing test,
   `test_run_s_int_dry_run_via_v4_cli`, was modified to give its `tmp_path` fixture a real git
   identity (git init + one commit) before invoking the v4 CLI as a subprocess. This file was
   added to the packet's allowlist by explicit supervisor amendment specifically for this reason
   — verify that the amendment's stated purpose (adapting a pre-existing test's fixture to the
   newly-enforced invariant, not weakening any assertion) actually matches what the diff does.

## Your task — attack these specific claims

For each claim below, independently verify it against the actual code (don't just read the
implementer's comments and test names — read the runtime logic and trace execution order
yourself):

1. **Gate dominance**: does `required_execution_source_identity(root)` now run before *every*
   code path that can reach `run_s_int()` or any live LLM call for `--phase S_INT`? Check both the
   `--dry-run` and non-dry-run branches inside the S_INT block. Is there any way to reach S_INT
   dispatch (directly or via `--phase ALL` / a phase sequence containing S_INT) that still
   bypasses the gate?
2. **No regression on the two original P1 repairs**: re-verify, independently, that C1R's original
   two fixes (RTE-W1-010 gate covering async/finalize/batch-watch/batch-retrieve/ordinary-phase
   dispatch, and RTE-W1-006 terminal-batch-failure accounting in
   `run_batch_retrieval_and_integration_detailed` / `lib/batch_retriever.py`) are still intact and
   unmodified in substance by this commit. `git diff 1c59dafd19..8ce4866470` should show the
   S_INT-relocation and comment edit in `run_extraction_v5.py`, the new/modified test content, and
   nothing else — confirm this yourself via the diff, don't take it on faith.
3. **The relocation is truly a pure move**: confirm the S_INT dispatch block's internal logic
   (imports, `RunnerConfig` construction, `_prompt_executor`, `run_s_int()` call, exception
   handling, output printing) is byte-for-byte identical before and after the move — i.e. this is
   a structural fix (gate ordering), not a logic rewrite that could have introduced new bugs.
4. **New test is mutation-sensitive, not just present**: `test_s10_s_int_blocked_before_dispatch`
   uses a call-recording list (`calls`) instead of relying on exit-code or exception propagation
   alone. Verify this design choice is actually necessary and correct: does the pre-existing
   `except Exception: ... sys.exit(1)` inside the S_INT branch swallow a raised
   `AssertionError` from a naive stub into the *same* exit code (1) that a correctly-gated run
   produces? If you have time, reproduce this yourself: temporarily revert just the
   `run_extraction_v5.py` relocation (put the S_INT block back before the gate — you can diff
   against `1c59dafd19` to get the exact prior text) and rerun
   `test_s10_s_int_blocked_before_dispatch` to confirm it fails on the broken code and passes on
   the fixed code. Restore the file afterward and confirm `git status` is clean before you finish.
5. **`test_s_int_runner.py` fixture fix is honest**: read `_init_minimal_git_repo` and the modified
   `test_run_s_int_dry_run_via_v4_cli`. Confirm this is a legitimate fixture repair (giving the
   subprocess a real, provable git identity so it now correctly exercises the newly-enforced gate)
   and not a hidden weakening — e.g. it must NOT special-case S_INT, disable the gate, mock
   `get_git_sha`/`required_execution_source_identity` to force success, or otherwise route around
   the invariant under test. The test's core assertions (`payload["status"] == "DRY_RUN"` and the
   machine-summary file existing) must be unchanged.
6. **Scope discipline**: confirm no files outside the supervisor-amended allowlist were touched:
   `services/repo-truth-extractor/run_extraction_v5.py`,
   `services/repo-truth-extractor/lib/batch_retriever.py` (untouched by this commit — verify),
   `services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py`,
   `services/repo-truth-extractor/tests/test_batch_retriever.py` (untouched by this commit —
   verify), `services/repo-truth-extractor/tests/test_s_int_runner.py`. Use
   `git show 8ce4866470 --stat` and `git diff 1c59dafd19..8ce4866470 --stat`.

## Validation you must run yourself (offline only — no live provider calls, no network)

- `python3 -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py services/repo-truth-extractor/tests/test_s_int_runner.py`
- `cd services/repo-truth-extractor && python3 -m pytest tests/test_rte_v5_terminal_provenance_fail_closed.py tests/test_batch_retriever.py tests/test_s_int_runner.py -q`
- `cd services/repo-truth-extractor && python3 -m pytest tests/ -q` (full suite; expect the same
  baseline as C1R's own audit: 1 skip requiring a real `OPENROUTER_API_KEY`, 8 pre-existing xfails
  unrelated to this packet — flag anything beyond that baseline as a new failure)
- The mutation probe described in claim 4 above.

Do not run anything that requires network access or a real provider API key. If you cannot get a
required tool/dependency to run, say so explicitly — do not silently skip and report PASS.

## Report format

Give a verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR, with:
- Confirmation the worktree was pinned to `8ce4866470` before you started (or the
  `C1R2_HEAD_MISMATCH` stop).
- Per-claim (1-6 above) confirmation or refutation, with evidence (file:line, command output).
- Any findings, each rated blocking or non-blocking, with a one-line rationale for the rating.
- Full validation command output (or a faithful summary with pass/fail counts) for everything you
  ran under "Validation you must run yourself".
- Explicit confirmation that you did not modify any tracked file in this worktree except during
  the claim-4 mutation probe, and that you restored it (`git status` clean) before finishing.
