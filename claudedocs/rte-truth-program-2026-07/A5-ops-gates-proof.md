# A5 — RTE Ops Posture: Quality Gates, CI, Test Debt, Proof Integrity

**Program**: RTE-TRUTH audit pass A5
**Date**: 2026-07-10/11 · **HEAD**: `542c17bb4` · **Worktree**: `.claude/worktrees/focused-mahavira-5bd29b`
**Method**: static inspection only (git log, grep, file reads). No live tests run, no network calls.
**Confidence labels**: observed = read directly from code/artifacts; inferred = derived from evidence; UNKNOWN = not verified this pass.

---

## 1. xfail/skip debt ledger

Complete enumeration of every xfail/skip/skipif under `services/repo-truth-extractor/tests/` (incl. `tests/regression/`). Wave assignments use the program's R0 (hygiene/config) → R5 taxonomy; where the wave charter is ambiguous the rationale is given.

### 1.1 Cluster D — prescan/walker xfails (deferred to TP-RTE-WALKER-006)

| # | Location | Marker | Encoded defect |
|---|----------|--------|----------------|
| D1 | `tests/test_prescan_e2e_smoke.py:69` | `xfail(sys.platform == "darwin", strict=True)` | Full+incremental E2E smoke: warm incremental rerun must reuse cache (`cached_code_analysis_reused == 2`, `reanalyzed == 0`) and produce identical manifests. Reason: "prescan incremental cache semantics… outside CostProfile F repair scope." |
| D2 | `tests/test_prescan_incremental.py:490` | `xfail` (unconditional, `strict=True`) | **Incremental/full semantic parity**: after changing one file, `_normalized_outputs(incremental_out) != _normalized_outputs(full_out)`. Incremental runs produce semantically different artifacts than a full recompute — the core correctness promise of incremental mode is broken. |
| D3 | `tests/test_prescan_contracts.py:129` | `xfail` (unconditional, `strict=True`) | **Optimize-pass payload schema drift.** Test expects the optimize payload to surface prior-pass content (`duplicate_assessments`, `hidden_features`, `planned_features`, plus their values) directly. Actual builder — `GrokPassRunner._build_optimize_payload`, `lib/prescan/grok_passes.py:506-519` — nests raw prior-pass dicts under *differently named* top-level keys (`dedup_results`, `discovery_results`, `feasibility_results`) and returns a dict (which `_call_grok` then passes as message `content`, grok_passes.py:521+ — itself suspect, since OpenAI SDK content should be a string). The optimize pass therefore does not receive prior-pass summaries in the contracted shape. Observed. |
| D4–D6 | `tests/test_code_prescan_truthfulness.py:29, 72, 121` | `xfail(sys.platform == "darwin", strict=True)` ×3 | (a) dotted relative Python imports (`.models`, `..core`) must be emitted; (b) api-surface detection must not fire on comment/string mentions of fastapi/flask/click/mcp; (c) TS arrow-function symbols/signatures must be captured. |

**Underlying defect analysis for D4–D6 (and the darwin condition generally).** The behaviors these tests assert **appear implemented** in current code: `lib/prescan/code_prescan.py:215-219` handles `relative_import` nodes; `:248-272` uses line-anchored regexes (`(^|\n)\s*(from\s+fastapi\b|import\s+fastapi\b)`) that cannot match comments/strings mid-line; `:108-110`/`:327-329` include `arrow_function` in symbol/signature target types. What *is* observed is a **fail-open Tree-sitter dependency**: `code_prescan.py:6-14` wraps the tree-sitter imports in `try/except ImportError` → `TREE_SITTER_AVAILABLE = False`, and `analyze_file` (`:64-65`) silently returns `{}` when no parser exists for the language. On a machine where tree-sitter wheels are missing/unimportable (harness python 3.9 vs required mise 3.12 is a known local trap), `result["imports"]` raises and the test fails — hence the darwin-conditioned xfail. Root pyproject **does** declare `tree-sitter>=0.25.2` + grammar pins (`pyproject.toml:96-100`), so a correctly synced darwin venv would make these tests XPASS, and with `strict=True` an XPASS is a hard error. **Inferred** (import check on this machine blocked this pass — UNKNOWN whether tree-sitter imports in the current darwin venv). Either way the marker encodes an *environment* assumption, not a code defect, and is a time bomb in both directions.

