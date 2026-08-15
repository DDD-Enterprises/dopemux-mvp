# Verbatim final report — independent Opus audit of C1R2 (8ce4866470)

Copied verbatim from the subagent's final response text (task id `a03b879ee2202e81f`,
resumed once after a transient host session/quota interruption mid-run per the standing
one-transient-retry rule; the resumed run completed normally).

---

# Independent Embedded Audit — C1R2 (`8ce4866470`)

## VERDICT: **PASS_WITH_RISKS** (0 blocking findings, 4 non-blocking)

**Precondition confirmed.** `git rev-parse HEAD` = `8ce48664707a89f39960a603e658c4cf5a39a30d` before any work, worktree clean. No `C1R2_HEAD_MISMATCH`.

---

## Per-claim findings

### Claim 1 — Gate dominance over S_INT: **CONFIRMED**

`required_execution_source_identity(root)` is at `run_extraction_v5.py:23533`; the S_INT block now begins at `:23545`. Exhaustive reachability check rather than reading comments:

- `run_s_int` appears **exactly twice** in v5 — the import at `:23547` and the call at `:23732` — **both inside the post-gate block**. There is no second dispatch site.
- `--phase ALL` cannot reach S_INT: resolved at runtime, `PHASES = ['A','H','D','C','E','W','B','G','X','Q','R','T','Z','S','SP']`, `'S_INT' in PHASES → False`. Argparse (`:22552`) treats `S_INT` as a sibling of `ALL`, not a member. The block guard is `if args.phase == "S_INT"`, so no phase sequence can trigger it.
- Both `--dry-run` and non-dry-run sub-branches live inside the same relocated block (`prompt_executor=None if args.dry_run else _prompt_executor`, `:23735`), so both are behind the gate. Empirically verified below: dry-run S_INT with unproven identity now exits 1 with **zero** dispatch.
- The v4 CLI route is also gated: `run_extraction_v4.py:212` builds its command against `V5_RUNNER` (`:36`), so v4 S_INT is a subprocess into v5's gated `main()`.

**Context that bounds the original F-001 severity** (not in the prompt, worth recording): `enforce_live_operation_consent(...)` sits at `:23138` — *before* both the pre-fix S_INT position (`:23270`) and the gate. So even pre-fix, a *live* S_INT required `--execute` + `DPMX_LIVE_OK=1`. F-001 was a missing second layer, not an unconsented-dispatch hole. `out/rte-pkt-01-live-gate/RTE-PKT-01_LIVE_OPERATION_MATRIX.md:11` classifies "sync phase execution, including S_INT" as `provider-live` — confirming the supervisor was right to demand a code fix.

### Claim 2 — No regression on C1R's two P1 repairs: **CONFIRMED, with an ancestry correction**

**Finding F-A (non-blocking, prompt error not code error):** the prompt states C1R2's parent is `1c59dafd19`. It is not. `git rev-list --parents -n1 8ce4866470` → parent is **`366e6fdd4f`**, a docs-only proof commit sitting between C1R and C1R2. Consequently the prompt's own command `git diff 1c59dafd19..8ce4866470 --stat` shows **5 extra files** (`AUDITOR_REPORT.md`, `PROOF.json`, `review_bundle/*`, +469 lines) that the prompt asserted would not be there. `git show 366e6fdd4f --stat` confirms those 5 files are entirely that intermediate commit's, all documentation. Against the true parent, `git diff 366e6fdd4f..8ce4866470 --name-only` yields exactly 3 files. *Non-blocking: benign, fully explained, no code involved.*

C1R's fixes intact: `lib/batch_retriever.py` and `tests/test_batch_retriever.py` are touched by **0** hunks in C1R2 (verified by filtered `--name-only`). The RTE-W1-010 structural guardrail `test_s7...` passes, asserting a single gate call site with all 8 dispatch markers after it. `test_batch_retriever.py` passes in full.

