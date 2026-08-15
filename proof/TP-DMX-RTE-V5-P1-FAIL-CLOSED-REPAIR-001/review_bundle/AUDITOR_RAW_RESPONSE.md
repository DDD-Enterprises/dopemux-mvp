# Raw Auditor Response — Claude Code CLI / Opus

Verbatim final message returned by the independent Opus subagent (Agent tool, `subagent_type=general-purpose`, `model=opus`, `isolation=worktree`), audited head `1c59dafd19817d7af7033245d3e1342927c38af5`. Copied exactly as returned, no edits.

---

Audit complete. Worktree remains clean (`git status --short` empty; no files edited).

---

# Embedded Audit — TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001

## Model / tier self-identification

Best effort: I am running as **Claude Opus 5 (1M-context variant)**, model id `claude-opus-5[1m]`, via the Claude Code CLI as an independent subagent. This is a different tier from the implementer session (Claude Sonnet 5, per the commit's `Co-Authored-By` trailer), satisfying the not-same-model-auditing-its-own-work requirement. I did not see the implementer's conversation; all findings below were re-derived from the files and git history in the pinned worktree.

**Precondition check — PASS.** `git rev-parse HEAD` = `1c59dafd19817d7af7033245d3e1342927c38af5`, `git status --short` empty at start and at end. Parent commit verified as exactly `492208f4684f1b7660be26deda7c29161ea50070` (PR #1232 frozen content head). No `C1R_HEAD_MISMATCH`.

## Verdict

**PASS_WITH_RISKS**

Both claimed P1 repairs are real, correctly implemented, and load-bearing (proven by mutation experiment, not just by reading). The risks below are pre-existing or test-quality issues, none of which reopen either audited P1.

## Blocking findings

**None.**

## Non-blocking risks

### R1 (highest) — residual pre-gate live-execution path: `--phase S_INT`, plus an overbroad correctness claim in the added comment

`run_extraction_v5.py:23270` handles `--phase S_INT` and terminates at `sys.exit(0)` / `sys.exit(1)` (lines 23465-23470) — **entirely before the relocated gate at 23733**. This branch is not inert: it constructs a live `_prompt_executor` and calls `call_llm_with_ladder(phase="S_INT", ...)` (line 23421), and `s_int/run_s_int.py` persists per-step JSON payloads, a `machine_summary` with `"status": "OK"`, and compiled reports via `compile_s_int_reports`. So a live-provider phase that writes durable phase artifacts still runs with `UNKNOWN`/unproven source identity.

Two important qualifiers, in the repair's favor:
- **This is pre-existing.** I confirmed against `492208f4:services/repo-truth-extractor/run_extraction_v5.py` that the S_INT block and the read-only introspection block sit at identical lines. This commit did not touch or create the S_INT path, and it was named in neither original P1 finding. It is not a regression.
- **S_INT does not write the canonical provenance triple.** It exits before `write_run_manifest` / `write_runner_identity` / `write_confidence_ramp_artifacts`, so it cannot forge RUN_MANIFEST.json or RUNNER_IDENTITY.json. The blast radius is S_INT-local artifacts, not top-level certification evidence.

What *is* attributable to this commit is a truthfulness defect in the new code comment at 23721-23728, which states that "no live/provider-mutating dispatch ... may run before this gate" and enumerates the pre-gate exits as consisting *only* of `print-*`, `doctor_auth`, `preflight_providers`, `print_promptpack`, `coverage_report`/`verify_phase_output`, and `doctor`. That enumeration is incomplete and the universal claim is false (see item 8 below for the full list). The commit message repeats it. Under truth-over-fluency this should be corrected even though the underlying gap is deferred. The `test_s7` structural guardrail also cannot catch it, since `run_s_int` is absent from its marker tuple.

Recommendation (follow-up packet, not this merge): either relocate the gate above the S_INT block or add a second call site inside it. This is genuinely not a one-liner — the S_INT block builds its own `run_id` and `RunnerConfig` before `resolve_run_context`/`get_run_dirs` run at 23474, so `update_run_manifest_startup_failure(dirs["root"], ...)` has no `dirs` available at that point. Deferral is defensible; the inaccurate comment is not.

### R2 — item A (disclosed): the async-submit gate test is a false green, and the disclosed *mechanism* is wrong

I tested this empirically rather than reasoning about it, using an audit-only pytest plugin held **outside** the worktree that neutralizes `required_execution_source_identity` to a no-op, simulating the pre-repair bug. Under that mutation, of the 7 `s10` tests: **5 failed, 2 passed.**

- Mutation-sensitive (correctly detect a bypassed gate): `test_s10_ordinary_phase_execution_blocked_before_dispatch`, **`test_s10_finalize_blocked_before_dispatch`**, `test_s10_batch_watch_blocked_before_dispatch`, `test_s10_batch_retrieve_blocked_before_dispatch`, `test_s10_manifest_and_runner_identity_files_are_never_written`.
- Mutation-insensitive: **`test_s10_async_provider_submit_blocked_before_dispatch`** only.
- `test_s10_read_only_print_config_is_unaffected_by_unproven_identity` also passed, correctly — it is a gate-independent preservation test.

So the disclosure was wrong in two directions. It over-reported on **finalize**, which is in fact mutation-sensitive: the `run_integrated_prescan_stage` / `write_run_manifest` stubs fire first at 23757/23822 and are *not* wrapped in `except Exception`, so their `AssertionError` propagates out of `main()` and breaks `pytest.raises(SystemExit)`. Concern A does not apply to that test.

And it mis-identified the mechanism for **async**. It is not the `except Exception: sys.exit(1)` at 23979 swallowing the stub's `AssertionError`. Running that test under mutation with logging on shows it exits 1 at `run_extraction_v5.py:23158` — `enforce_pre_live_validator_for_execution`, an unrelated pre-existing fail-closed gate at line 23150, i.e. ~575 lines *before* the identity gate:

```
ERROR extract_runner:run_extraction_v5.py:23158 Pre-live validator blocked live execution (verdict=NO_GO).
RuntimeError: Live LLM call blocked in test context provider=gemini model=gemini-3-flash-preview.
```

This is slightly worse than disclosed: the test never reaches the identity gate at all, so it asserts nothing about it — its `assert exit_code == 1` is satisfied by a different mechanism entirely.

Is the gap closed in combination? **Partially, and adequately for merge.** `test_s7` does pin `n = run_phase_R_async_submit(` as strictly after the gate index in `inspect.getsource(runner.main)`, and source-order dominance is the actual invariant at issue for a single-call-site gate in straight-line code. Combined with the five mutation-sensitive siblings proving the gate is live, a reviewer has real evidence. But the s10 async test should not be cited as independent runtime proof. Hardening suggestion for follow-up: have the async stub raise a `BaseException` subclass (uncatchable by `except Exception`) **and** set `--prescan-skip`/env so the pre-live validator does not preempt, or assert on the written manifest's `failure_reason == "source_identity_unproven"` rather than on the exit code.

### R3 — item B (disclosed): the startup-failure manifest record is correctly shaped

- **(a) Matches the pre-existing pattern — confirmed.** The gate calls the same `update_run_manifest_startup_failure` (defined at 7192) used by `cost_cap_setup_failed` (24158) and `launch_provider_preflight_failed` (24168). No new function, no new shape.
- **(b) Not mistakable for a completed run — confirmed.** The function writes only `run_status: "FAILED"`, `phase_status: "startup_failed"`, `failure_reason`, `failure_message`, `updated_at`. No `phases`, no `prompt_set_integrity`, no certification claim. `test_s10_manifest_and_runner_identity_files_are_never_written` asserts this against real files on disk and additionally proves `RUNNER_IDENTITY.json` is never created (there is no failure-record variant of it) — and that test is mutation-sensitive, so it is genuine evidence.

One pre-existing nuance worth recording: the function *merges* into an existing `RUN_MANIFEST.json` rather than replacing it (7200-7204). If a run directory is reused (`--run-id` / `--resume`) after a prior successful run, stale `phases`/`prompt_set_integrity` keys would survive under an overlaid `run_status: "FAILED"`. `run_status: FAILED` still dominates for any correct consumer, and this behavior is shared with the two pre-existing callers, so it is not introduced here. Non-blocking; worth a follow-up note.

### R4 — minor accounting and pinning observations
- A provider-failure batch still increments `outcome.integrated` (its `batch.failed` webhook event genuinely was integrated). Semantically defensible — `integrated` counts webhook events, not successful batches — but a downstream consumer reading `integrated` alone without `terminal_failure_batches` could misread it. `success=False`/`exit_code=1` prevent any laundering, so this is presentation only.
- Reason-code precedence at 24625-24630: `elif outcome.retrieved < outcome.attempted` (`retrieval_failed`) is evaluated *before* the `terminal_failure_batches` branch, so a run with both a retrieval failure and a provider terminal-failure batch emits only `retrieval_failed`. Verdict is unaffected; telemetry fidelity is slightly lossy.
- `test_s7`'s marker tuple omits `write_confidence_ramp_artifacts` despite the docstring citing it. The write at 23832 is in fact after the gate, but that ordering is not structurally pinned against future edits.

## Files reviewed

- `/private/tmp/claude-501/-Users-hue-code-dopemux-mvp/896aa81d-fc50-4c5e-aaf6-5f1b5fd747eb/scratchpad/agy-audit-c1r-1c59dafd/services/repo-truth-extractor/run_extraction_v5.py` (full `main()`, 22499-24367; `run_batch_retrieval_and_integration_detailed`, 24463-24649; `update_run_manifest_startup_failure`, 7192-7210)
- `.../services/repo-truth-extractor/lib/batch_retriever.py`
- `.../services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py`
- `.../services/repo-truth-extractor/tests/test_batch_retriever.py`
- `.../services/repo-truth-extractor/s_int/run_s_int.py` (read to assess R1; not part of the diff)
- `492208f4:services/repo-truth-extractor/run_extraction_v5.py` (parent, for pre-existence checks)

## Validation evidence reviewed

All offline pytest. No live-provider execution; `run_extraction_v5.py` was never invoked against real providers. Python 3.12.13.

| Run | Result |
|---|---|
| `pytest tests/test_rte_v5_terminal_provenance_fail_closed.py tests/test_batch_retriever.py` | **73 passed in 9.13s** |
| `pytest tests/ -p no:randomly` (full suite) | **1304 passed, 1 skipped, 8 xfailed in 186.92s**, exit 0 |
| Mutation probe (gate neutralized, plugin outside worktree), `-k s10` | **5 failed, 2 passed** — gate proven load-bearing; with the gate neutralized the run logs `PHASE_DONE phase=A status=PASS`, i.e. phase A actually executes |

The 1 skip requires a real `OPENROUTER_API_KEY`; the 8 xfails are pre-existing deferrals to TP-RTE-WALKER-006 and the 2026-05-22 audit series, unrelated to this packet. Zero `FAILED` lines in the full suite.

Mutation-probe artifacts live at `/private/tmp/.../scratchpad/mut/plugin_neutralize_gate.py`, outside the audited worktree. The worktree was never modified: `git status --short` returned empty both before and after all test execution.

## Authority-boundary / scope concerns

**Clean.** `git show 1c59dafd19 --stat` reports exactly four files, all within the allowed set:

```
services/repo-truth-extractor/lib/batch_retriever.py                       |  16 +-
services/repo-truth-extractor/run_extraction_v5.py                         |  64 +-
services/repo-truth-extractor/tests/test_batch_retriever.py                |  26 +
services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py | 339 +-
4 files changed, 410 insertions(+), 35 deletions(-)
```

No v3/v4 runners, no schemas, no workflows, no `.github/**`, no `proof/pr_merge/embedded-audit/pr-1232/**`, no CLI routing changes beyond the two in-scope dispatch fixes. The `run_extraction_v5.py` change is a pure relocation: the identical 15-line gate block was deleted from its old position before `runners = {` and re-inserted after the persist=False `--doctor` exit — I diffed the two hunks and they are textually identical apart from the expanded comment. Commit is authored on branch `tp/DMX-RTE-V5-TERMINAL-PROVENANCE-001` directly atop the frozen head, no unrelated commits interleaved.

## The 13 claims, one by one

| # | Claim | Verdict |
|---|---|---|
| 1 | Identity gate dominates every canonical evidence write | **CONFIRMED, with a caveat on the comment's wider claim.** Gate at 23733. First `write_run_manifest` at 23822, `write_runner_identity` at 23827, `write_confidence_ramp_artifacts` at 23832 and 23942 — all strictly after, in straight-line code with no `goto`-equivalent. No earlier call site of any of the three exists anywhere in `main()`. Caveat: the *broader* claim in the added comment ("no live/provider-mutating dispatch may run before this gate") is false — see R1/S_INT. The narrow claim about canonical evidence writes holds. |
| 2 | Gate dominates Stage-0 online prescan | **CONFIRMED — and the implementer's independent discovery is real, and stronger than they described.** `run_integrated_prescan_stage(root, dirs["root"], cfg)` is at 23757, 24 lines after the gate, single call site in `main()`. Contrary to the framing in the task, it is **not** conditioned on `--prescan-online`/`--allow-online-llm`; it runs whenever `not cfg.prescan_skip` (23756), i.e. on essentially every execution. At the parent head it sat ~400 lines before the old gate position, so this was a genuine second bypass that neither original P1 finding named. Credit where due: this is a correct find, correctly ordered. |
| 3 | Gate dominates async submit | **CONFIRMED.** `run_phase_R_async_submit` at 23964, inside `if args.async_provider == "openai" and not args.finalize:` at 23962. Structurally after the gate. (Runtime test evidence for this one specific path is weak — see R2.) |
| 4 | Gate dominates finalize | **CONFIRMED.** `run_phase_R_finalize` at 23986 under `if args.finalize:` at 23984. Independently proven at runtime by the mutation probe. |
| 5 | Gate dominates batch watch | **CONFIRMED.** `run_batch_watch` at 24011 under `if args.batch_watch:` at 24006. Mutation-sensitive at runtime. |
| 6 | Gate dominates batch retrieval | **CONFIRMED.** `run_batch_retrieval_and_integration_detailed` at 24049 under `if args.batch_retrieve:` at 24041. Mutation-sensitive at runtime. Note this call is *not* wrapped in `try/except`, which is why its test is genuinely mutation-sensitive. |
| 7 | `runners = {...}` unreachable without passing the gate | **CONFIRMED.** Dispatch dict at 24176, gate at 23733; `test_s7` pins `gate_idx < runners_dict_idx`, and the mutation probe empirically executed phase A (`PHASE_DONE phase=A status=PASS`) only once the gate was neutralized. |
| 8 | Read-only/introspection modes remain usable; enumerate every pre-gate early exit | **CONFIRMED for the named modes; enumeration reveals four unlisted non-read-only branches.** All eight named modes exit before 23733 and stay usable: `--print-config` 23675, `--print-run-order` 23678, `--print-phase-routing` 23681, `--print-phase-prompts` 23684/23696, `--doctor-auth` (persist=False) 23697, `--preflight-providers` 23699-23705, `--print-promptpack` 23706, `--coverage-report` (persist=False) 23709, `--verify-phase-output` 23712, `--doctor` (persist=False) 23717. Also legitimately read-only: `--print-routing-guide` 23003, `--print-prescan-guide` 23005, `--list-phases` 23007, `--status`/`--status-json` 23554, `--tail-run-log` 23556, `--show-provider-usage` 23567. All `sys.exit(1)` setup-failure branches (23095, 23101, 23122, 23128, 23159, 23486) are fail-closed error exits with no writes or dispatch — legitimate. **Not purely read-only, all pre-gate:** (i) `--phase S_INT` 23270->23470, live LLM + artifact writes (R1, material); (ii) `--promptgen-scan` 23510->23535, writes `PROMPTGEN_INPUTS`/fingerprint JSON and a failure marker into the run dir (local scan, no provider); (iii) `write_phase_contract_map(dirs["root"], run_id)` ~23487, unconditional artifact write when not print-only/read-only; (iv) `--gemini-list-models` 23552, a live provider API call (read-only listing, passed `dirs`). All four pre-exist at 492208f4. Only (i) is materially concerning. |
| 9 | Terminal-failure status cannot yield `exit_code=0`/`success=True` even with clean webhook integration | **CONFIRMED.** At 24580 the status is lowercased/stripped and tested against `TERMINAL_FAILURE_STATES` = `{failed, expired, cancelled, canceled, timeout}`, incrementing `terminal_failure_batches_total` **before and independently of** the integration `try`. That total is assigned to `outcome.terminal_failure_batches` at 24605 and folded into the material-failure predicate at 24619 (`or outcome.terminal_failure_batches > 0`), which unconditionally sets `success=False`/`exit_code=1`. The success branches are all in the `elif`/`else` chain below, so they are unreachable when the counter is nonzero. The laundering path is closed. |
| 10 | Webhook-event integration is not suppressed for a failed batch | **CONFIRMED.** The new check is a bare counter increment with no `continue`, no `break`, no conditional guard around the subsequent block. `integrate_batch_results_with_webhook_detailed` is still called unconditionally for every terminal batch at 24582. The `batch.failed` event is still recorded; only the outcome-level determination changed. This is the right shape — evidence preserved, verdict corrected. |
| 11 | Fully-successful terminal sets still produce `success=True`/`exit_code=0` | **CONFIRMED.** For `completed`/`succeeded`/`done` with no failures: `failed = (attempted-retrieved) + integration_failed = 0`, `unmapped = max(0, len(terminal_ids) - accounted_for) = 0`, `terminal_failure_batches = 0`. Predicate at 24619 is false; `terminal != 0`; `integrated_total > 0` so the `idempotent_replay_only` branch is skipped; falls to `else` -> `fully_integrated`, `success=True`, `exit_code=0`. No happy-path regression. Covered by passing tests in `test_batch_retriever.py`. |
| 12 | Nonterminal / zero-terminal-work retrieval still classifies `no_terminal_batches_yet`/`success=True` | **CONFIRMED.** Empty `terminal_ids` => loop body never executes => all three counters 0, `unmapped = max(0, 0-0) = 0`. Predicate at 24619 false, `elif outcome.terminal == 0` at 24634 fires -> `no_terminal_batches_yet`, `success=True`, `exit_code=0`. Invariant 17 preserved. |
| 13 | `terminal_failure_batches` not double-counted against `failed`/`unmapped` | **CONFIRMED.** `outcome.failed` is incremented in exactly two places -- `+= attempted - retrieved` (24556, retrieval-layer) and `+= integration_failed_total` (24604, integration-layer). `outcome.unmapped` is assigned once (24607) as `max(0, len(terminal_ids) - accounted_for)` where `accounted_for = integrated + idempotent + integration_failed`. `terminal_failure_batches` is assigned once (24605) from a counter incremented in a disjoint code path. A batch that retrieves cleanly, reports `failed`, and integrates cleanly contributes: `failed` +0, `unmapped` +0 (it is counted in `accounted_for` via `integrated`), `terminal_failure_batches` +1. No single provider-failure batch inflates more than one counter. No double-subtraction: `unmapped` is floored at 0 and `terminal_failure_batches` is not subtracted from `accounted_for`. Totals remain internally consistent. See R4 for the `integrated`-semantics and reason-code-precedence nuances, neither of which affects the verdict. |

---

`auditor_tool: claude-code-cli`
`auditor_model: opus`
`audited_head: 1c59dafd19817d7af7033245d3e1342927c38af5`