- **Defect it encodes**: (i) D2/D3 = real code defects (incremental parity; optimize payload contract); (ii) D1/D4–D6 = platform-conditioned markers most plausibly masking a silent tree-sitter degradation path.
- **Fix requires**: D3 — reshape `_build_optimize_payload` to the contracted flat schema (and serialize before `_call_grok`); D2 — make incremental cache merge produce full-recompute-equivalent artifacts; D1/D4–D6 — make tree-sitter a hard (fail-closed) dependency of prescan or explicitly record degraded mode in output metadata, then drop the darwin conditions.
- **Severity**: D2 HIGH (silent wrong artifacts in incremental mode), D3 HIGH (optimize pass operating on wrong contract), D1/D4–D6 MEDIUM (env-conditional masking).
- **Owning wave**: **R2** (walker/prescan correctness — TP-RTE-WALKER-006 already exists as the named owner; keep it, schedule it in R2). The fail-open tree-sitter import is an **R0** hardening candidate (one-line fail-closed change + venv verification).

### 1.2 Regression pack `tests/regression/audit_2026_05_22/`

| Finding | Location | Marker | Status |
|---------|----------|--------|--------|
| FA-3-HIGH-1 | `test_fa_3_high_1_prompt_input_separator.py:47` (+guard `pytest.skip` :53) | `xfail` (non-strict) | **Unfixed.** 0/138 v4 prompts contain any INPUT/INSTRUCTION delimiter (`<repo_content>`, `<INSTRUCTIONS>`, etc.). Prompt-injection surface: repo content is pasted verbatim into user content; runtime-confirmed injection in prior audit (TRACE.md L178). Fix = add delimiter convention to promptset templates. **Severity HIGH (security)** → **R1**. |
| FA-4-HIGH-1 | `test_fa_4_high_1_secret_assign_regex.py` | **No xfail — FIXED** | xfail removed; `SURROUNDED_LEAKS` cases are now plain regression tests. Fix confirmed in `output_safety.py:23` — `\b` replaced with lookarounds `(?<![A-Za-z0-9_-])`, so `AWS_SECRET_ACCESS_KEY=…` redacts. Observed. Ledger entry closed; the prior audit's ":47/:58/:37/:41" list is current, FA-4 entries are historical. |
| FA-4-HIGH-2 | `test_fa_4_high_2_walker_env_variants.py` | **No xfail — FIXED** | Glob list extended: `lib/prescan/models.py:81-88` now includes `.env-*`, `.env_*`, `**/.env-*`, `**/.env_*`. Observed. Closed. |
| FA-7-MED-1 | `test_fa_7_med_1_status_no_telemetry.py:58` | `xfail` (non-strict) | **Unfixed.** `--status` (text mode) with a typo'd run-id writes `telemetry/TERMINAL_TIMELINE.jsonl` under a phantom run dir — violates `readonly_introspection`. Partial regression of P5 F4-CRIT-1: PR #603 fixed the 14 phantom phase dirs but missed the telemetry sidecar (`--status-json` is clean, positive test :40 guards that). Fix = wrap the telemetry writer in `if not readonly_introspection:`. **Severity MEDIUM** → **R2**. |
| FA-8-HIGH-1 | `test_fa_8_high_1_preflight_probe.py:37 (skipif) + :41 (xfail)` | `skipif(no OPENROUTER_API_KEY)` + `xfail` (non-strict) | **Unfixed + double-gated.** Preflight probe returns `failure_type=unknown / AMBIGUOUS_PROVIDER_BLOCK` even with valid keys while direct curl succeeds; suspected `call_llm` payload construction (max_tokens/response_format). Because it is skipped in CI (no key) AND xfailed, this test can never signal anything in CI. **Severity HIGH (blocks live go-live diagnosis)** → **R1**. |

### 1.3 Environment-guard skips