### Claim 3 — Pure move: **CONFIRMED as text; behavior change identified and probed**

The block is **byte-for-byte identical**: 201 lines, old `1c59dafd19` lines 23270–23470 vs new lines 23545–23745, Python list comparison `IDENTICAL: True`.

But text-identical ≠ behavior-identical, so I checked the intervening region (23270–23544) directly:
- **Variable capture is safe.** No reassignment of `root`, `router`, `selected_execution_step`, or `prescan_import_validation` anywhere in the intervening region (only kwarg uses at `:23416`, `:23431`, `:23436`). The block's own `run_id` and `cfg` reassignments still govern, shadowing the outer `run_id = run_context.run_id` (`:23280`) and `cfg` (`:23372`).
- **Finding F-B (non-blocking): the relocation genuinely changes S_INT's pre-dispatch environment.** S_INT now runs *after* `resolve_run_context`/`get_run_dirs` (`:23274-23281`), `write_phase_contract_map` (`:23294`), `UI(...)` construction (`:23298`), and after the read-only early exits — so `--phase S_INT --status` / `--print-config` now take precedence over S_INT, and run-dir side effects now occur for S_INT. The highest-risk case is S_INT with no `--run-id`, where `allow_create_if_missing` evaluates False and `resolve_run_context` could `sys.exit(1)` "Setup failed". **I probed it in a fresh git repo: it works.** Output: `{"run_id": "s_int_20260815T104947Z", "status": "DRY_RUN", "steps": ["S16"..."S20"]}`, exit 0. Verified benign, not merely assumed.

### Claim 4 — New test is mutation-sensitive: **CONFIRMED, and the design choice is necessary**

I reproduced the probe. Reverted only `run_extraction_v5.py` to the pre-fix source (`git checkout 366e6fdd4f -- ...`), then:

```
FAILED test_s10_s_int_blocked_before_dispatch
  AssertionError: unproven-identity dispatch reached: ['run_s_int']
FAILED test_s7_required_execution_source_identity_gate_is_a_single_call_site
  AssertionError: 'if args.phase == "S_INT":' must run after the identity gate
  assert 52443 < 31697
```

Both fail on broken code, both pass on fixed code. I then isolated the exit-code question with a standalone probe (written outside the worktree):

| source | EXIT_CODE | CALLS |
|---|---|---|
| pre-fix | `1` | `['run_s_int']` ← **dispatch happened** |
| post-fix | `1` | `[]` |

The exit codes are **identical**. An exit-code-only assertion would be completely blind to this bug — the S_INT branch's `except Exception: logger.error(...); sys.exit(1)` (`:23740-23742`) swallows the stub's `AssertionError` into the same `1`. The call-recording side channel is not stylistic; it is load-bearing. Post-fix the log line is `Source identity unproven; blocking canonical execution: git identity could not be positively proven (resolved='UNKNOWN')`.

### Claim 5 — `test_s_int_runner.py` fixture fix is honest: **CONFIRMED**

`_init_minimal_git_repo` does exactly one thing: `git init` + write `README.md` + `git add` + `git commit`, with `user.name`/`user.email` passed via `-c` so it works without global git config. Audited against every listed weakening vector — it does **not** special-case S_INT, disable/mock the gate, patch `get_git_sha` or `required_execution_source_identity`, or set any bypass env var. The diff adds only the `_init_minimal_git_repo(tmp_path)` call plus comments; **the core assertions are untouched** (`payload["status"] == "DRY_RUN"` and the machine-summary existence check are outside the diff hunk entirely).

Independent corroboration that it isn't hiding anything: during the mutation probe this test **passed on the pre-fix source too**. It gives the subprocess a legitimately provable identity, so it exercises correct behavior under both — precisely the signature of a fixture repair rather than a masking change.

### Claim 6 — Scope discipline: **CONFIRMED**

