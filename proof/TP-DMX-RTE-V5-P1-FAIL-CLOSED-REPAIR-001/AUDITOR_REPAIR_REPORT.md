# Embedded Audit Report — C1R2 (F-001 closure) — TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001

**Audited head**: `8ce4866470` (branch `tp/DMX-RTE-V5-TERMINAL-PROVENANCE-001`, parent `366e6fdd4f` = C1R proof-only commit, grandparent `1c59dafd19` = C1R)
**Auditor**: `claude-code-cli` / `opus` (Claude Opus, self-identified), invoked as an independent subagent with no memory of the implementation session. Implementer session ran on Claude Sonnet 5.
**Route**: Same fallback route as C1R's audit (AGY still not re-attempted per supervisor instruction — "no need to resurrect AGY"). Claude Code CLI / Opus, isolated git worktree, detached HEAD, pinned to and verified against `8ce4866470` as the auditor's first action.
**Scope**: Focused re-audit. Not a full re-audit of the whole repair — targets exactly the F-001 closure (S_INT gate relocation) plus non-regression of C1R's two original P1 repairs.
**Session note**: the audit agent's first invocation was terminated mid-run by a host session/quota limit (transient, non-route failure — "You've hit your session limit"); resumed once from its own transcript per the standing one-transient-retry rule and completed normally on resume.

## Verdict

**PASS_WITH_RISKS** (0 blocking findings, 4 non-blocking)

## Precondition

Confirmed: `git rev-parse HEAD` = `8ce48664707a89f39960a603e658c4cf5a39a30d` before any other action. No `C1R2_HEAD_MISMATCH`.

## Per-claim findings

1. **Gate dominance over S_INT** — CONFIRMED. `run_s_int` appears exactly twice in `run_extraction_v5.py` (import + call), both after the gate. `S_INT` is not a member of `PHASES`, so no `--phase ALL` sequence can reach it; the branch is reached only via the literal `args.phase == "S_INT"` guard, itself now positioned after the gate. Both dry-run and live sub-branches are inside the same relocated block. v4's CLI path is also covered (v4 subprocess-delegates into v5's gated `main()`). Noted for context: `enforce_live_operation_consent` already required `--execute` + `DPMX_LIVE_OK=1` for a *live* S_INT dispatch even pre-fix, so F-001 was a missing second (identity) layer, not an unconsented-dispatch hole — consistent with why the supervisor rated it MEDIUM rather than CRITICAL, and still correctly required a code fix given the repo's own `provider-live` classification of S_INT.
2. **No regression on C1R's two P1 repairs** — CONFIRMED, with one non-blocking ancestry correction (F-A below). `lib/batch_retriever.py` and `tests/test_batch_retriever.py` are untouched by C1R2 (0 hunks). The `test_s7` structural guardrail and the full `test_batch_retriever.py` suite pass.
3. **Relocation is a pure move** — CONFIRMED as text (byte-for-byte identical 201-line block, verified by direct Python list comparison of the old and new line ranges). One real behavioral consequence was identified and probed benign (F-B below): S_INT now runs after `resolve_run_context`/`get_run_dirs`/`write_phase_contract_map`/`UI(...)` construction and after the read-only early exits, so e.g. `--phase S_INT --status` now takes precedence, and a run-dir side effect now occurs for S_INT. Probed live in a fresh git repo: dry-run S_INT with no `--run-id` still works (exit 0, correct DRY_RUN payload).
4. **New test is mutation-sensitive, not just present** — CONFIRMED, and independently reproduced. Reverting `run_extraction_v5.py` alone to the pre-fix source and rerunning both `test_s10_s_int_blocked_before_dispatch` and `test_s7_...` fails both; both pass on the fixed source. The auditor additionally isolated the exit-code question directly: pre-fix and post-fix runs both exit `1`, but only the pre-fix run actually invoked `run_s_int` (proven via the call-recording side channel) — confirming exit-code-only assertions would have been blind to this exact bug, and the design choice in the new test was necessary, not stylistic.
5. **`test_s_int_runner.py` fixture fix is honest** — CONFIRMED. `_init_minimal_git_repo` does exactly `git init` + one commit, with `-c user.name=`/`-c user.email=` so it needs no host git config. It does not special-case S_INT, does not mock/patch the gate or `get_git_sha`, and does not set any bypass env var. The core assertions (`payload["status"] == "DRY_RUN"`, machine-summary file existence) are untouched by the diff. Corroborated by the mutation probe: this test passes on both the pre-fix and post-fix source, because it gives the subprocess a legitimately provable identity either way — the signature of a fixture repair, not a masking change.
6. **Scope discipline** — CONFIRMED. `git diff 366e6fdd4f..8ce4866470 --name-only` returns exactly the three supervisor-amended-allowlist files. `lib/batch_retriever.py` and `tests/test_batch_retriever.py` confirmed untouched by this commit.