`tests/test_tp_rtx_v5_phase_recovery_hardening.py:327, 381, 397` — `pytest.skip` when `CLI_COMMAND_SURFACE.json` / `REPOCTRL_QA.json` / `HOMECTRL_QA.json` are absent from the compiled contract map. Guard-style, not debt per se, but they **silently drop coverage** if the contract map ever stops emitting those targets — a skip that should arguably be a failure (the artifacts are contracted). **Severity LOW** → **R3** (convert to hard assert or explicit marker).

### 1.4 Ledger-level finding

The three live regression xfails (FA-3, FA-7, FA-8) are **non-strict**, so when their defects get fixed the tests XPASS silently and the ledger rots — exactly what happened benignly with FA-4 (fixed, marker removed manually) will not self-report for the others. **R0 action**: add `strict=True` (or `xfail_strict = true` service-wide) to all remaining regression xfails, and adopt a rule that every xfail carries a TP reference (Cluster D does; FA-* reference audit docs only).

---

## 2. Pre-live gate posture (`services/repo-truth-extractor/validate_pre_live_gate_v25.py`, 1536 lines)

### 2.1 Evaluator inventory (observed)

Blocking (emit `Blocker`, force NO_GO): `evaluate_import_cli_smoke` (:432), `evaluate_prompt_integrity` (:454), truth-split via `collect_truth_split` (:523, `SP_CONTRACT_MISSING`/`TARGET_TRUTH_SPLIT_MISMATCH` :598-621), `evaluate_contract_map` (:639, double-compile determinism), `evaluate_route_readiness` (:692, providers + API keys), `evaluate_pytest_layer` for `critical_tests` (:1087, invoked blocking at :1430), `evaluate_smoke_tests` (:1124). Claim **confirmed**.

SKIP/WARN-by-default (emit `Condition`, never block):
- `evaluate_pal_validation` **:780** — with no `--pal-validation-file` and no `pal_validation.json`, returns `status: "SKIPPED"` (:836) + `Condition(PAL_REQUIRED_UNAVAILABLE)` (:825-832).
- `evaluate_online_preflight` **:958** — `allow_online_preflight` defaults False (flag :290-293); `:965` short-circuits to `status: "WARN"` (:976) + `Condition(ONLINE_PREFLIGHT_FAILURE)`.

Verdict path (:1490-1492): `verdict = "NO_GO"; if not active_blockers: verdict = "CONDITIONAL_GO" if condition_rows else "GO"`. Conditions are never waiver-filtered (`split_findings_by_waiver` :1173-1202 filters Blockers only). So a run that does **nothing** about PAL or online preflight still exits **CONDITIONAL_GO**. Claim **confirmed** — the gate's weakest posture is its default posture.

### 2.2 Designed flip: `--allow-conditional` opt-in

1. `build_arg_parser()` (:258-306): add `--allow-conditional` (`store_true`, default False) with help text stating that without it, skipped PAL/preflight = NO_GO.
2. `GateConfig` dataclass (:118-133): add `allow_conditional: bool = False`; wire in `build_config` (:327-344).
3. Verdict block (:1490-1492) becomes:
   ```python
   verdict = "NO_GO"
   if not active_blockers:
       if condition_rows and not config.allow_conditional:
           verdict = "NO_GO"   # un-opted-in skip is a hard stop
       elif condition_rows:
           verdict = "CONDITIONAL_GO"
       else:
           verdict = "GO"
   ```
   `config` is already in scope in `run_gate` (:1385) — no parameter threading.
4. Consistency: `derive_operator_verdict` (:1280-1296) inspects only blockers/repo-findings, so it would still say GO_NOW — either promote un-waived conditions into blocker-shaped rows before :1493, or add a `NO_GO_CONDITIONAL_NOT_ALLOWED` operator bucket alongside the existing `NO_GO_ENV`/`NO_GO_ARTIFACT_STATE` constants (:160-164).

**Severity MEDIUM-HIGH (gate integrity)** → **R1** (small diff, big honesty gain).

### 2.3 Report-writing claim — partially inaccurate (corrected)