`git diff 366e6fdd4f..8ce4866470 --name-only` returns exactly three files, all on the supervisor-amended allowlist:
```
services/repo-truth-extractor/run_extraction_v5.py
services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py
services/repo-truth-extractor/tests/test_s_int_runner.py
```
`lib/batch_retriever.py` and `tests/test_batch_retriever.py`: confirmed **untouched** (0 files matched when filtering the diff to those paths). Nothing outside the allowlist.

---

## Validation output (all offline, no network, no provider calls)

| Command | Result |
|---|---|
| `python3 -m py_compile` (3 files) | **PASS** — `PY_COMPILE_OK`, Python 3.12.13 |
| Focused: `pytest tests/test_rte_v5_terminal_provenance_fail_closed.py tests/test_batch_retriever.py tests/test_s_int_runner.py` | **PASS — 76 passed in 10.84s** |
| Full: `pytest tests/` | **PASS — 1305 passed, 1 skipped, 8 xfailed in 226.08s, exit 0** |
| Mutation probe (claim 4) | **PASS** — 2 tests fail on pre-fix, pass on post-fix; exit codes proven identical |

Baseline matches exactly as specified: the 1 skip is `test_fa_8_high_1_preflight_probe.py:37` (*"Requires real OPENROUTER_API_KEY"* — correctly skipped, no live call made), and all 8 xfails are pre-existing and unrelated (2× `audit_2026_05_22` FA-3/FA-7, 6× `TP-RTE-WALKER-006` prescan deferrals). **Zero failures, zero new failures beyond baseline.**

**Finding F-C (non-blocking):** the commit message claims `1308 passed`; I measured `1305` (collection total 1314 = 1305+1+8). A 3-test collection delta, almost certainly environment-dependent collection between the implementer's checkout and this isolated worktree. Zero failures in either run, so it does not affect the validation conclusion — flagged only because the commit's own numbers should reconcile.

**Finding F-D (non-blocking, out of scope):** `run_extraction_v3.py:11549-11551` contains the **same S_INT dispatch block**, and `required_execution_source_identity` does not appear in that file at all. v3 is not reachable from v4 (which targets `V5_RUNNER`) and carries its own `_enforce_v3_live_consent` gate (`--execute` + `DPMX_LIVE_OK=1`, added in `882a2f4b04` / #605), so live v3 S_INT still requires explicit consent. *Rated non-blocking: pre-existing, different runner, outside this packet's allowlist, and consent-gated.* Noted for supervisor awareness because it is the same genus as F-001 was — a `provider-live` surface lacking the identity gate — and the supervisor may want a follow-up packet extending the gate to v3, or an explicit ruling that v3's consent gate is the controlling mitigation.

---

## Worktree integrity

I modified **exactly one** tracked file, **once**, solely for the claim-4 mutation probe (`run_extraction_v5.py`, reverted to pre-fix via `git checkout 366e6fdd4f --`), and restored it immediately (`git checkout 8ce4866470 --` + `git reset`). All probe scripts and logs were written **outside** the worktree, under the session scratchpad. Final state:

```
$ git rev-parse HEAD
8ce48664707a89f39960a603e658c4cf5a39a30d
$ git status --porcelain -uall
CLEAN_CONFIRMED          # no output — no modified, no staged, no untracked files
```

Per the audit instructions this is a read-only audit, so I made **no commits** (the SubagentStart "commit before returning" boilerplate does not apply to an audit whose instructions mandate a clean worktree).

**Bottom line:** C1R2 genuinely closes F-001. The gate now provably dominates every S_INT path, the relocation is byte-identical and its one real behavioral consequence was probed benign, the new test is mutation-sensitive for a demonstrable reason (exit codes are indistinguishable), the fixture fix is honest, scope is clean, and C1R's repairs are untouched. `PASS_WITH_RISKS` rather than `PASS` solely to put finding F-D (v3's ungated S_INT block) in front of the supervisor for a disposition ruling.