## Non-blocking findings

- **F-A**: the audit prompt asserted C1R2's parent was `1c59dafd19`; it is actually `366e6fdd4f` (C1R's proof-only commit). This made the prompt's own suggested diff command show 5 extra (docs-only) files. Auditor caught and corrected this itself; no code impact.
- **F-B**: the S_INT relocation moves S_INT's dispatch to run after run-dir/context resolution and the read-only early exits, which is a genuine (if narrow) behavioral change beyond pure gate-ordering. Probed live and confirmed benign for the no-`--run-id` dry-run case, the highest-risk shape.
- **F-C**: the C1R2 commit message states "1308 passed"; the auditor's own full-suite run in the isolated worktree measured 1305 passed (1314 collected total including skip/xfail). Zero failures in either run — flagged only as a number that should reconcile, not a correctness issue.
- **F-D** (out of scope for this packet, flagged for supervisor awareness): `run_extraction_v3.py` contains the same S_INT dispatch block and does not call `required_execution_source_identity` at all. v3 is not reachable from the v4 CLI wrapper (which targets v5) and carries its own separate live-consent gate (`--execute` + `DPMX_LIVE_OK=1`, added in a prior PR), so live v3 S_INT is still consent-gated, just not identity-gated. Same genus of gap as F-001 was. Recommend a supervisor ruling: either a follow-up packet extending the identity gate to v3, or an explicit acceptance that v3's consent gate is the controlling mitigation there.

## Validation evidence (all offline, no network, no live provider calls)

| Run | Result |
|---|---|
| `python3 -m py_compile` (3 changed files) | PASS |
| `pytest tests/test_rte_v5_terminal_provenance_fail_closed.py tests/test_batch_retriever.py tests/test_s_int_runner.py -q` | 76 passed in 10.84s |
| `pytest tests/ -q` (full suite, isolated worktree) | 1305 passed, 1 skipped, 8 xfailed in 226.08s, exit 0 |
| Mutation probe (S_INT gate relocation reverted) | `test_s10_s_int_blocked_before_dispatch` and `test_s7_...` both fail on pre-fix source, both pass on post-fix source |

Baseline matches C1R's own audit exactly: the 1 skip requires a real `OPENROUTER_API_KEY` (correctly skipped, no live call made); all 8 xfails are pre-existing, unrelated deferrals. Zero new failures beyond that baseline.

## Worktree integrity

Exactly one tracked file was modified once, solely for the claim-4 mutation probe (`run_extraction_v5.py`, reverted via `git checkout 366e6fdd4f --` and restored via `git checkout 8ce4866470 --`). All probe scripts/logs were written outside the worktree. Final state: `git rev-parse HEAD` = `8ce48664707a89f39960a603e658c4cf5a39a30d`, `git status --porcelain -uall` empty.

## Declared identity

`auditor_tool: claude-code-cli`
`auditor_model: opus`
`audited_head: 8ce48664707a89f39960a603e658c4cf5a39a30d`