There is **no `--output-root` flag** on this script; the flag is `--output-dir` (:261). When omitted, default is repo-tree-relative: `REPO_ROOT / "reports" / "repo-truth-extractor" / "pre_live_gate_v25" / run_id` (:317-319) — that is the real symptom behind the prior claim. When `--output-dir` IS passed, it is honored for **all seven** artifacts (`VALIDATION_SCOPE.json` :1396, `TRUTH_SPLIT_REPORT.json` :1418, `OFFLINE_GATE_RESULTS.json` :1461, `PAL_VALIDATION.json` :1470, `ONLINE_PREFLIGHT_RESULTS.json` :1476, `VALIDATION_VERDICT.json` :1514, `VALIDATION_SUMMARY.md` :1516) — no hardcoded bypass found; the only non-config write is a `TemporaryDirectory` determinism probe inside `evaluate_contract_map` (:645-648), auto-deleted. **Disposition: prior audit finding downgraded** — real issue is only the repo-tree *default*; fix is changing the default (or requiring the flag). **Severity LOW** → **R0**.

---

## 3. CI coverage

### 3.1 extractor-smoke (`.github/workflows/ci-complete.yml:227-262`, timeout 30 min)

Runs exactly 6 service test files + 1 root file (`tests/unit/test_cli_upgrades_commands.py`) via `uv run --frozen pytest … -n auto --maxfail=1 --disable-warnings --no-cov`: `test_run_extraction_v4_core.py`, `test_rte_live_cert_characterization.py`, `test_rte_v5_characterization.py`, `test_truth_run_cli.py`, `test_run_extraction_v5_promptset_truth.py`, `test_run_extraction_v5_validator.py`. Observed.

### 3.2 extractor-full (`:315-346`, timeout-minutes: 45)

Invocation (:342-346): `PYTHONPATH=src uv run --frozen pytest services/repo-truth-extractor/tests/ -n auto --dist worksteal -q --tb=short --disable-warnings --no-cov --durations=40 --durations-min=0.05`. **No `-m`/`-k` filters, no ignores** — and grep confirms zero `@pytest.mark.slow` markers exist in the suite, so **all 179 test files are genuinely collected**. Claim "runs ALL files" **confirmed**.

**Wall-time risk**: no `pytest-timeout` dependency and no per-test `--timeout`; only the 45-min job cap. Commit `cd6243721` ("ci: parallelize extractor full gate (#882)") added xdist specifically as a duration mitigation and promised follow-up "path-based conditional gating after duration evidence" — never landed. One hung test (e.g. a subprocess-spawning regression test like FA-7's 30 s-timeout `subprocess.run`, multiplied across retries) can burn the job. **Severity MEDIUM** → **R0** (add `pytest-timeout` + `--timeout=120 --timeout-method=thread` to extractor-full).

### 3.3 Root pytest.ini and the lint hole

Root `pytest.ini:11-20` `norecursedirs` includes `services` (line 15); `testpaths = tests`. This does **not** affect CI extractor jobs (explicit positional paths bypass `testpaths`/`norecursedirs`) — it only means bare `pytest` at root never touches the service. The service has **no local pytest.ini/pyproject/ruff.toml/mypy config at all**.

Bigger observed finding: **no CI job anywhere runs ruff, mypy, or flake8** (0 hits across all 16 workflow files); the only "lint" is the brand-color linter (`ci-complete.yml:208`). Root `pyproject.toml:285-297` declares a strict `[tool.mypy]` profile that nothing executes; `dev` extras carry flake8/mypy unused; `.pre-commit-config.yaml` has no code linter. The repo's declared strictness is aspirational.

### 3.4 R0 fix spec — service-local lint config + job

Add to a new `services/repo-truth-extractor/pyproject.toml` (or `ruff.toml` + mypy section):

```toml
[tool.ruff]
line-length = 88
target-version = "py311"
extend-exclude = ["__pycache__", "archive"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_return_any = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
exclude = ["tests/", "archive/"]
```

(mypy block mirrors root's declared profile.) CI: **add a new dedicated `extractor-lint` job** in `ci-complete.yml` (`ruff check services/repo-truth-extractor/ && mypy services/repo-truth-extractor/`) — there is no existing lint job to hook into. Expect a large initial violation baseline; land as warn-only first or with a baseline file, then ratchet. Repo-wide lint is a separate, larger decision — out of R0 scope. **Owning wave R0.**

---

## 4. Proof integrity

### 4.1 TP-RTE-S7-DRIFT-FIX-001 — the "verdict:FAIL" is NOT a failure (premise corrected)

`proof/TP-RTE-S7-DRIFT-FIX-001/PROOF.json` (flat path) shows `status: READY_FOR_REVIEW`, `validation_state: PASSED`, `outcome: VERIFY_AND_CLOSE`, `pytest 10/10 passed`, all 7 validations PASS. The only `"FAIL"` strings live inside `s7_gate_result.verdict` / `verify_and_close_evidence.expected_status` — they are the **expected output of the S7 drift gate when fed a deliberately injected stale step** (`FAKE_STALE_STEP` absent from the model map). The packet's job was to prove the gate correctly *rejects* drift; gate-says-FAIL-on-bad-input **is** the passing result. Commit `c8b054d43` ("test(rte): verify S7 stale drift gate closes VERIFY_AND_CLOSE", 2026-06-06) created the bundle and matches it exactly; 5 later commits were metadata touch-ups. **Honest disposition: RE-CLOSE — no reopen warranted.** The audit trigger was a naive grep for `FAIL` inside proof JSON. **Follow-up (R3)**: proof-bundle schema should namespace fixture/expected-output fields so verdict greps don't false-positive.

### 4.2 TP-RTE-GOLIVE-REMEDIATION-001/-002 — path-assumption error, work IS proven

`proof/TP-RTE-GOLIVE-REMEDIATION-001/` and `-002/` **do not exist** (the audit premise of "empty dirs" was itself wrong — nothing is there). The packets' own JSON (`task-packets/generated/TP-RTE-GOLIVE-REMEDIATION-00{1,2}.json`) declare, in `commit.allowlist` and step S4 `expected_files`, the proof path as `proof/rte-golive-remediation/TP-RTE-GOLIVE-REMEDIATION-00X/implementation-notes.md` — which exists, with Scope/Changes/Validation/NOT_RUN/Residual-Risk sections (jsonschema PASS, 49 tests passed for -001; validator suite + py_compile + pre-commit PASS for -002). Commits `d2fe66cac`, `46da5f9c9`, `ae76136a3` are all ancestors of HEAD. **Disposition: PROVEN; no gap.** The flat-dir convention assumption was the auditor's, not the packets'. **Follow-up (R3)**: standardize proof-dir layout so bundle location is derivable from TP ID.

### 4.3 Spot-checks (3 bundles)

- **TP-RTE-STRICT-ATTESTATION-007**: 12 validation commands all exit 0; expected-nonzero `rg` check correctly labeled; merged PR #616 (`843a69242`), ancestor of HEAD. **CONSISTENT.**
- **TP-RTE-BATCH-E2E-006**: contains an honest RED→GREEN trail (one exit-1 entry documented as intermediate guard failure, followed by exit-0 rerun); `f3_high_2_status: "narrowed_further"` matches residual_risks. Merged PR #615. **CONSISTENT.**
- **TP-RTE-V3-CONSENT-004**: 9 commands exit 0; findings map to behavior_before/after; 2 skipped tests disclosed (litellm absent), not concealed. Merged PR #605. **CONSISTENT.**

**Corpus-level finding (MEDIUM → R3)**: proof-bundle schema is inconsistent across the family — some bundles use `validation_state`/nested `verdict`, others bare per-command `exit_code` arrays with no aggregate verdict field. Automated verdict extraction across `proof/` is unreliable; this pass's two false alarms (4.1, 4.2) are direct consequences.

---

## 5. Runtime ops surface

### 5.1 gitignore does not cover the real output path — HIGH

Root `.gitignore` entries (:303-314 `extraction/runs/`, `extraction/repo-truth-extractor/v{3,4,5}/{runs,doctor}/`, quarantine; :366 `extraction/prescan/`; :371-376 `_audit_out/`, `extraction/v*/` etc.) are all **root-anchored** — they match `<repo>/extraction/` only. The service actually writes to `services/repo-truth-extractor/extraction/…`; `git check-ignore -v` matches **nothing** there. Result: **119 files already git-tracked** under `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/{runs,doctor}/`, including 13 timestamped `run_*/` dirs each with committed `spend_ledger.json` + `RUN_MANIFEST.json` (7.3 MB and growing per run — git-history growth, not just disk). The root-level `extraction/` tree separately holds 1,313 tracked files (~50 MB) committed *before* the ignore rules landed (gitignore never untracks). **Severity HIGH → R0**: add service-anchored ignore rules + `git rm -r --cached` sweep of run artifacts (needs a decision on which committed runs are load-bearing fixtures vs. detritus).

### 5.2 No automated retention — MEDIUM

`extraction_hygiene.py` (TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001) exists but is a **manual CLI only** — no caller anywhere in repo, policy hardcoded (its own comments admit the YAML policy files are not loaded), `apply` defaults to dry-run. No TTL/rotation/pruning anywhere else. Unbounded growth of `runs/` + `doctor/` per invocation. → **R2**: wire hygiene into runner post-run or a scheduled job; load policy from config.

### 5.3 SPEND_LEDGER.json — MEDIUM

Written per-run as lowercase `spend_ledger.json` (constant `SPEND_LEDGER_FILENAME`, `rte_config.py:43`) by `_write_spend_ledger_snapshot` (`run_extraction_v5.py:4544-4581`) → `write_json` (:3676-3692) which is a **bare `path.write_text`** — not atomic (no temp+rename), full rewrite per spend event, guarded only by a process-local `threading.Lock` (:4178, used :4890). Crash mid-write or two processes sharing a run_root can truncate the spend record — the one artifact that must survive a crash. Currently also git-tracked (5.1). → **R1** (spend truth is a go-live safety artifact): atomic write (tmp+`os.replace`), consider append-only JSONL event log alongside the snapshot.

### 5.4 Log hygiene — LOW

`run_extraction_v5.py:2279-2283` basicConfig to stdout/stderr; per-run `RUN.log` via plain `FileHandler` append (`configure_run_file_logger` :2289-2306) — no rotation anywhere in the service (RotatingFileHandler appears only in a prompt template doc). Bounded per-run in practice, unbounded across runs via 5.2. → **R2**, rides along with retention fix.

---

## Consolidated severity table

| Finding | Severity | Wave |
|---|---|---|
| gitignore misses `services/…/extraction/`; run artifacts committed | HIGH | R0 |
| Pre-live gate defaults to CONDITIONAL_GO on skipped PAL/preflight | MED-HIGH | R1 |
| FA-3-HIGH-1 prompt-injection delimiter absent (0/138 prompts) | HIGH | R1 |
| FA-8-HIGH-1 preflight probe broken + double-gated (skip∧xfail) | HIGH | R1 |
| SPEND_LEDGER non-atomic write | MEDIUM | R1 |
| Cluster D: incremental/full parity (D2), optimize payload contract (D3) | HIGH | R2 (TP-RTE-WALKER-006) |
| Cluster D: darwin-conditioned xfails masking tree-sitter fail-open | MEDIUM | R0 (fail-closed) / R2 (drop markers) |
| FA-7-MED-1 `--status` telemetry write in readonly mode | MEDIUM | R2 |
| No retention/pruning; hygiene tool unwired | MEDIUM | R2 |
| No lint/type CI anywhere; service lint config spec (§3.4) | MEDIUM | R0 |
| extractor-full lacks per-test timeout | MEDIUM | R0 |
| Non-strict regression xfails rot silently | LOW | R0 |
| Pre-live gate default output dir inside repo tree | LOW | R0 |
| Proof-bundle schema inconsistency (verdict fields) + layout convention | MEDIUM | R3 |
| Contract-map guard skips silently drop coverage | LOW | R3 |

## UNKNOWNs

- Whether tree-sitter actually imports in the current darwin venv (import check blocked this pass) — determines if Cluster D darwin xfails would XPASS-error today.
- Actual wall-time of extractor-full at HEAD (no live run performed).
- Which of the 1,313 root-level committed `extraction/` files are load-bearing fixtures vs. removable artifacts.
- FA-4 fix commits' identities (fixes verified in code; provenance not traced).
