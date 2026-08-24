# A7 — Legacy Reference Graph (RTE-TRUTH program)

**Pass**: A7 (mechanical reference-tracing; no assessment)
**Date**: 2026-07-11
**Worktree**: `/Users/hue/code/dopemux-mvp/.claude/worktrees/focused-mahavira-5bd29b` (branch `claude/rte-audit-improvement-f4beb7`)
**Method**: `rg -n` over the entire worktree (default VCS-ignore rules apply; `.git/` and nested `.worktrees/` excluded). Each hit classified by path, precedence: `.github/` → CI; `extraction/ proof/ proof_bundle/ out/ task-packets/` → ARTIFACTS; path containing `tests?/`, `test_*`, `*_test.*`, `conftest.py` → TESTS; `*.md`/`*.mdx` → DOCS; `scripts/` or `tools/` path segment → SCRIPTS; `src/` or `services/` → RUNTIME; everything else (claudedocs/, audit_inputs/, reports/, config, json, etc.) → OTHER (listed for completeness; not part of the six requested categories). Content lines truncated at 240 chars.

## Count summary

| # | Target | RUNTIME | TESTS | CI | DOCS | SCRIPTS | ARTIFACTS | (OTHER) |
|---|--------|--------:|------:|---:|-----:|--------:|----------:|--------:|
| 1 | run_extraction_v3.py | 10 | 80 | 0 | 108 | 11 | 132 | 503 |
| 2 | run_extraction_v4.py (external refs only) | 7 | 19 | 0 | 103 | 0 | 76 | 53 |
| 3 | run_extraction.py (bare) | 21* | 6 | 0 | 81 | 0 | 10 | 31 |
| 4 | run_repscan.py (repscan) | 11 | 13 | 0 | 24 | 0 | 108 | 33 |
| 5 | run_prescan.py (run_prescan) | 5 | 2 | 0 | 28 | 0 | 22 | 19 |
| 6 | prompts/ legacy subdirs | 6 | 19 | 0 | 62 | 20 | 56 | 134 |
| 7 | base_prompts/ | 2 | 0 | 0 | 3 | 0 | 0 | 5 |
| 8 | archive/legacy_prompts + legacy_artifact_gates | 0 | 1 | 0 | 8 | 0 | 0 | 7 |
| 9 | PipelineRunner (extractor/upgrades runner.py) | 7 | 0 | 0 | 31 | 0 | 15 | 4 |

*Target 3 caveat (mechanical observation, not assessment): the bare pattern `run_extraction(?!_v\d)` also matches same-named functions/methods defined in unrelated modules (`src/dopemux/ux/wizard/extraction.py`, `src/dopemux/extraction/pipeline_orchestrator.py`, `services/dopemux-gpt-researcher/*/chatlog_extractor.py`, `extraction_pipeline.py`, `src/dopemux_github_specialist/*`). Restricting to the exact filename string `run_extraction.py`: 0 hits in RUNTIME/TESTS/CI/SCRIPTS outside the file itself; exact-filename hits occur only in `docs/archive/pipeline-v2/`, `reports/work-recovery/`, `proof/`, `claudedocs/`, and `docs/05-audit-reports/`.

Search patterns per target are recorded at the top of each section below.

---

## services/repo-truth-extractor/run_extraction_v3.py

Pattern: `run_extraction_v3|pipeline[-_]version.*v3|--pipeline-version v3`

### RUNTIME (10)
src/dopemux/commands/extractor_commands.py:473 — if pipeline_version == "v3":
src/dopemux/commands/extractor_commands.py:474 — return base / "run_extraction_v3.py"
src/dopemux/commands/extractor_commands.py:477 — f"{pipeline_version!r}. Expected one of: v5, v4, v3."
src/dopemux/cli.py:4999 — # hidden --engine-version flag or --pipeline-version v3. Keep it working but warn
src/dopemux/cli.py:5004 — "shadow engine and v5 is canonical. Prefer --pipeline-version v5. v3 remains "
services/repo-truth-extractor/run_repscan.py:5 — This wrapper keeps `run_extraction_v3.py` unchanged and layers:
services/repo-truth-extractor/run_repscan.py:72 — DEFAULT_LEGACY_RUNNER = SERVICE_DIR / "run_extraction_v3.py"
services/repo-truth-extractor/run_repscan.py:305 — parser = argparse.ArgumentParser("RepoScan promptgen wrapper for run_extraction_v3.py")
services/repo-truth-extractor/run_probe.py:45 — runner_path = (repo_root / "services" / "repo-truth-extractor" / "run_extraction_v3.py").resolve()
services/repo-truth-extractor/run_probe.py:48 — spec = importlib.util.spec_from_file_location("run_extraction_v3_probe", runner_path)

### TESTS (80)
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/tests/TEST_AND_CI_EVIDENCE.md:2725 — tests/unit/test_run_extraction_v3_phase_m.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/tests/TEST_AND_CI_EVIDENCE.md:2726 — tests/unit/test_run_extraction_v3_pipeline_controls.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/tests/TEST_AND_CI_EVIDENCE.md:2727 — tests/unit/test_run_extraction_v3_processpool_stability.py
scripts/test_batch_integration.py:73 — sys.executable, "services/repo-truth-extractor/run_extraction_v3.py",
test_batch_integration.py:72 — sys.executable, "services/repo-truth-extractor/run_extraction_v3.py",
services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:13 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:14 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:14 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:15 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:378 — script = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:12 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:13 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
tests/unit/test_extractor_schema_repair.py:16 — / "run_extraction_v3.py"
tests/unit/test_extractor_schema_repair.py:18 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
services/repo-truth-extractor/tests/test_phase_s_prompt_registry.py:13 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_phase_s_prompt_registry.py:14 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:9 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:10 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
tests/extractor/test_extractor_routing_ladders.py:8 — RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
tests/extractor/test_extractor_routing_ladders.py:9 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
tests/extractor/conftest.py:2 — # These tests import run_extraction_v3.py directly from services/,
services/repo-truth-extractor/tests/test_rte_v5_characterization.py:55 — assert extractor_commands._extractor_runner_path(repo_root, "v3").name == "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_rte_v5_characterization.py:180 — return ["python", "run_extraction_v3.py", "--phase", str(kwargs["phase"])]
services/repo-truth-extractor/tests/test_rte_v5_characterization.py:240 — monkeypatch.setattr(runner, "build_v3_cmd", lambda **kwargs: ["python", "run_extraction_v3.py"])
tests/unit/test_extractor_key_hygiene.py:17 — / "run_extraction_v3.py"
tests/unit/test_extractor_key_hygiene.py:19 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
tests/unit/test_run_extraction_v3_processpool_stability.py:20 — RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
tests/unit/test_run_extraction_v3_processpool_stability.py:21 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
tests/unit/test_run_extraction_v3_phase_m.py:10 — RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
tests/unit/test_run_extraction_v3_phase_m.py:11 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
tests/integration/test_batch_integration.py:42 — [sys.executable, str(SERVICE_DIR / "run_extraction_v3.py"), "--help"],
services/repo-truth-extractor/tests/test_hygiene_version_path.py:64 — runner_path=Path("services/repo-truth-extractor/run_extraction_v3.py"),
services/repo-truth-extractor/tests/test_phase_d_pressure_caps.py:76 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_d_caps_parse")
services/repo-truth-extractor/tests/test_phase_d_pressure_caps.py:92 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_d_caps_sort")
services/repo-truth-extractor/tests/test_phase_d_pressure_caps.py:110 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_d_caps_scope")
services/repo-truth-extractor/tests/test_phase_d_pressure_caps.py:127 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_d_caps_meta")
services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:11 — RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:12 — FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "run_extraction_v3"
services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:16 — spec = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
tests/unit/test_cli_upgrades_commands.py:115 — assert kwargs["pipeline_version"] == "v3"
services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:10 — RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
tests/unit/test_run_extraction_v3_pipeline_controls.py:8 — RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
tests/unit/test_run_extraction_v3_pipeline_controls.py:9 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
services/repo-truth-extractor/tests/test_phase_s_step_selection.py:15 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_phase_s_step_selection.py:16 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_phase_s_step_selection.py:180 — script = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:14 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:15 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:12 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:13 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_phase_execution_step_filter.py:28 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_step_filter")
services/repo-truth-extractor/tests/test_phase_execution_step_filter.py:34 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_step_filter_invalid")
services/repo-truth-extractor/tests/test_phase_execution_step_filter.py:47 — runner = _load_module("run_extraction_v5.py", "run_extraction_v3_run_phase_d")
services/repo-truth-extractor/tests/test_phase_d_contract_hardening.py:17 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_phase_d_contract_hardening.py:18 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:12 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:13 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_truth_run_cli.py:108 — def test_unknown_pipeline_version_does_not_fall_back_to_v3(self):
services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py:11 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py:12 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:10 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:11 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
tests/unit/test_extractor_gemini_thinking_config.py:16 — / "run_extraction_v3.py"
tests/unit/test_extractor_gemini_thinking_config.py:18 — SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
tests/unit/test_extractor_runner_resolution.py:21 — assert runner.name == "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_live_llm_guard.py:52 — ("run_extraction_v3.py", "run_extraction_v3_live_guard"),
services/repo-truth-extractor/tests/test_live_llm_guard.py:72 — ("run_extraction_v3.py", "run_extraction_v3_live_guard_allow"),
services/repo-truth-extractor/tests/test_live_llm_guard.py:92 — ("run_extraction_v3.py", "run_extraction_v3_live_guard_call"),
services/repo-truth-extractor/tests/test_phase_d_line_range.py:9 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_phase_d_line_range.py:10 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:184 — rc = runner.call_v3_runner(["python", "run_extraction_v3.py"], prompt_root=prompt_root)
services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:11 — RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:15 — spec = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:14 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:15 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:9 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:10 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:12 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:13 — spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:11 — return root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"

### CI (0)
(none)

### DOCS (108)
claudedocs/rte-cost-profile-plan-b-design-2026-06-04.md:91 — Shipped: strict-cell profile values corrected to OpenAI-only (catalog says anthropic-via-OpenRouter is NOT `supports_json_schema_strict`, and the 57 CE/AGG steps require strict primary — user confirmed keeping strict cells OpenAI-only); str …[truncated]
claudedocs/rte-truth-program-2026-07/A6-fresh-eyes.md:39 — - **`13f0db81a`** — adds a regression test guarding v3/v5 cell-model drift (documents that `run_extraction_v3.py` hardcodes value-default cell models and shares `model_map.yaml` directly, no cost-profile mechanism — i.e. v3 is intentionally …[truncated]
claudedocs/rte-truth-program-2026-07/A6-fresh-eyes.md:49 — | `run_extraction_v3.py` is a second, cost-profile-unaware legacy routing path, still live and diverging from v5 by design | LOW–MEDIUM (architecture debt) | deferred — not admitted to this program |
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:32 — 1. `src/dopemux/commands/extractor_commands.py:474` → `return base / "run_extraction_v3.py"` — the operator CLI itself can resolve to v3.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:33 — 2. `scripts/reprocess_failed_partitions.py:17` → `RUNNER_SCRIPT = Path(".../run_extraction_v3.py")` — an operator script hardcoded to v3.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:37 — This is now a material finding. The operator CLI (`extractor_commands.py:467-478`) is a **multi-version dispatcher** that accepts `pipeline_version` of v5/v4/v3 and resolves to the corresponding runner via subprocess. So v3 *is* operator-re …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:43 — Key clarification: the `extractor` command group's `run` (line 282) is **disabled** (raises ClickException at line 291) — it does NOT reach `_run_extractor_runner`. And `status` (line 323) disables the legacy `--pipeline-version` alias (lin …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:48 — - BUT: `_resolved_pipeline_version` (cli.py:4926) lets a hidden `--engine-version` legacy flag (cli.py:4910, `default=None`) **override** the v5 default. And most `rte` subcommands pass `effective_version` (not hardcoded v5) to `_run_extrac …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:567 — - evidence: observed. Repo-wide `rg -rn '"CLEAR"' --glob '*.py'` (excluding tests) returns only the emit sites in `reporting.py` and the legacy `run_extraction_v3.py`; no `== "CLEAR"` / `.get(...) == "CLEAR"` consumer exists. Inferred (low) …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:771 — - evidence: observed. Repo-wide grep for `repo-truth-extractor/archive`, `legacy_artifact_gates`, and `R_REQUIRED_ARTIFACT_GROUPS` returns **no** runtime reference to these files: the `R_REQUIRED_ARTIFACT_GROUPS` symbol is defined fresh in  …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:772 — - why it matters: pure workspace clutter — these 40 inert files are dead weight, not an execution or contract hazard. They do **not** block go-live. The genuine "legacy script pollution" risk (a still-live `run_extraction_v3.py` with its ow …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:786 — | S8-006 | OBS | `archive/` (40 inert files) is unreferenced dead clutter; the real live-legacy risk (`run_extraction_v3.py --execute`) is outside this stage. |
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1456 — 1. **v3 is a live-capable but legacy/shadow engine**: it has its own `--execute` flag (gated by `DPMX_LIVE_OK`, observed `run_extraction_v3.py:11247-11251`) and its own `RUNNER_SCRIPT = Path(__file__).resolve()` (v3:159). README still docum …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1479 — **Shadow / legacy:** `run_extraction_v3.py` (12,106 lines, identical docstring to v5 → v5 is its fork). Has its own live `--execute` path gated by `DPMX_LIVE_OK` (v3:11247-11251) and its own `RUNNER_SCRIPT=__file__` (v3:159). In non-test ru …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:267 — **`run_extraction_v5.py`** is the single canonical engine. Own `main()` (v5:21502), own `OperatorArgumentParser` (v5:1829); **no delegation** to v3/v4 (grep: zero `run_extraction_v3/v4` imports). Pinned as authority by `rte_config.py:126` ( …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:274 — - **`run_extraction_v3.py`** = independent legacy engine, **consent-gated** (`--execute` + `DPMX_LIVE_OK=1`, v3:11225-11234). "Legacy but still imported" — live non-test consumers exist: `run_probe.py`, `run_repscan.py`, `tools/phase0_seria …[truncated]
claudedocs/rte-distributed-audit-2026-05-29.md:68 — - **[S1-V3REACH] HIGH** (embedded) — v3 (the consent-gated legacy engine) is **operator-reachable**, not just helper-imported: `src/dopemux/commands/extractor_commands.py:474` resolves to `run_extraction_v3.py`, `scripts/reprocess_failed_pa …[truncated]
claudedocs/rte-distributed-audit-2026-05-29.md:84 — - **[CLI-V3] HIGH** (overlaps S1-V3REACH) — the multi-version dispatcher exposes live v3 via `--engine-version`/`--pipeline-version v3`.
UPGRADES/FULL_PIPELINE_OVERVIEW.md:19 — - The v3 runner (`UPGRADES/run_extraction_v3.py`) fails closed when duplicate StepIDs are found.
UPGRADES/PIPELINE_PROOF.md:14 — > Scope note: This runbook applies only to `UPGRADES/run_extraction_v3.py`. It does not define v5 launch authority. In v5, shared doctor artifacts under `extraction/doctor/` are diagnostic only, and launch/certification authority use run-sc …[truncated]
UPGRADES/PIPELINE_PROOF.md:20 — python UPGRADES/run_extraction_v3.py --preflight-providers
UPGRADES/PIPELINE_PROOF.md:21 — python UPGRADES/run_extraction_v3.py --doctor-auth --gemini-transport openai_compat_http --gemini-auth-mode auto
UPGRADES/PIPELINE_PROOF.md:22 — python UPGRADES/run_extraction_v3.py --phase A --resume
UPGRADES/PIPELINE_PROOF.md:23 — python UPGRADES/run_extraction_v3.py --phase H --resume
UPGRADES/PIPELINE_PROOF.md:24 — python UPGRADES/run_extraction_v3.py --phase D --resume
UPGRADES/PIPELINE_PROOF.md:25 — python UPGRADES/run_extraction_v3.py --phase C --resume
UPGRADES/PIPELINE_PROOF.md:26 — python UPGRADES/run_extraction_v3.py --phase R --dry-run
UPGRADES/PIPELINE_PROOF.md:27 — python UPGRADES/run_extraction_v3.py --coverage-report --phase R
UPGRADES/PIPELINE_PROOF.md:39 — These are enforced by `R_REQUIRED_ARTIFACT_GROUPS` in `UPGRADES/run_extraction_v3.py`.
UPGRADES/RUN_ORDER.md:14 — > Scope note: This runbook applies only to `UPGRADES/run_extraction_v3.py`. It does not define v5 launch authority. In v5, shared doctor artifacts under `extraction/doctor/` are diagnostic only, and launch/certification authority use run-sc …[truncated]
UPGRADES/RUN_ORDER.md:16 — This runbook is authoritative for `UPGRADES/run_extraction_v3.py`.
UPGRADES/RUN_ORDER.md:31 — python UPGRADES/run_extraction_v3.py --preflight-providers
UPGRADES/RUN_ORDER.md:32 — python UPGRADES/run_extraction_v3.py --doctor-auth --gemini-transport openai_compat_http --gemini-auth-mode auto
UPGRADES/RUN_ORDER.md:41 — python UPGRADES/run_extraction_v3.py --phase A --resume
UPGRADES/RUN_ORDER.md:42 — python UPGRADES/run_extraction_v3.py --phase H --resume
UPGRADES/RUN_ORDER.md:43 — python UPGRADES/run_extraction_v3.py --phase D --resume
UPGRADES/RUN_ORDER.md:44 — python UPGRADES/run_extraction_v3.py --phase C --resume
UPGRADES/RUN_ORDER.md:45 — python UPGRADES/run_extraction_v3.py --phase E --resume
UPGRADES/RUN_ORDER.md:46 — python UPGRADES/run_extraction_v3.py --phase W --resume
UPGRADES/RUN_ORDER.md:47 — python UPGRADES/run_extraction_v3.py --phase B --resume
UPGRADES/RUN_ORDER.md:48 — python UPGRADES/run_extraction_v3.py --phase G --resume
UPGRADES/RUN_ORDER.md:49 — python UPGRADES/run_extraction_v3.py --phase Q --resume
UPGRADES/RUN_ORDER.md:50 — python UPGRADES/run_extraction_v3.py --phase R --resume
UPGRADES/RUN_ORDER.md:51 — python UPGRADES/run_extraction_v3.py --phase X --resume
UPGRADES/RUN_ORDER.md:52 — python UPGRADES/run_extraction_v3.py --phase T --resume
UPGRADES/RUN_ORDER.md:53 — python UPGRADES/run_extraction_v3.py --phase Z --resume
UPGRADES/RUN_ORDER.md:60 — Artifact payload parsing in `UPGRADES/run_extraction_v3.py` is deterministic and fail-closed:
UPGRADES/RUN_ORDER.md:91 — Before Phase R runs, A/H/D/C must provide all required normalized artifacts declared in `R_REQUIRED_ARTIFACT_GROUPS` in `UPGRADES/run_extraction_v3.py`.
UPGRADES/RUN_ORDER.md:96 — python UPGRADES/run_extraction_v3.py --coverage-report --phase ALL
services/repo-truth-extractor/README.md:15 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/README.md:72 — - `services/repo-truth-extractor/run_extraction_v3.py`
services/repo-truth-extractor/README.md:79 — python services/repo-truth-extractor/run_extraction_v3.py --print-run-order
services/repo-truth-extractor/README.md:80 — python services/repo-truth-extractor/run_extraction_v3.py --print-phase-routing --phase Q --dry-run
services/repo-truth-extractor/README.md:81 — python services/repo-truth-extractor/run_extraction_v3.py --print-phase-prompts ALL
services/repo-truth-extractor/README.md:82 — python services/repo-truth-extractor/run_extraction_v3.py --tail-run-log --run-id <RUN_ID> --phase C --step C0 --tail-lines 100
services/repo-truth-extractor/README.md:83 — python services/repo-truth-extractor/run_extraction_v3.py --show-provider-usage --run-id <RUN_ID>
services/repo-truth-extractor/README.md:86 — python services/repo-truth-extractor/run_extraction_v3.py --phase D --batch-mode --batch-submit-only --run-id <RUN_ID>
services/repo-truth-extractor/README.md:87 — python services/repo-truth-extractor/run_extraction_v3.py --phase D --batch-watch --run-id <RUN_ID>
docs/05-audit-reports/rte-production-certification-audit-20260414.md:54 — | `services/repo-truth-extractor/run_extraction_v3.py` | `legacy compatibility runtime` | Still present and still referenced by docs and compatibility flows. |
docs/05-audit-reports/rte-production-certification-audit-20260414.md:300 — - `python -m py_compile src/dopemux/cli.py src/dopemux/commands/extract_commands.py src/dopemux/commands/extractor_commands.py src/dopemux/commands/extractor_validation.py src/dopemux/commands/extractor_validation_ui.py src/dopemux/extracto …[truncated]
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A99__A_P0001.TRACE.md:282 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A8__A_P0001.TRACE.md:207 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A9__A_P0001.TRACE.md:206 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A5__A_P0001.TRACE.md:255 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A13__A_P0001.TRACE.md:155 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A0__A_P0001.TRACE.md:188 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A4__A_P0001.TRACE.md:209 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A12__A_P0001.TRACE.md:146 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A1__A_P0001.TRACE.md:196 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A7__A_P0001.TRACE.md:211 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A11__A_P0001.TRACE.md:147 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A2__A_P0001.TRACE.md:208 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A6__A_P0001.TRACE.md:214 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A10__A_P0001.TRACE.md:166 — - services/repo-truth-extractor/run_extraction_v3.py
services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/golden_cost_preview_1/A_repo_control_plane/raw/A3__A_P0001.TRACE.md:204 — - services/repo-truth-extractor/run_extraction_v3.py
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:75 — `services/repo-truth-extractor/run_extraction_v3.py`
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:146 — Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.
reports/INTELLIGENCE_REPORT_FORMAT.md:432 — **Partition creation:** `run_extraction_v5.py`, `run_extraction_v3.py`
reports/work-recovery/2026-03-26/salvage-classification.md:40 — - `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-26/salvage-classification.md:58 — - `services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py`
reports/work-recovery/2026-03-26/salvage-classification.md:60 — - `services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py`
reports/git_cleanup_audit_2026-02-21.md:49 — - `python -m py_compile services/repo-truth-extractor/run_extraction_v3.py src/dopemux/cli.py` -> pass
reports/git_cleanup_audit_2026-02-21.md:53 — - fixed prompt root + parse retry scope/escalation handling in `services/repo-truth-extractor/run_extraction_v3.py`
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:363 — - Retire `run_extraction_v3.py` — Remove 12K lines; redirect any remaining references
docs/archive/claudedocs/audit-2026-05-22/hygiene-sweep-report.md:56 — | `services/repo-truth-extractor/run_extraction_v3.py` + v3 test suite (~804 KB) | medium | **KEEP** | v3 is gated (PR #605) but still alive; deleting destroys the F1-CRIT-1/2 closure surface. Audit F2a will review the gate. Deprecation bel …[truncated]
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:45 — - v3 remains available via `--pipeline-version v3`.
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-3.md:16 — - services/repo-truth-extractor/run_extraction_v3.py
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-3.md:47 — - `services/repo-truth-extractor/run_extraction_v3.py`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:45 — - v3 remains available via `--pipeline-version v3`.
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-2.md:16 — - services/repo-truth-extractor/run_extraction_v3.py
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-2.md:47 — - `services/repo-truth-extractor/run_extraction_v3.py`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:45 — - v3 remains available via `--pipeline-version v3`.
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace.md:16 — - services/repo-truth-extractor/run_extraction_v3.py
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace.md:47 — - `services/repo-truth-extractor/run_extraction_v3.py`
docs/02-how-to/extraction/repo-truth-extractor-user-guide.md:182 — DPMX_LIVE_OK=1 dopemux rte run --pipeline-version v3 --phase ALL --execute --run-id rte_v3_fallback_001
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:118 — DPMX_LIVE_OK=1 dopemux rte run --pipeline-version v3 --phase ALL --run-id rte_v3_legacy_001 --execute
docs/03-reference/extraction/pipeline-transport-layer.md:16 — `/Users/hue/code/dopemux-mvp/UPGRADES/run_extraction_v3.py`.
docs/03-reference/extraction/pipeline-transport-layer-2.md:16 — `/Users/hue/code/dopemux-mvp/UPGRADES/run_extraction_v3.py`.
docs/03-reference/extraction/transport-options.md:13 — - services/repo-truth-extractor/run_extraction_v3.py
docs/03-reference/extraction/transport-options.md:22 — - runner: `python services/repo-truth-extractor/run_extraction_v3.py ...`
docs/03-reference/extraction/transport-options.md:64 — python services/repo-truth-extractor/run_extraction_v3.py \
docs/03-reference/extraction/pipeline-reliability-2.md:15 — This document defines reliability controls added to `UPGRADES/run_extraction_v3.py`.
docs/03-reference/extraction/pipeline-phases.md:15 — - services/repo-truth-extractor/run_extraction_v3.py
docs/03-reference/extraction/failure-policy-matrix.md:16 — - services/repo-truth-extractor/run_extraction_v3.py
docs/03-reference/extraction/failure-policy-matrix.md:25 — - `python services/repo-truth-extractor/run_extraction_v3.py --doctor --run-id <RUN_ID>` (plan output)
docs/03-reference/extraction/doctor-reprocess.md:16 — - services/repo-truth-extractor/run_extraction_v3.py
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:80 — `services/repo-truth-extractor/run_extraction_v3.py`
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:156 — Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.

### SCRIPTS (11)
scripts/create_llm_archive.sh:39 — 2) services/repo-truth-extractor/run_extraction_v3.py
scripts/create_llm_archive.sh:62 — cp services/repo-truth-extractor/run_extraction_v3.py "${staging_root}/services/repo-truth-extractor/"
scripts/create_llm_archive.sh:114 — 2) services/repo-truth-extractor/run_extraction_v3.py
scripts/run_processpool_stability_tests.sh:10 — python -m pytest tests/unit/test_run_extraction_v3_processpool_stability.py --no-cov -q
scripts/RUN_DETERMINISM_TEST.sh:30 — python services/repo-truth-extractor/run_extraction_v3.py \
scripts/RUN_DETERMINISM_TEST.sh:42 — python services/repo-truth-extractor/run_extraction_v3.py \
scripts/reprocess_failed_partitions.py:17 — RUNNER_SCRIPT = Path("services/repo-truth-extractor/run_extraction_v3.py")
services/repo-truth-extractor/tools/phase0_serialize_partitions.py:15 — # Add the service directory to path to import from run_extraction_v3
services/repo-truth-extractor/tools/phase0_serialize_partitions.py:21 — from run_extraction_v3 import build_partitions, build_inventory
services/repo-truth-extractor/tools/phase0_serialize_partitions.py:23 — print(f"Error importing from run_extraction_v3: {e}")
services/repo-truth-extractor/tools/phase0_serialize_partitions.py:103 — from run_extraction_v3 import Collector, is_text_candidate, safe_read, sha256_text, classify_kind

### ARTIFACTS (132)
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/16_UPLOAD_ORDER.md:30 — 21. `services/repo-truth-extractor/run_extraction_v3.py`
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/03_RTE_SURFACE_MAP.md:12 — - OBSERVED v3 legacy/fallback runner: `services/repo-truth-extractor/run_extraction_v3.py`; proof says live execution is now gated by explicit consent.
out/rte-pkt-02-payload-redaction/RTE-PKT-02_REMAINING_UNKNOWNS.md:30 — `run_extraction_v3.py` has separate provider/batch surfaces, but this packet target and allowlist name RTE v5 and Grok prescan paths. v3 was not changed.
out/rte-pkt-02-payload-redaction/RTE-PKT-02_PAYLOAD_REDACTION_MATRIX.md:18 — - Legacy `run_extraction_v3.py` provider paths remain outside this packet's target and allowlist.
out/rte-pkt-02-payload-redaction/RTE-PKT-02_MANIFEST.json:88 — "Legacy run_extraction_v3 provider payload paths were not changed because the packet target and allowlist are v5/RTE prescan focused."
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:56 — "services/repo-truth-extractor/run_extraction_v3.py",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:186 — "services/repo-truth-extractor/run_extraction_v3.py": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md:8 — | Unknown pipeline version or legacy v3 execution could fail open. | FIXED | `proof/TP-RTE-V3-CONSENT-004/PROOF.json`, PR #605, `src/dopemux/commands/extractor_commands.py:467`, `services/repo-truth-extractor/run_extraction_v3.py:11249` | L …[truncated]
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md:15 — | Multiple legacy extraction runtimes remain (`run_extraction.py`, v3, v4, v5). | PARTIALLY_FIXED | `services/repo-truth-extractor/run_extraction_v3.py`, `run_extraction_v4.py`, `run_extraction_v5.py`, `proof/TP-RTE-V3-CONSENT-004/PROOF.jso …[truncated]
task-packets/generated/TP-RTE-BATCH-005.json:120 — "services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py",
task-packets/generated/TP-RTE-COSTPROFILE-F-VERIFY-001.json:112 — "dopemux rte promptset audit --pipeline-version v4 --no-strict 2>&1 | tee proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/promptset_audit_v3.txt"
task-packets/generated/TP-RTE-DOCS-CANON-008.json:61 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:121 — "rg -n \"rte|extractor|truth|upgrades|LegacyReplacementCommand|run_extraction|run_repscan|PipelineRunner\" src/dopemux/cli.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth- …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:122 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:140 — "services/repo-truth-extractor/run_extraction_v3.py",
task-packets/generated/TP-RTE-DOCS-CANON-008.json:153 — "rg -n \"dopemux upgrades|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v3|run_extraction_v4|run_repscan|python services/repo-truth-extractor/run_extraction_v5.py\" README.md docs/00-MASTER-INDEX.md docs/02-how-to/extraction …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:80 — `services/repo-truth-extractor/run_extraction_v3.py`
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:156 — Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.
out/rte-pkt-15-failed-sidecars/RTE-PKT-15_FAILED_SIDECAR_WRITER_LEDGER.md:28 — | Legacy v3 failed sidecar fixtures | `services/repo-truth-extractor/tests/fixtures/run_extraction_v3/` | Evidence fixtures only. Contents were not quoted in proof. |
task-packets/generated/TP-RTE-V3-CONSENT-004.json:39 — "services/repo-truth-extractor/run_extraction_v3.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:50 — "python services/repo-truth-extractor/run_extraction_v3.py --help",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:54 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:61 — "body": "Implements TP-RTE-V3-CONSENT-004. Adds fail-closed pipeline-version routing, adds explicit --execute plus DPMX_LIVE_OK=1 consent for legacy v3 live execution, and blocks dopemux rte scan unless the operator explicitly opts into the …[truncated]
task-packets/generated/TP-RTE-V3-CONSENT-004.json:116 — "Unknown values must raise a clear ClickException or equivalent instead of returning run_extraction_v3.py.",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:127 — "Invalid pipeline version no longer resolves to run_extraction_v3.py."
task-packets/generated/TP-RTE-V3-CONSENT-004.json:138 — "Add --execute to run_extraction_v3.py with default false.",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:144 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py"
task-packets/generated/TP-RTE-V3-CONSENT-004.json:147 — "services/repo-truth-extractor/run_extraction_v3.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:148 — "services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py"
task-packets/generated/TP-RTE-V3-CONSENT-004.json:154 — "services/repo-truth-extractor/run_extraction_v3.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:194 — "python services/repo-truth-extractor/run_extraction_v3.py --help",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:198 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py",
task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:61 — "services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py",
task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:94 — "body": "## Summary\n- Repairs the 26 RTE-suite failures observed under TP-RTE-COSTPROFILE-F-VERIFY-001 (status: NOT_VERIFIED_ACCEPTED_AS_EVIDENCE).\n- Reconciles cost-profile route expectations across v3/v5 routing tests, pre-live gate def …[truncated]
task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:152 — "task": "Cluster A — Cost-profile routing reconciliation. Apply the S2-classified repair direction across the 8 failing files: test_intelligence_routing_integration.py (gpt-4o vs gpt-5.4-mini), test_phase_d_contract_hardening.py (D-step Gem …[truncated]
task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:154 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 python -m pytest services/repo-truth-extractor/tests/test_intelligence_routing_integration.py services/repo-truth-extractor/tests/test_phase_d_contract_hardening.py services/repo-truth-extractor/tests/test_p …[truncated]
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:148 — "services/repo-truth-extractor/run_extraction_v3.py",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:231 — "services/repo-truth-extractor/run_extraction_v3.py",
proof/rte_deep_audit_gemini_007_stage1_authority.md:20 — - **Shadow Authority:** `run_extraction_v3.py` remains in the service directory. It is a standalone legacy engine that bypasses v5 safety gates.
proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json:14 — "shadow_paths_identified": ["run_extraction_v3.py", "run_extraction_v4.py", "run_extraction.py"],
proof/TP-DOPMUX-COVERAGE-POLICY-0001/TEST_OUTPUT_FULL.txt:346 — tests/unit/test_run_extraction_v3_phase_m.py:78:
proof/TP-DOPMUX-COVERAGE-POLICY-0001/TEST_OUTPUT_FULL.txt:348 — services/repo-truth-extractor/run_extraction_v3.py:10116: in run_phase_R
proof/TP-DOPMUX-COVERAGE-POLICY-0001/TEST_OUTPUT_FULL.txt:387 — E           run_extraction_v3.PromptsetBlockedError: Promptset blocked for phase R: invalid promptset (/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/v3/PROMPT_R10_*.md, /Users/hue/code/dopemux-mvp/services/repo-truth-ext …[truncated]
proof/TP-DOPMUX-COVERAGE-POLICY-0001/TEST_OUTPUT_FULL.txt:389 — services/repo-truth-extractor/run_extraction_v3.py:7710: PromptsetBlockedError
proof/TP-DOPMUX-COVERAGE-POLICY-0001/TEST_OUTPUT_FULL.txt:397 — FAILED tests/unit/test_run_extraction_v3_phase_m.py::test_run_phase_r_gates_on_required_norm_artifacts
proof/rte_deep_audit_gemini_007.json:31 — "legacy_scripts": ["run_extraction_v3.py", "run_extraction_v4.py"],
proof/TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401/PROOF.json:76 — "notes": "legacy run_extraction_v3-related failures remain outside this packet"
proof/TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401/IMPLEMENTER_REPORT.md:52 — - still fails in older `run_extraction_v3` coverage and related legacy surfaces outside this packet
proof/TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401/IMPLEMENTER_REPORT.md:59 — - Full extractor suite still contains unrelated `run_extraction_v3` failures; this packet did not backport v5 changes into v3.
proof/rte_deep_audit_gemini_007_stage1_challenge.md:10 — - **Shadow Authority Persistence:** `run_extraction_v3.py` is not just "legacy"; it is an un-gated execution path that persists in the primary service folder. It represents a "Shadow Authority" that could be accidentally invoked, bypassing  …[truncated]
proof/TP-RTE-DOCS-CANON-008/IMPLEMENTER_REPORT.md:30 — - `services/repo-truth-extractor/run_extraction_v3.py`
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:126 — "services/repo-truth-extractor/run_extraction_v3.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:15 — "services/repo-truth-extractor/run_extraction_v3.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:17 — "services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:28 — "F1-CRIT-1": "Addressed: run_extraction_v3.py now supports --execute and refuses live-capable v3 operations unless --execute and DPMX_LIVE_OK=1 are both present. The refusal happens before root/run context resolution and before run artifact …[truncated]
proof/TP-RTE-V3-CONSENT-004/PROOF.json:29 — "F1-CRIT-2": "Addressed: _extractor_runner_path now accepts only v5, v4, and v3, and raises ClickException for unknown values instead of returning run_extraction_v3.py.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:33 — "_extractor_runner_path returned run_extraction_v3.py for any pipeline_version other than v5 or v4.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:34 — "run_extraction_v3.py had no --execute flag and treated omitted --dry-run as live-capable execution.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:35 — "run_extraction_v3.py resolved run context and created v3 run directories before any live consent posture existed.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:36 — "run_repscan.py created v3 run artifacts and delegated to run_extraction_v3.py without a wrapper-level legacy opt-in.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:41 — "run_extraction_v3.py exposes --execute and requires both --execute and DPMX_LIVE_OK=1 for live-capable phase, async, finalize, batch-watch, or batch-retrieve operations.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:65 — "command": "python services/repo-truth-extractor/run_extraction_v3.py --help >/tmp/rte_v3_help.txt",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:85 — "command": "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:95 — "command": "pre-commit run --files services/repo-truth-extractor/run_extraction_v3.py services/repo-truth-extractor/run_repscan.py services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/tes …[truncated]
proof/TP-RTE-V3-CONSENT-004/PROOF.json:101 — "services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py",
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:8 — - `run_extraction_v3.py` now requires `--execute` and `DPMX_LIVE_OK=1` before live-capable v3 operations.
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:14 — - Runtime authority: `services/repo-truth-extractor/run_extraction_v5.py`, `run_extraction_v4.py`, `run_extraction_v3.py`, `run_repscan.py`, `src/dopemux/cli.py`, and `src/dopemux/commands/extractor_commands.py`.
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:22 — - `services/repo-truth-extractor/run_extraction_v3.py`
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:24 — - `services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py`
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:48 — - `python services/repo-truth-extractor/run_extraction_v3.py --help >/tmp/rte_v3_help.txt`: exit 0
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:52 — - `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py`: exit 0, 2 …[truncated]
proof/rte-seam-extraction-foundation.proof.json:361 — "command": "UV_CACHE_DIR=.uv-cache uv run --frozen pytest -q services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_v5_observability_improvements.py services/repo-truth-extractor/tests/test_run …[truncated]
proof/repo-truth-extractor/audit-2026-05-22/TP-RTE-FINAL-AUDIT-MODEL-REFRESH-004_PROOF.json:149 — "run_extraction_v3.py and run_extraction_v5.py contain hardcoded legacy ROUTING_LADDERS outside this packet allowlist; this TP updates structured model_map routing only."
proof/repo-truth-extractor/audit-2026-05-22/TP-RTE-FINAL-AUDIT-GROK-NONE-REASONING-006_PROOF.json:207 — "mitigation": "Single existing BatchRequest construction site (grep confirmed: run_extraction_v5.py:13144 in v5; run_extraction_v3.py:7843 in legacy v3). v3 path is unchanged. New BatchRequest construction sites should follow the v5 pattern …[truncated]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/SERIES_VERIFICATION_REPORT.md:64 — - `test_run_extraction_v3_model_routing.py`: three route contract/strict/fallback expectations failed.
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:219 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py . [ 63%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:221 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py . [ 64%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:223 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py .. [ 65%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:225 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:227 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:229 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py . [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:231 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:233 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:235 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:237 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:239 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:241 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py ...  [ 69%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:242 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py . [ 69%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:244 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py . [ 69%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:246 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py . [ 70%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:470 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:157: in test_contract_lane_routes_override_policy_for_json_managed_steps
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:477 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:188: in test_resolve_effective_step_route_marks_strict_required_contract_lane
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:481 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:305: in test_no_auto_transport_flip_across_retry_hops
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:571 — FAILED services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py::test_contract_lane_routes_override_policy_for_json_managed_steps
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:572 — FAILED services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py::test_resolve_effective_step_route_marks_strict_required_contract_lane
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:573 — FAILED services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py::test_no_auto_transport_flip_across_retry_hops
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:183 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py . [ 60%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:185 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py . [ 61%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:187 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py .. [ 62%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:189 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py . [ 63%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:191 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py . [ 64%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:193 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py . [ 64%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:195 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py . [ 65%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:197 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py . [ 65%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:199 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:201 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:203 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:205 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py ...  [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:206 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py . [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:208 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py . [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:210 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/PROOF.json:25 — "services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py",
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:183 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py . [ 60%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:185 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py . [ 61%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:187 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py .. [ 62%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:189 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py . [ 63%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:191 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py . [ 64%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:193 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py . [ 64%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:195 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py . [ 65%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:197 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py . [ 65%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:199 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:201 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:203 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py . [ 66%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:205 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py ...  [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:206 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py . [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:208 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py . [ 67%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:210 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py . [ 68%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/REPAIR_DECISIONS.md:74 — | F16 | `test_run_extraction_v3_model_routing.py` route contract expectation 1 failed | A | stale test expectation | v3 runner routing contract; model-map v3 / E-series route migration | Update assertion to current resolved route. |
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/REPAIR_DECISIONS.md:75 — | F17 | `test_run_extraction_v3_model_routing.py` route strict expectation failed | A | stale test expectation | v3 runner routing contract; model-map v3 / E-series route migration | Update assertion to current resolved route. |
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/REPAIR_DECISIONS.md:76 — | F18 | `test_run_extraction_v3_model_routing.py` route fallback expectation failed | A | stale test expectation | v3 runner routing contract; model-map v3 / E-series route migration | Update assertion to current resolved route. |
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/REPAIR_DECISIONS.md:151 — - `run_extraction_v3.collect_provider_routes(["D"], "cost")` returns providers
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/REPAIR_DECISIONS.md:156 — - `run_extraction_v3.phase_requires_provider_preflight("D", cfg)` returns

### OTHER (503)
Makefile:95 — uv run --frozen --extra test pytest --no-cov tests/unit/test_run_extraction_v3_phase_m.py tests/unit/test_run_extraction_v3_pipeline_controls.py
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7429 — services/repo-truth-extractor/run_extraction_v3.py:24:from dataclasses import dataclass, replace
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7430 — services/repo-truth-extractor/run_extraction_v3.py:770:    ".config/mcp",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7431 — services/repo-truth-extractor/run_extraction_v3.py:2196:        or lower.startswith("~/.config/mcp/")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7432 — services/repo-truth-extractor/run_extraction_v3.py:6685:    # Guard: only attempt for the supported failure classes
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7433 — services/repo-truth-extractor/run_extraction_v3.py:8217:                "schema_gate_passed": bool(schema_ok),
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7452 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:5:from dataclasses import replace
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7453 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:15:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7454 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:17:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7455 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:113:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7456 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:114:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7457 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:115:    assert stats["escalated_partitions"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7458 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:117:    assert payload["request_meta"]["route_hop_total"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7459 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:118:    assert len(payload["request_meta"]["route_attempts"]) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7460 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:181:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7461 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:182:    assert stats["escalated_partitions"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7462 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:184:    assert payload["request_meta"]["route_hop_total"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7463 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:224:    assert stats["ok"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7464 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:225:    assert stats["failed"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7465 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:227:    assert payload["request_meta"]["route_hop_total"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7466 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:268:    assert meta["route_hop_total"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7467 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:269:    assert meta["provider"] == "openrouter"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7468 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:270:    assert meta["model_id"] == "openai/gpt-5.4"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7469 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:271:    assert meta["escalation_class"] == "schema_repair"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7470 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:272:    assert meta["opus_eligible"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7471 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:273:    assert meta["opus_block_reason"] == "blocked_for_escalation_class:schema_repair"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7472 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:306:    assert meta["route_hop_total"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7473 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:307:    assert meta["model_id"] == "openai/gpt-5.4"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7474 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:308:    assert meta["escalation_class"] == "schema_repair"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7475 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:309:    assert meta["opus_eligible"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7476 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:341:    assert meta["route_hop_total"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7477 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:342:    assert meta["model_id"] == "openai/gpt-5.4"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7478 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:343:    assert meta["escalation_class"] == "provider_transport"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7479 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:344:    assert meta["opus_eligible"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7480 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:389:    assert meta["route_hop_total"] == 3
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7481 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:390:    assert meta["provider"] == "openrouter"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7482 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:391:    assert meta["model_id"] == "anthropic/claude-opus-4-6"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7483 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:392:    assert meta["opus_eligible"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7484 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:393:    assert meta["opus_block_reason"] is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7485 — services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py:394:    assert meta["route_attempts"][1]["escalation_class"] == "hard_reconciliation"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7496 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:16:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7497 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:18:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7498 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:27:    assert spec is not None and spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7499 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:43:        assert (v3_entry[0], v3_entry[1]) == (provider, model_id), (
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7500 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:167:    assert runner.resolve_step_tier("A", "A0") == "bulk"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7501 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:168:    assert runner.resolve_step_tier("A", "A1") == "extract"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7502 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:169:    assert runner.resolve_step_tier("Q", "Q1") == "qa"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7503 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:170:    assert runner.resolve_step_tier("C", "C9") == "qa"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7504 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:171:    assert runner.resolve_step_tier("R", "R1") == "synthesis"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7505 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:172:    assert runner.resolve_step_tier("Z", "Z2") == "synthesis"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7506 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:187:    assert runner.resolve_step_ladder("cost", "D", "D0") == expected_d0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7507 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:188:    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D0") == expected_d0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7508 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:189:    assert runner.resolve_step_ladder("quality", "D", "D1") == expected_d0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7509 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:191:    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D2") == [
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7510 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:195:    assert runner.resolve_step_ladder("balanced_grok_openrouter", "C", "C1") == [
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7511 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:201:    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D4") == [
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7512 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:212:    assert route_info["reason"] == "contract_lane_primary_strict"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7513 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:213:    assert route_info["strict_required"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7514 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:214:    assert route_info["provider"] == "openai"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7515 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:215:    assert route_info["model_id"] == "gpt-5.3-codex"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7516 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:217:    assert isinstance(attempts, list) and len(attempts) >= 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7517 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:221:    assert attempts[0]["strict_capable"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7518 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:222:    assert attempts[1]["strict_capable"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7519 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:245:    assert route is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7520 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:246:    assert attempts
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7521 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:247:    assert attempts[0]["strict_capable"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7522 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:248:    assert attempts[0]["reason"] == "openrouter_strict_passthrough_unverified"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7523 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:331:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7524 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:335:    assert request_meta["no_auto_transport_flips"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7525 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:337:    assert len(attempts) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7526 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:338:    assert {row["provider"] for row in attempts} == {"openai"}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7527 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:339:    assert {row["model_id"] for row in attempts} == {"gpt-5.3-codex", "gpt-5.5"}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7528 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:371:    assert ok is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7529 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:372:    assert payload["status"] == "FAIL"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7530 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:373:    assert "xai" in payload["failed_providers"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7531 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:401:    assert payload["cli"]["gemini_model_id"] == "models/gemini-2.5-flash"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7532 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:402:    assert payload["cli"]["routing_policy"] == "cost"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7533 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:403:    assert payload["effective_model_routing"]["A"]["provider"] == "openai"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7534 — services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py:404:    assert payload["effective_model_routing"]["A"]["model_id"] == "gpt-5.3-codex"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8383 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:14:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8384 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:16:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8385 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:106:    assert calls["count"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8386 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:107:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8387 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:108:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8388 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:111:    assert request_meta["parse_retry_attempted"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8389 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:112:    assert request_meta["parse_retry_attempts"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8390 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:113:    assert request_meta["parse_retry_reason"] == "max_tokens_string_eof_parse_failure"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8391 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:114:    assert len(request_meta["parse_retry_trace"]) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8392 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:115:    assert request_meta["parse_retry_trace"][0]["artifacts_ok"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8393 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:116:    assert request_meta["parse_retry_trace"][1]["artifacts_ok"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8394 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:117:    assert not (phase_dir / "raw" / "A0__A_P0001.FAILED.txt").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8395 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:118:    assert not (phase_dir / "raw" / "A0__A_P0001.FAILED.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8396 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:165:    assert calls["count"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8397 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:166:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8398 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:167:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8399 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:170:    assert request_meta["parse_retry_attempted"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8400 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:171:    assert request_meta["parse_retry_attempts"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8401 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:172:    assert request_meta["parse_retry_reason"] == "json_contract_parse_failure"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8402 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:173:    assert len(request_meta["parse_retry_trace"]) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8403 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:220:    assert calls["count"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8404 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:221:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8405 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:222:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8406 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:225:    assert request_meta["parse_retry_attempted"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8407 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:226:    assert request_meta["parse_retry_attempts"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8408 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:227:    assert request_meta["parse_retry_reason"] == "json_contract_parse_failure"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8409 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:228:    assert request_meta["parse_retry_trace"][0]["strict_string_literal_error"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8410 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:229:    assert request_meta["parse_retry_trace"][0]["strict_semantic_eof_eligible"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8411 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:262:    assert calls["count"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8412 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:263:    assert stats["ok"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8413 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:264:    assert stats["failed"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8414 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:267:    assert request_meta["parse_retry_attempted"] is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8415 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:268:    assert request_meta["parse_retry_attempts"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8416 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:269:    assert request_meta["parse_retry_reason"] == "max_tokens_string_eof_parse_failure"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8417 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:270:    assert len(request_meta["parse_retry_trace"]) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8418 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:271:    assert request_meta["parse_retry_trace"][0]["artifacts_ok"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8419 — services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py:272:    assert request_meta["parse_retry_trace"][1]["artifacts_ok"] is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8809 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:22:    assert "--phase" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8810 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:23:    assert "--status-json" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8811 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:24:    assert "--doctor" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8812 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:25:    assert "--batch-watch" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8813 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:26:    assert "--batch-submit-only" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8814 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:27:    assert "--print-run-order" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8815 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:28:    assert "--print-phase-routing" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8816 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:29:    assert "--print-phase-prompts" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8817 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:30:    assert "--tail-run-log" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8818 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:31:    assert "--show-provider-usage" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8819 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:44:    assert payload["run_id"] == run_id
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8820 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:45:    assert "summary" in payload
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8821 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:46:    assert "phases" in payload
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8822 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:59:    assert isinstance(phase_order, list)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8823 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:60:    assert phase_order[0]["phase_id"] == "A"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8824 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:61:    assert phase_order[-1]["phase_id"] == "S"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8825 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:82:    assert "Q" in payload["phases"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8826 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:83:    assert isinstance(payload["phases"]["Q"], list)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8827 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:103:    assert isinstance(prompts, list)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8828 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:104:    assert any(str(row.get("step_id", "")).startswith("Q") for row in prompts)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8829 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:142:    assert "step=C0" in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8830 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:143:    assert "step=C1" not in result.stdout
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8831 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:178:    assert payload["step_start_counts"]["openai/gpt-5-mini"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8832 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:179:    assert payload["step_start_counts"]["gemini/gemini-2.5-pro"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8833 — services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py:180:    assert payload["step_done_route_counts"]["gemini/gemini-2.5-pro"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9716 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:14:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9717 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:16:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9718 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:115:    assert call_counter["count"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9719 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:116:    assert stats["resume_skipped"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9720 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:117:    assert (raw_dir / f"{step_id}__{partition_id}.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9721 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:118:    assert not (raw_dir / f"{step_id}__{partition_id}.FAILED.txt").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9722 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:119:    assert not (raw_dir / f"{step_id}__{partition_id}.FAILED.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9723 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:120:    assert not (raw_dir / f"{step_id}__{partition_id}.FAILED.trace").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9724 — services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py:121:    assert any(
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9757 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:16:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9758 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:18:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9759 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:36:    assert exc.pos > len(raw_text.rstrip())
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9760 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:37:    assert runner._is_semantic_eof_eligible(exc, raw_text) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9761 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:44:    assert exc.pos == len(raw_text.rstrip()) - 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9762 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:45:    assert runner._is_semantic_eof_eligible(exc, raw_text) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9763 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:52:    assert exc.pos < len(raw_text.rstrip()) - 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9764 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:53:    assert runner._is_semantic_eof_eligible(exc, raw_text) is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9765 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:54:    assert runner.try_repair_json_truncation(raw_text, exc) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9766 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:55:    assert runner.parse_json_from_response(raw_text) == {"a": 1}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9767 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:62:    assert runner._is_semantic_eof_eligible(exc, raw_text) is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9768 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:63:    assert runner.try_repair_json_truncation(raw_text, exc) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9769 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:78:    assert runner._is_string_literal_decode_error(exc) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9770 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:79:    assert runner._is_semantic_eof_eligible(exc, raw_text) is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9771 — services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py:80:    assert runner.try_repair_json_truncation(raw_text, exc) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10276 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:16:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10277 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:18:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10278 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:133:    assert call_counter["count"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10279 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:134:    assert stats["resume_skipped"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10280 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:135:    assert stats["recomputed"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10281 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:157:    assert call_counter["count"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10282 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:158:    assert stats["resume_skipped"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10283 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:159:    assert stats["recomputed"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10284 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:187:    assert call_counter["count"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10285 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:188:    assert stats["resume_skipped"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10286 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:189:    assert stats["recomputed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10287 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:226:    assert call_counter["count"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10288 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:227:    assert stats["resume_skipped"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10289 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:228:    assert not failed_txt_path.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10290 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:229:    assert not failed_json_path.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10291 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:273:    assert call_counter["count"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10292 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:274:    assert stats["resume_skipped"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10293 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:275:    assert any("Resume: rerun failed_newer_than_success for A0 A_P0001" in line for line in info_logs)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10294 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:276:    assert not failed_txt_path.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10295 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:277:    assert not failed_json_path.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10296 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:278:    assert any("Resume: prune stale FAILED after success for A0 A_P0001 count=2" in line for line in info_logs)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10297 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:336:    assert stats["resume_skipped"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10298 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:337:    assert stats["recomputed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10299 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:339:        assert not (raw_dir / f"A0__{partition_id}.FAILED.txt").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10300 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:340:        assert not (raw_dir / f"A0__{partition_id}.FAILED.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10301 — services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py:343:    assert resume_logs == [
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10399 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:11:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10400 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:13:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10401 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:20:    assert runner.classify_failure_type(413, "", "payload too large") == "payload"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10402 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:21:    assert runner.classify_failure_type(429, "", "rate limit") == "rate_limit"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10403 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:22:    assert runner.classify_failure_type(None, "", "") == "unknown"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10404 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:27:    assert runner.is_auth_classified_failure("auth_rejected") is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10405 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:28:    assert runner.is_auth_classified_failure("api_key_missing_or_invalid") is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10406 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:29:    assert runner.is_auth_classified_failure("rate_limit") is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10407 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:34:    assert runner.is_retryable_exception(TimeoutError("connection timeout")) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10408 — services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py:35:    assert runner.is_retryable_exception(RuntimeError("boom")) is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11302 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:14:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11303 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:16:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11304 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:61:    assert reason == "json_contract_parse_failure"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11305 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:96:    assert stats["ok"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11306 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:97:    assert stats["failed"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11307 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py:99:    assert failed_json["failure_type"] == "parse"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11848 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:12:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11849 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:14:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11850 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:21:    assert runner.classify_failure_type(401, "", "unauthorized") == "auth_rejected"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11851 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:22:    assert runner.classify_failure_type(429, "", "rate limit exceeded") == "rate_limit"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11852 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:23:    assert runner.classify_failure_type(413, "", "payload too large") == "payload"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11853 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:28:    assert runner.should_retry(429, "rate_limit", None, "default") is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11854 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:29:    assert runner.should_retry(503, "provider", None, "default") is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11855 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:30:    assert runner.should_retry(401, "auth_rejected", None, "default") is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11856 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:31:    assert runner.should_retry(429, "rate_limit", None, "none") is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11857 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:36:    assert runner.backoff_seconds(1, 2.0, 30.0) == 0.0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11858 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:37:    assert runner.backoff_seconds(2, 2.0, 30.0) == 2.0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11859 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:38:    assert runner.backoff_seconds(3, 2.0, 30.0) == 4.0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11860 — services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py:39:    assert runner.backoff_seconds(10, 2.0, 5.0) == 5.0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11861 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:11:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11862 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:13:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11863 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:34:    assert meta["run_id"] == "run-123"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11864 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:35:    assert meta["phase"] == "A"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11865 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:36:    assert meta["step_id"] == "A0"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11866 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:37:    assert meta["partition_id"] == "A_P0001"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11867 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:38:    assert meta["provider"] == "gemini"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11868 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:39:    assert "routing_signature" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11869 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:40:    assert "provider_signature" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11870 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:41:    assert "routing_tier" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11871 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:42:    assert "routing_policy" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11872 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:43:    assert "route_hop_index" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11873 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:44:    assert "route_hop_total" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11874 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:45:    assert "route_attempts" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11875 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:46:    assert "escalation_trigger" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11876 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:47:    assert "execution_mode" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11877 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:48:    assert "batch_provider" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11878 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:49:    assert "batch_job_id" in meta
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11879 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:54:    assert runner.classify_failure_type(429, "resource_exhausted", "") == "quota_or_billing"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11880 — services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py:55:    assert runner.classify_failure_type(500, "", "server exploded") == "provider"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11921 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:29:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11922 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:30:    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11923 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:31:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11924 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:37:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11925 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:38:    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11926 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:39:    assert "DPMX_LIVE_OK=1" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11927 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:40:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11928 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:46:    assert "Legacy v3 live execution requires explicit consent" not in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11929 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:52:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11930 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:53:    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11931 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:54:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11932 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:61:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11933 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:62:    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11934 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:63:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11935 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:69:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11936 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:70:    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11937 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:71:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11938 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:77:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11939 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:78:    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11940 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:79:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11941 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:86:    assert "Legacy v3 live execution requires explicit consent" not in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11942 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:100:    assert proc.returncode != 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11943 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:101:    assert "--execute and --dry-run are mutually exclusive" in proc.stderr
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11944 — services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py:102:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12428 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:16:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12429 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:18:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12430 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:74:        assert match is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12431 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:110:    assert stats["ok"] == 3
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12432 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:111:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12433 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:112:    assert stats["recomputed"] == 3
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12434 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:113:    assert write_order == ["A0__A_P0001.json", "A0__A_P0002.json", "A0__A_P0003.json"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12435 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:142:        assert match is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12436 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:173:    assert sorted(path.name for path in (phase_dir / "raw").glob("A0__*.json")) == []
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12437 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:203:        assert match is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12438 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:235:    assert stats["ok"] == 3
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12439 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:236:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12440 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:237:    assert write_order == ["A0__A_P0001.json", "A0__A_P0002.json", "A0__A_P0003.json"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12441 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:266:        assert match is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12442 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:290:    assert stats["ok"] == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12443 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:291:    assert stats["failed"] == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12444 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:292:    assert sorted(path.name for path in (phase_dir / "raw").glob("A0__*.json")) == [
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12445 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:338:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12446 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:339:    assert stats["failed"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:12447 — services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py:340:    assert (phase_dir / "raw" / "A0__A_P0001.FAILED.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13272 — services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A1__A_P0005.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPO_INSTRUCTION_SURFACE.json","payload":{"instruction_sources":[{"id":"INSTR_0001","path":"/Users/hue/code/dopemux-mvp/ …[truncated]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13401 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:3:from dataclasses import replace
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13402 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:14:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13403 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:16:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13404 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:130:    assert stats["ok"] == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13405 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:132:    assert payload["request_meta"]["execution_mode"] == "batch"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13406 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:133:    assert payload["request_meta"]["batch_job_id"] == "job-123"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13407 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:136:    assert (batch_dir / "A1.requests.jsonl").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13408 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:137:    assert (batch_dir / "A1.job.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13409 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:138:    assert (batch_dir / "A1.results.jsonl").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13410 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:139:    assert (batch_dir / "A1.summary.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13411 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:160:    assert ok is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13412 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:161:    assert status_code == 204
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13413 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:162:    assert err is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13414 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:163:    assert captured["timeout"] == 7
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13415 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:166:    assert "x-dopemux-signature" in headers
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13416 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:167:    assert headers["x-dopemux-event"] == "batch.completed"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13417 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:184:    assert ok is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13418 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:185:    assert status_code == 502
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13419 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:186:    assert err == "http_error:502"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13420 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:227:    assert result.exit_code == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13421 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:230:    assert job["state"] == "failed"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13422 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:231:    assert str(job["error"]).startswith("missing_api_key")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13423 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:274:    assert result.exit_code == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13424 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:275:    assert result.auto_continue_blocked is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13425 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:276:    assert result.next_phase is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13426 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:285:        assert "OpenRouter is not supported for live batch execution" in str(exc)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13427 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:287:        raise AssertionError("Expected openrouter batch provider rejection")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13428 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:342:    assert finalized == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13429 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:343:    assert fake_store.status_updates == []
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13430 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:392:    assert finalized == 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13431 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:394:    assert out_json.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13432 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:396:    assert payload["phase"] == "R"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13433 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:397:    assert payload["step_id"] == "R1"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13434 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:398:    assert payload["request_meta"]["execution_mode"] == "async"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13435 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:399:    assert payload["request_meta"]["external_job_id"] == "resp_1"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13436 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:400:    assert not pending_placeholder.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13437 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:401:    assert any(update["status"] == "completed" for update in fake_store.status_updates)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13438 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:430:    assert finalized == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13439 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:432:    assert not out_json.exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13440 — services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py:433:    assert any(
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13660 — services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A1__A_P0001.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPO_INSTRUCTION_SURFACE.json","payload":{"instruction_sources":[{"id":"INSTR_0001","path":"/Users/hue/code/dopemux-mvp/ …[truncated]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13727 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:17:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13728 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:19:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13729 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:34:    assert isinstance(parsed, list)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13730 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:52:    assert len(artifacts) == len(expected)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13731 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:53:    assert {row["artifact_name"] for row in artifacts} == set(expected)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13732 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:59:    assert isinstance(parsed, dict)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13733 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:66:    assert len(artifacts) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13734 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:67:    assert {row["artifact_name"] for row in artifacts} == {
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13735 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:80:    assert repaired is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13736 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:81:    assert runner.parse_json_from_response(raw_text) == {"artifacts":[{"artifact_name":"A.json","payload":{"k":1}}]}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13737 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:91:    assert repaired is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13738 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:97:    assert runner.parse_json_from_response(raw_text) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13739 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:102:    assert runner._is_string_literal_decode_error(exc) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13740 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:103:    assert runner._is_semantic_eof_eligible(exc, stripped) is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13741 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:104:    assert runner.try_repair_json_truncation(stripped, exc) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13742 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:110:    assert runner.parse_json_from_response(raw_text) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13743 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:115:    assert runner._is_string_literal_decode_error(exc) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13744 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:116:    assert runner._is_semantic_eof_eligible(exc, stripped) is False
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13745 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:117:    assert runner.try_repair_json_truncation(stripped, exc) is None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13746 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:131:    assert parsed == {"from": "first"}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13747 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:139:    assert artifacts == [{"artifact_name": "A.json", "payload": {"k": 1}}]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13748 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:152:    assert repaired_one is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13749 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:153:    assert repaired_one == repaired_two
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13750 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:154:    assert isinstance(json.loads(repaired_one), dict)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13751 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:169:    assert runner._is_string_literal_decode_error(exc_info.value) is True
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13752 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:174:    assert "Output MUST be a single JSON value" in instructions
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13753 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:175:    assert "No markdown, prose, code fences" in instructions
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13754 — services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py:176:    assert "Never emit invalid JSON" in instructions
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13883 — services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A0__A_P0004.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPOCTRL_INVENTORY.json","payload":[{"path":"docker/conport-kg/README.md","ext":"md","size":2796,"mtime":null,"sha256":n …[truncated]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14222 — services/repo-truth-extractor/tests/test_rte_v5_characterization.py:55:    assert extractor_commands._extractor_runner_path(repo_root, "v3").name == "run_extraction_v3.py"
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_surfaces.txt:685 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4539 — ./services/repo-truth-extractor/run_extraction_v3.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4679 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_artifact_parsing.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4680 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_batch_mode.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4681 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4682 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_eof_gate.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4683 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4684 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4685 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_parse_retry.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4686 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_partition_concurrency.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4687 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_prune_on_success.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4688 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_request_meta_index.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4689 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_resume_semantics.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4690 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_retry.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4691 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_retry_decisions.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4692 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_shrink_policy.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4693 — ./services/repo-truth-extractor/tests/test_run_extraction_v3_typer_cli.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:6122 — ./tests/unit/test_run_extraction_v3_phase_m.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:6123 — ./tests/unit/test_run_extraction_v3_pipeline_controls.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:6124 — ./tests/unit/test_run_extraction_v3_processpool_stability.py
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:510 — audit_inputs/dcp-runner-recon/MCP_RECON.txt:13272:services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A1__A_P0005.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPO_INSTRUCTION_SURFACE.json","payload":{"instruction_sources":[{"id" …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:512 — audit_inputs/dcp-runner-recon/MCP_RECON.txt:13660:services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A1__A_P0001.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPO_INSTRUCTION_SURFACE.json","payload":{"instruction_sources":[{"id" …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3139 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:17583:task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:61:      "services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py",
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3153 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:17597:task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:94:    "body": "## Summary\n- Repairs the 26 RTE-suite failures observed under TP-RTE-COSTPROFILE-F-VERIFY-001  …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3163 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:17607:task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:152:      "task": "Cluster A — Cost-profile routing reconciliation. Apply the S2-classified repair direction ac …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3164 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:17608:task-packets/generated/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001.json:154:        "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 python -m pytest services/repo-truth-extractor/tests/test_intellig …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3542 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:19762:task-packets/generated/TP-RTE-COSTPROFILE-F-VERIFY-001.json:112:        "dopemux rte promptset audit --pipeline-version v4 --no-strict 2>&1 | tee proof/rte-cost-profile-redesign/TP- …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:4030 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:24959:task-packets/generated/TP-RTE-V3-CONSENT-004.json:61:    "body": "Implements TP-RTE-V3-CONSENT-004. Adds fail-closed pipeline-version routing, adds explicit --execute plus DPMX_LIVE …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:4743 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:45024:services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A1__A_P0005.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPO_INSTRUCTION_SURFACE.json","payload":{"instruction_source …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:4744 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:45352:services/repo-truth-extractor/tests/fixtures/run_extraction_v3/A1__A_P0001.FAILED.txt:1:{"artifacts":[{"artifact_name":"REPO_INSTRUCTION_SURFACE.json","payload":{"instruction_source …[truncated]
reports/rte-production-certification-audit-20260414.json:11 — "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/status.txt:3 — M  services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/status.txt:16 — M  services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/status.txt:17 — M  services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:7360 — diff --git a/services/repo-truth-extractor/run_extraction_v3.py b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:7362 — --- a/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:7363 — +++ b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9431 — diff --git a/services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py b/services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9433 — --- a/services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9434 — +++ b/services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9471 — diff --git a/services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py b/services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9473 — --- a/services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9474 — +++ b/services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/diffstat.txt:2 — services/repo-truth-extractor/run_extraction_v3.py |  598 +-
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/diffstat.txt:15 — .../tests/test_run_extraction_v3_escalation.py     |    8 +-
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/diffstat.txt:16 — .../tests/test_run_extraction_v3_model_routing.py  |   21 +-
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/name-status.txt:2 — M	services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/name-status.txt:15 — M	services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/name-status.txt:16 — M	services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1996 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2001 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2006 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2026 — -rg -n "kind = op.get" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2029 — -rg -n "Processing completed future" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2032 — -rg -n "Validate write_ops" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2043 — -python services/repo-truth-extractor/run_extraction_v3.py --phase A --workers 4
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2072 — -- Code changes: Committed to `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2101 — -**Location**: `services/repo-truth-extractor/run_extraction_v3.py:6183`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2125 — -**Location**: `services/repo-truth-extractor/run_extraction_v3.py:7185-7190`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2161 — -**Location**: `services/repo-truth-extractor/run_extraction_v3.py:7259-7267`
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2191 — -rg -n "kind = op.get" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2195 — -rg -n "Processing completed future" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:2199 — -rg -n "Validate write_ops" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7980 — diff --git a/services/repo-truth-extractor/run_extraction_v3.py b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7982 — --- a/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7983 — +++ b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:8084 — # Add the service directory to path to import from run_extraction_v3
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:8098 — -        from run_extraction_v3 import Collector, is_text_candidate, safe_read, sha256_text, classify_kind
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:8100 — +        from run_extraction_v3 import Collector, safe_read, sha256_text, classify_kind
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:18310 — diff --git a/tests/unit/test_run_extraction_v3_pipeline_controls.py b/tests/unit/test_run_extraction_v3_pipeline_controls.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:18312 — --- a/tests/unit/test_run_extraction_v3_pipeline_controls.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:18313 — +++ b/tests/unit/test_run_extraction_v3_pipeline_controls.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:18322 — diff --git a/tests/unit/test_run_extraction_v3_processpool_stability.py b/tests/unit/test_run_extraction_v3_processpool_stability.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:18324 — --- a/tests/unit/test_run_extraction_v3_processpool_stability.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:18325 — +++ b/tests/unit/test_run_extraction_v3_processpool_stability.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:663 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:668 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:673 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:693 — -rg -n "kind = op.get" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:696 — -rg -n "Processing completed future" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:699 — -rg -n "Validate write_ops" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:710 — -python services/repo-truth-extractor/run_extraction_v3.py --phase A --workers 4
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:739 — -- Code changes: Committed to `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:758 — +- services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:1749 — +        "excerpt_snippet": "pytest --no-cov tests/unit/test_run_extraction_v3_phase_m.py tests/unit/test_run_extraction_v3_pipeline_controls.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:1753 — +      "recipe_or_body": "pytest --no-cov tests/unit/test_run_extraction_v3_phase_m.py tests/unit/test_run_extraction_v3_pipeline_controls.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117486 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117491 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117497 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117502 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117508 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117513 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:118005 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:118010 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:123814 — +        "<< 'EOF'\nUsage:\n  scripts/create_llm_archive.sh [--next-batch]\n\nModes:\n  --next-batch  Create targeted \"next batch\" archive for audit handoff:\n                1) Repo Truth Extractor prompts for W/B/G/Q\n                2) …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:123817 — +        "<< EOF\nDOPEMUX-MVP NEXT BATCH DELIVERABLE\n\nCreated: $(date -u +\"%Y-%m-%d %H:%M:%S UTC\")\nMode: --next-batch\n\nIncluded:\n1) Repo Truth Extractor prompts for W/B/G/Q (active v3 prompts)\n2) services/repo-truth-extractor/run_e …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:126169 — +        "excerpt_snippet": "pytest --no-cov tests/unit/test_run_extraction_v3_phase_m.py tests/unit/test_run_extraction_v3_pipeline_controls.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:126173 — +      "recipe_or_body": "pytest --no-cov tests/unit/test_run_extraction_v3_phase_m.py tests/unit/test_run_extraction_v3_pipeline_controls.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241906 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241911 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241917 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241922 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241928 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241933 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:242425 — +        "excerpt_snippet": "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:242430 — +      "to_path": "services/repo-truth-extractor/run_extraction_v3.py"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:248234 — +        "<< 'EOF'\nUsage:\n  scripts/create_llm_archive.sh [--next-batch]\n\nModes:\n  --next-batch  Create targeted \"next batch\" archive for audit handoff:\n                1) Repo Truth Extractor prompts for W/B/G/Q\n                2) …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:248237 — +        "<< EOF\nDOPEMUX-MVP NEXT BATCH DELIVERABLE\n\nCreated: $(date -u +\"%Y-%m-%d %H:%M:%S UTC\")\nMode: --next-batch\n\nIncluded:\n1) Repo Truth Extractor prompts for W/B/G/Q (active v3 prompts)\n2) services/repo-truth-extractor/run_e …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:250023 — diff --git a/services/repo-truth-extractor/run_extraction_v3.py b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:250025 — --- a/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:250026 — +++ b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:250874 — -            sys.executable, "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:179 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:184 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:189 — -**File**: `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:209 — -rg -n "kind = op.get" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:212 — -rg -n "Processing completed future" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:215 — -rg -n "Validate write_ops" services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:226 — -python services/repo-truth-extractor/run_extraction_v3.py --phase A --workers 4
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:255 — -- Code changes: Committed to `services/repo-truth-extractor/run_extraction_v3.py`
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:273 — +- services/repo-truth-extractor/run_extraction_v3.py (single real LLM call site wrapper)
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:296 — +3) DOPEMUX_RATE_LIMIT_DEBUG=1 DOPEMUX_ROUTING_YAML=/tmp/dopemux-throttle-routing.yaml DOPEMUX_RATE_LIMIT_TIMEOUT_SECONDS=0.1 OPENAI_API_KEY=dummy GEMINI_API_KEY=dummy XAI_API_KEY=dummy python services/repo-truth-extractor/run_extraction_v3 …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:324 — diff --git a/services/repo-truth-extractor/run_extraction_v3.py b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:326 — --- a/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__3___patch.diff:327 — +++ b/services/repo-truth-extractor/run_extraction_v3.py
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:383 — services/repo-truth-extractor/run_extraction_v3.py |   2 +-
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:775 — .../test_run_extraction_v3_pipeline_controls.py    |   1 -
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:776 — ...test_run_extraction_v3_processpool_stability.py |   2 -
reports/work-recovery/2026-03-05/stashes/stashat__4___stat.txt:44 — services/repo-truth-extractor/run_extraction_v3.py |   293 +-
reports/work-recovery/2026-03-05/stashes/stashat__3___stat.txt:5 — services/repo-truth-extractor/run_extraction_v3.py | 196 ++++++++++++++++++---
reports/work-recovery/2026-03-05/stashes/stashat__1___patch.diff:262 — -            sys.executable, "services/repo-truth-extractor/run_extraction_v3.py",
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2441 — services/repo-truth-extractor/run_extraction_v3.py |  1672 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2468 — .../tests/test_run_extraction_v3_batch_mode.py     |   150 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2469 — .../tests/test_run_extraction_v3_escalation.py     |   168 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2470 — .../tests/test_run_extraction_v3_model_routing.py  |   311 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2471 — .../tests/test_run_extraction_v3_parse_retry.py    |    94 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2472 — ...test_run_extraction_v3_partition_concurrency.py |    58 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2473 — .../test_run_extraction_v3_retry_decisions.py      |     4 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2652 — ...test_run_extraction_v3_processpool_stability.py |   281 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2420 — services/repo-truth-extractor/run_extraction_v3.py |  1672 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2447 — .../tests/test_run_extraction_v3_batch_mode.py     |   150 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2448 — .../tests/test_run_extraction_v3_escalation.py     |   168 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2449 — .../tests/test_run_extraction_v3_model_routing.py  |   311 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2450 — .../tests/test_run_extraction_v3_parse_retry.py    |    94 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2451 — ...test_run_extraction_v3_partition_concurrency.py |    58 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2452 — .../test_run_extraction_v3_retry_decisions.py      |     4 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2629 — ...test_run_extraction_v3_processpool_stability.py |   281 -

**COUNT LINE**: RUNTIME:10 TESTS:80 CI:0 DOCS:108 SCRIPTS:11 ARTIFACTS:132 (OTHER:503)

---

## services/repo-truth-extractor/run_extraction_v4.py (refs OUTSIDE the file itself)

Pattern: `run_extraction_v4|pipeline[-_]version.*v4|--pipeline-version v4`
Excluded (self): services/repo-truth-extractor/run_extraction_v4.py

### RUNTIME (7)
src/dopemux/commands/extractor_commands.py:471 — if pipeline_version == "v4":
src/dopemux/commands/extractor_commands.py:472 — return base / "run_extraction_v4.py"
src/dopemux/commands/extractor_commands.py:477 — f"{pipeline_version!r}. Expected one of: v5, v4, v3."
src/dopemux/cli.py:5117 — pipeline_version="v4",
src/dopemux/cli.py:5627 — dopemux rte promptset audit --pipeline-version v4 --strict
src/dopemux/cli.py:5637 — _run_extractor_runner(pipeline_version="v4", args=args)
services/repo-truth-extractor/lib/service_catalog.py:7 — # Constants moved from run_extraction_v4.py or defined here

### TESTS (19)
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/tests/TEST_AND_CI_EVIDENCE.md:1281 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py
services/repo-truth-extractor/tests/test_phase_s_prompt_registry.py:25 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
services/repo-truth-extractor/tests/test_phase_s_prompt_registry.py:26 — spec = importlib.util.spec_from_file_location("run_extraction_v4", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:13 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:14 — spec = importlib.util.spec_from_file_location("run_extraction_v4", module_path)
services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:118 — assert parsed["pipeline_version"] == "v4"
services/repo-truth-extractor/tests/test_rte_v5_characterization.py:40 — _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v4.py",
services/repo-truth-extractor/tests/test_rte_v5_characterization.py:41 — "run_extraction_v4_characterization",
services/repo-truth-extractor/tests/test_rte_v5_characterization.py:54 — assert extractor_commands._extractor_runner_path(repo_root, "v4").name == "run_extraction_v4.py"
services/repo-truth-extractor/tests/test_phase_d_pressure_caps.py:147 — runner = _load_module("run_extraction_v4.py", "run_extraction_v4_d_caps_forward")
services/repo-truth-extractor/tests/test_s_int_runner.py:58 — script = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
services/repo-truth-extractor/tests/test_phase_s_step_selection.py:27 — module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
services/repo-truth-extractor/tests/test_phase_s_step_selection.py:28 — spec = importlib.util.spec_from_file_location("run_extraction_v4", module_path)
services/repo-truth-extractor/tests/test_phase_s_step_selection.py:193 — script = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
services/repo-truth-extractor/tests/test_phase_execution_step_filter.py:91 — runner = _load_module("run_extraction_v4.py", "run_extraction_v4_step_filter")
tests/unit/test_extractor_runner_resolution.py:15 — assert runner.name == "run_extraction_v4.py"
tests/unit/test_extractor_command_authority.py:39 — ["status", "--pipeline-version", "v4", "--run-id", "rid2"],
tests/unit/test_cli_upgrades_commands.py:39 — assert kwargs["pipeline_version"] == "v4"
tests/unit/test_cli_upgrades_commands.py:409 — pipeline_version="v4",

### CI (0)
(none)

### DOCS (103)
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:267 — **`run_extraction_v5.py`** is the single canonical engine. Own `main()` (v5:21502), own `OperatorArgumentParser` (v5:1829); **no delegation** to v3/v4 (grep: zero `run_extraction_v3/v4` imports). Pinned as authority by `rte_config.py:126` ( …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:270 — **`run_extraction_v4.py`** — thin Typer wrapper that **subprocesses v5** and rebuilds deterministic v4 norm outputs (docstring v4:3-9). It is NOT an engine but IS the **default prompt/artifact-contract layer** (README:27 "v4 (default)"). Tw …[truncated]
claudedocs/pr725-proof-bundle-2026-05-30.md:71 — - `services/repo-truth-extractor/run_extraction_v4.py` — promptset docs
claudedocs/rte-truth-program-2026-07/A3b-prompts-DEGHM.md:5 — **Method**: full read of every template + `PROMPTSET_RULES.md`, `promptset.yaml`, `schemas/G6_*.schema.json`, `schemas/G7_*.schema.json`, and the runtime linter (`lib/promptgen/template_renderer.py`, `run_extraction_v4.py`)
claudedocs/rte-truth-program-2026-07/A3b-prompts-DEGHM.md:20 — **Confirmed by maintainer comment** (`run_extraction_v4.py:104–110`): `promptset.yaml`'s `required_prompt_sections` has **zero runtime readers** — sections are not enforced against prompt bodies — and the "Legacy Context (for intent only; n …[truncated]
claudedocs/rte-truth-program-2026-07/A3b-prompts-DEGHM.md:139 — - **F-5 (program)**: `required_prompt_sections` unenforced (zero runtime readers — maintainer-confirmed at `run_extraction_v4.py:104–110`) and `PROMPTSET_RULES.md` is not among any template's declared runner-context artifacts. For ~30/40 te …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:19 — Important discrepancy found: the authority map says `run_extraction_v4.py` is 1,142 lines and a "Typer wrapper" — confirmed Typer (`APP = typer.Typer`, v4:29). But v4 has its own `PHASE_DIR_NAMES` dict that **diverges** from `phases.py`: v4 …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:37 — This is now a material finding. The operator CLI (`extractor_commands.py:467-478`) is a **multi-version dispatcher** that accepts `pipeline_version` of v5/v4/v3 and resolves to the corresponding runner via subprocess. So v3 *is* operator-re …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:43 — Key clarification: the `extractor` command group's `run` (line 282) is **disabled** (raises ClickException at line 291) — it does NOT reach `_run_extractor_runner`. And `status` (line 323) disables the legacy `--pipeline-version` alias (lin …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:49 — - `cli.py:5522` hardcodes `pipeline_version="v4"` for one command — need to know which.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:99 — 2. **`required_prompt_sections` is consumed by v4's `load_promptset()`** (run_extraction_v4.py:103-104) but I need to verify if v4 actually *validates* prompts against the 9 required sections. It's referenced in `lib/promptgen/contract_gene …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1444 — - v5 is the canonical engine (`rte_config.py:126`, observed). v4 (`run_extraction_v4.py`) is a thin Typer wrapper that delegates to v5 (`V5_RUNNER`, observed `run_extraction_v4.py:35`) but enforces v4 prompt/artifact contracts.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1464 — Confirmed. The operator CLI (`src/dopemux/cli.py:4920`, observed) defaults `--pipeline-version` to `v5`, and `cli.py:4949` hardcodes `pipeline_version="v5"` for the truth-run alias. This contradicts README:27 ("v4 (default)"). The runtime a …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1475 — - `run_extraction_v4.py` — Typer wrapper; executes v5 (`V5_RUNNER`, v4:35) but enforces v4 prompt/artifact contracts from `promptsets/v4/`. *Authority over v4 contract shape, not execution.*
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:17 — Repo Truth Extractor is the repository's canonical repo-truth extraction runtime family. In the inspected code, the primary execution authority is `services/repo-truth-extractor/run_extraction_v5.py`, with `run_extraction_v4.py` acting as a …[truncated]
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:47 — Evidence: `services/repo-truth-extractor/run_extraction_v4.py` states it "keeps v5 execution intact" while loading v4 prompt/artifact manifests, executing v5 for supported phases, and rebuilding deterministic v4 normalized outputs under `ex …[truncated]
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:72 — `services/repo-truth-extractor/run_extraction_v4.py`
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:90 — - v4 root/constants in `run_extraction_v4.py`: `extraction/repo-truth-extractor/v4`
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:123 — - v4 normalized outputs rebuilt by `run_extraction_v4.py`
docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md:146 — Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.
docs/research/mcp-customization/dopemux-constraints/TRUTH_SYSTEMS.md:208 — - Preserves v4 contract compatibility through `run_extraction_v4.py`.
docs/research/mcp-customization/dopemux-constraints/TRUTH_CANONICALS.md:203 — - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v4.py`
docs/research/mcp-customization/dopemux-constraints/TRUTH_CANONICALS.md:210 — - `run_extraction_v4.py` explicitly wraps v5 for v4 contract compatibility.
docs/research/mcp-customization/dopemux-constraints/ARCHITECTURE.md:163 — - compatibility contract rebuilding can occur through `run_extraction_v4.py`
services/repo-truth-extractor/README.md:73 — - `services/repo-truth-extractor/run_extraction_v4.py`
docs/audit/rte-opus-uiux-claude-design-audit/recommendations.md:96 — - **Verification:** `dopemux rte promptset audit --pipeline-version v5` either succeeds or returns a message that explicitly states the v5-audit gap and offers the v4 fallback.
docs/audit/rte-opus-uiux-claude-design-audit/ux-risk-ledger.md:55 — - **Harm:** `ClickException("Promptset audit is implemented for v4 only.")`. Operator either tries `--pipeline-version v4` (wrong engine) or gives up. The pre-flight audit they wanted is unavailable. (`F-OPUS-HIGH-4`)
docs/05-audit-reports/rte-production-certification-audit-20260414.md:53 — | `services/repo-truth-extractor/run_extraction_v4.py` | `compatibility runtime` | Active shim; v4 core suite passed. |
docs/05-audit-reports/rte-production-certification-audit-20260414.md:293 — - `pytest -q services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_extraction_v4_core.py services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py services/repo-truth-extr …[truncated]
docs/05-audit-reports/rte-production-certification-audit-20260414.md:300 — - `python -m py_compile src/dopemux/cli.py src/dopemux/commands/extract_commands.py src/dopemux/commands/extractor_commands.py src/dopemux/commands/extractor_validation.py src/dopemux/commands/extractor_validation_ui.py src/dopemux/extracto …[truncated]
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:56 — - Compatibility runtime: `services/repo-truth-extractor/run_extraction_v4.py`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:107 — - `services/repo-truth-extractor/run_extraction_v4.py`: compatibility writer preserving v4 prompt/artifact contracts while delegating supported execution to v5
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:131 — | `services/repo-truth-extractor/promptsets/v4/promptset.yaml` | canonical | Declares active v4 prompt/artifact contract consumed by runtime and validator | Referenced by `run_extraction_v4.py`, `validate_pre_live_gate_v25.py`, and snapshot …[truncated]
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:160 — 2. `services/repo-truth-extractor/run_extraction_v4.py`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:207 — | `services/repo-truth-extractor/run_extraction_v4.py` | compatibility_runtime | Shows current compatibility layer and v4 contract preservation boundary | yes |
ARCHITECTURE.md:152 — - compatibility contract rebuilding can occur through `run_extraction_v4.py`
KNOWN_GAPS.md:46 — **File:** `services/repo-truth-extractor/run_extraction_v4.py` (`load_promptset`)
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:364 — - Retire `run_extraction_v4.py` — Remove 1.1K lines
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-2.md:83 — - `UPGRADES/tests/test_run_extraction_v4_core.py`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-2.md:85 — - `python UPGRADES/run_extraction_v4.py --phase C --run-id <RUN_ID> --dry-run`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-2.md:86 — - `python UPGRADES/run_extraction_v4.py --phase Q --run-id <RUN_ID> --dry-run`
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace.md:17 — - services/repo-truth-extractor/run_extraction_v4.py
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace.md:48 — - `services/repo-truth-extractor/run_extraction_v4.py`
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-2.md:17 — - services/repo-truth-extractor/run_extraction_v4.py
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-2.md:48 — - `services/repo-truth-extractor/run_extraction_v4.py`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-3.md:83 — - `UPGRADES/tests/test_run_extraction_v4_core.py`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-3.md:85 — - `python UPGRADES/run_extraction_v4.py --phase C --run-id <RUN_ID> --dry-run`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction-3.md:86 — - `python UPGRADES/run_extraction_v4.py --phase Q --run-id <RUN_ID> --dry-run`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:16 — - UPGRADES/run_extraction_v4.py
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:38 — - Runner: `UPGRADES/run_extraction_v4.py`.
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:44 — - `dopemux upgrades run` defaults to `--pipeline-version v4`.
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:80 — - `UPGRADES/tests/test_run_extraction_v4_core.py`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:82 — - `uv run python -m dopemux.cli upgrades run --pipeline-version v4 --dry-run --phase A`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint.md:83 — - `uv run python -m dopemux.cli upgrades status --pipeline-version v4 --json`
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:16 — - services/repo-truth-extractor/run_extraction_v4.py
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:30 — dopemux rte promptset audit --pipeline-version v4
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:36 — dopemux rte preflight --pipeline-version v4 --auth-doctor
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:42 — dopemux rte run --pipeline-version v4 --phase A --run-id rte_v4_local_001 --dry-run --resume
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:48 — DPMX_LIVE_OK=1 dopemux rte run --pipeline-version v4 --phase ALL --run-id rte_v4_full_001 --execute --resume
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:55 — --pipeline-version v4 \
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:66 — --pipeline-version v4 \
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:82 — dopemux rte status --pipeline-version v4 --run-id rte_v4_full_001
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:88 — dopemux rte status --pipeline-version v4 --run-id rte_v4_full_001 --json
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:94 — dopemux rte doctor --pipeline-version v4 --run-id rte_v4_full_001
docs/02-how-to/extraction/run-v4-from-dopemux-cli.md:101 — --pipeline-version v4 \
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction.md:83 — - `UPGRADES/tests/test_run_extraction_v4_core.py`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction.md:85 — - `python UPGRADES/run_extraction_v4.py --phase C --run-id <RUN_ID> --dry-run`
docs/90-adr/adr-217-upgrades-v4-all-services-deep-extraction.md:86 — - `python UPGRADES/run_extraction_v4.py --phase Q --run-id <RUN_ID> --dry-run`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:16 — - UPGRADES/run_extraction_v4.py
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:38 — - Runner: `UPGRADES/run_extraction_v4.py`.
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:44 — - `dopemux upgrades run` defaults to `--pipeline-version v4`.
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:80 — - `UPGRADES/tests/test_run_extraction_v4_core.py`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:82 — - `uv run python -m dopemux.cli upgrades run --pipeline-version v4 --dry-run --phase A`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-2.md:83 — - `uv run python -m dopemux.cli upgrades status --pipeline-version v4 --json`
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-3.md:17 — - services/repo-truth-extractor/run_extraction_v4.py
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-3.md:48 — - `services/repo-truth-extractor/run_extraction_v4.py`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:16 — - UPGRADES/run_extraction_v4.py
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:38 — - Runner: `UPGRADES/run_extraction_v4.py`.
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:44 — - `dopemux upgrades run` defaults to `--pipeline-version v4`.
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:80 — - `UPGRADES/tests/test_run_extraction_v4_core.py`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:82 — - `uv run python -m dopemux.cli upgrades run --pipeline-version v4 --dry-run --phase A`
docs/90-adr/adr-216-upgrades-v4-runner-layout-and-cli-entrypoint-3.md:83 — - `uv run python -m dopemux.cli upgrades status --pipeline-version v4 --json`
docs/03-reference/extraction/pipeline-phases.md:16 — - services/repo-truth-extractor/run_extraction_v4.py
docs/03-reference/extraction/pipeline-phases.md:46 — dopemux upgrades run --pipeline-version v4 --phase A --routing-policy cost --dry-run --resume
docs/03-reference/extraction/pipeline-phases.md:50 — dopemux upgrades run --pipeline-version v4 --phase C --batch-mode --batch-provider openai --ui rich --execute
docs/03-reference/extraction/doctor-reprocess.md:15 — - services/repo-truth-extractor/run_extraction_v4.py
docs/03-reference/extraction/doctor-reprocess.md:26 — dopemux upgrades doctor --pipeline-version v4 --run-id <RUN_ID>
docs/03-reference/extraction/doctor-reprocess.md:34 — python services/repo-truth-extractor/run_extraction_v4.py --doctor --run-id <RUN_ID>
docs/03-reference/extraction/doctor-reprocess.md:51 — python services/repo-truth-extractor/run_extraction_v4.py \
docs/03-reference/extraction/doctor-reprocess.md:61 — python services/repo-truth-extractor/run_extraction_v4.py \
docs/03-reference/extraction/doctor-reprocess.md:70 — python services/repo-truth-extractor/run_extraction_v4.py \
docs/03-reference/extraction/artifact-contract-v4.md:15 — - services/repo-truth-extractor/run_extraction_v4.py
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:17 — Repo Truth Extractor is the repository's canonical repo-truth extraction runtime family. In the inspected code, the primary execution authority is `services/repo-truth-extractor/run_extraction_v5.py`, with `run_extraction_v4.py` acting as a …[truncated]
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:52 — Evidence: `services/repo-truth-extractor/run_extraction_v4.py` states it "keeps v5 execution intact" while loading v4 prompt/artifact manifests, executing v5 for supported phases, and rebuilding deterministic v4 normalized outputs under `ex …[truncated]
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:77 — `services/repo-truth-extractor/run_extraction_v4.py`
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:99 — - v4 root/constants in `run_extraction_v4.py`: `extraction/repo-truth-extractor/v4`
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:132 — - v4 normalized outputs rebuilt by `run_extraction_v4.py`
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:156 — Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.
docs/03-reference/truth/truth-systems.md:208 — - Preserves v4 contract compatibility through `run_extraction_v4.py`.
docs/03-reference/truth/truth-canonicals.md:210 — - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v4.py`
docs/03-reference/truth/truth-canonicals.md:220 — - `run_extraction_v4.py` explicitly wraps v5 for v4 contract compatibility.
docs/archive/unclassified-top-level/repo-truth/truth-interfaces.md:544 — - Fact: `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v4.py` explicitly preserves v4 prompt/artifact contracts while executing v5.
docs/archive/unclassified-top-level/repo-truth/truth-interfaces.md:578 — 2. Fact: `run_extraction_v4.py` wraps v5 execution and rebuilds deterministic v4-normalized outputs under `extraction/repo-truth-extractor/v4/runs/RUN_ID/`.

### SCRIPTS (0)
(none)

### ARTIFACTS (76)
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/03_ARCHITECTURE.md:152 — - compatibility contract rebuilding can occur through `run_extraction_v4.py`
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/08_TRUTH_SYSTEMS.md:208 — - Preserves v4 contract compatibility through `run_extraction_v4.py`.
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/11_TRUTH_CANONICALS.md:210 — - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v4.py`
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/11_TRUTH_CANONICALS.md:220 — - `run_extraction_v4.py` explicitly wraps v5 for v4 contract compatibility.
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:17 — Repo Truth Extractor is the repository's canonical repo-truth extraction runtime family. In the inspected code, the primary execution authority is `services/repo-truth-extractor/run_extraction_v5.py`, with `run_extraction_v4.py` acting as a …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:52 — Evidence: `services/repo-truth-extractor/run_extraction_v4.py` states it "keeps v5 execution intact" while loading v4 prompt/artifact manifests, executing v5 for supported phases, and rebuilding deterministic v4 normalized outputs under `ex …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:77 — `services/repo-truth-extractor/run_extraction_v4.py`
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:99 — - v4 root/constants in `run_extraction_v4.py`: `extraction/repo-truth-extractor/v4`
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:132 — - v4 normalized outputs rebuilt by `run_extraction_v4.py`
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:156 — Evidence: `run_extraction_v4.py` is not a separate clean-room engine; it preserves v4 contracts while executing through v5 for supported phases. `run_extraction_v3.py` still exists as a compatibility/fallback path.
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/16_UPLOAD_ORDER.md:29 — 20. `services/repo-truth-extractor/run_extraction_v4.py`
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/03_RTE_SURFACE_MAP.md:11 — - OBSERVED v4 wrapper: `services/repo-truth-extractor/run_extraction_v4.py`; it references v4 promptset paths and delegates/syncs around v5/v3 compatibility behavior.
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:55 — "services/repo-truth-extractor/run_extraction_v4.py",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:185 — "services/repo-truth-extractor/run_extraction_v4.py": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md:15 — | Multiple legacy extraction runtimes remain (`run_extraction.py`, v3, v4, v5). | PARTIALLY_FIXED | `services/repo-truth-extractor/run_extraction_v3.py`, `run_extraction_v4.py`, `run_extraction_v5.py`, `proof/TP-RTE-V3-CONSENT-004/PROOF.jso …[truncated]
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:147 — "services/repo-truth-extractor/run_extraction_v4.py",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:230 — "services/repo-truth-extractor/run_extraction_v4.py",
task-packets/generated/TP-RTE-COSTPROFILE-F-VERIFY-001.json:112 — "dopemux rte promptset audit --pipeline-version v4 --no-strict 2>&1 | tee proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/promptset_audit_v3.txt"
task-packets/generated/TP-RTE-DOCS-CANON-008.json:61 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:121 — "rg -n \"rte|extractor|truth|upgrades|LegacyReplacementCommand|run_extraction|run_repscan|PipelineRunner\" src/dopemux/cli.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth- …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:122 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:139 — "services/repo-truth-extractor/run_extraction_v4.py",
task-packets/generated/TP-RTE-DOCS-CANON-008.json:153 — "rg -n \"dopemux upgrades|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v3|run_extraction_v4|run_repscan|python services/repo-truth-extractor/run_extraction_v5.py\" README.md docs/00-MASTER-INDEX.md docs/02-how-to/extraction …[truncated]
proof/rte_deep_audit_gemini_007_stage1_authority.md:8 — 2.  **Contract Authority (Compatibility):** `services/repo-truth-extractor/run_extraction_v4.py`
task-packets/generated/TP-RTE-V3-CONSENT-004.json:51 — "python services/repo-truth-extractor/run_extraction_v4.py --help",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:195 — "python services/repo-truth-extractor/run_extraction_v4.py --help",
proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json:14 — "shadow_paths_identified": ["run_extraction_v3.py", "run_extraction_v4.py", "run_extraction.py"],
proof/rte_deep_audit_gemini_007.json:31 — "legacy_scripts": ["run_extraction_v3.py", "run_extraction_v4.py"],
proof/TP-RTE-DOCS-CANON-008/IMPLEMENTER_REPORT.md:29 — - `services/repo-truth-extractor/run_extraction_v4.py`
proof/rte_deep_audit_gemini_007_stage1_challenge.md:9 — - **v4 Wrapper Complexity:** The discovery that `run_extraction_v4.py` is an active wrapper for `v5` complicates the "terminal authority" claim. An operator invoking `v4` triggers a dual-authority state where `v4` dictates the schema/contra …[truncated]
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:125 — "services/repo-truth-extractor/run_extraction_v4.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1057 — "services/repo-truth-extractor/run_extraction_v4.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:33 — "_extractor_runner_path returned run_extraction_v3.py for any pipeline_version other than v5 or v4.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:70 — "command": "python services/repo-truth-extractor/run_extraction_v4.py --help >/tmp/rte_v4_help.txt",
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:14 — - Runtime authority: `services/repo-truth-extractor/run_extraction_v5.py`, `run_extraction_v4.py`, `run_extraction_v3.py`, `run_repscan.py`, `src/dopemux/cli.py`, and `src/dopemux/commands/extractor_commands.py`.
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:49 — - `python services/repo-truth-extractor/run_extraction_v4.py --help >/tmp/rte_v4_help.txt`: exit 0
proof/rte-prelive-audit-pack-2026-04-23.proof.json:23 — "services/repo-truth-extractor/run_extraction_v4.py",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:112 — "path": "services/repo-truth-extractor/run_extraction_v4.py",
proof/rte-seam-extraction-foundation.proof.json:234 — "command": "python3 -m pytest -q services/repo-truth-extractor/tests/test_run_extraction_v4_core.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py serv …[truncated]
proof/rte-seam-extraction-foundation.proof.json:300 — "command": "UV_CACHE_DIR=.uv-cache uv run --frozen pytest -q services/repo-truth-extractor/tests/test_run_extraction_v4_core.py services/repo-truth-extractor/tests/test_truth_run_cli.py --maxfail=1 --disable-warnings --no-cov",
proof/rte-seam-extraction-foundation.proof.json:343 — "command": "UV_CACHE_DIR=.uv-cache uv run --frozen pytest -q services/repo-truth-extractor/tests/test_run_extraction_v4_core.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_extractio …[truncated]
proof/rte-seam-extraction-foundation.proof.json:368 — "command": "UV_CACHE_DIR=.uv-cache uv run --frozen pytest -q services/repo-truth-extractor/tests/test_live_llm_guard.py services/repo-truth-extractor/tests/test_run_extraction_v5_cost_cap.py services/repo-truth-extractor/tests/test_run_extr …[truncated]
proof/rte-seam-extraction-foundation.proof.json:386 — "command": "UV_CACHE_DIR=.uv-cache uv run --frozen pytest -q services/repo-truth-extractor/tests/test_phase_runner_seam.py services/repo-truth-extractor/tests/test_phase_interaction.py services/repo-truth-extractor/tests/test_phase_executio …[truncated]
proof/rte_deep_audit_gemini_007.md:28 — - **Fragmentation:** `run_extraction_v4.py` acts as an active contract wrapper for v5, while `v3` persists as an un-gated "Shadow Authority".
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:248 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py ..... [ 70%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:212 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py ..... [ 69%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:212 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py ..... [ 69%]
proof/pr_merge/run_20260530_221722/pr/725/COMMANDS_RUN.txt:138 — services/repo-truth-extractor/run_extraction_v4.py
proof/pr_merge/run_20260530_221722/pr/725/COMMANDS_RUN.txt:156 — $ pre-commit run --files INSTALL.md KNOWN_GAPS.md claudedocs/pr725-proof-bundle-2026-05-30.md docs/02-how-to/install.md docs/02-how-to/universal-extractor-usage.md install.sh scripts/deploy/deployment/stack_up_all.sh scripts/install-docker- …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/STATE.json:238 — "command": "pre-commit run --files INSTALL.md KNOWN_GAPS.md claudedocs/pr725-proof-bundle-2026-05-30.md docs/02-how-to/install.md docs/02-how-to/universal-extractor-usage.md install.sh scripts/deploy/deployment/stack_up_all.sh scripts/insta …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/STATE.json:320 — "command": "pre-commit run --files INSTALL.md KNOWN_GAPS.md claudedocs/pr725-proof-bundle-2026-05-30.md docs/02-how-to/install.md docs/02-how-to/universal-extractor-usage.md install.sh scripts/deploy/deployment/stack_up_all.sh scripts/insta …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/STATE_RECOMPUTE_REPORT.json:241 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/STATE_RECOMPUTE_REPORT.json:323 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/STATE_RECOMPUTE_REPORT.json:613 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/STATE_RECOMPUTE_REPORT.json:695 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/724/COMMANDS_RUN.txt:140 — services/repo-truth-extractor/run_extraction_v4.py
proof/pr_merge/run_20260530_221722/pr/724/COMMANDS_RUN.txt:161 — $ pre-commit run --files .claude/claude.md .claude/hooks/orchestrator_enforcement.py .claude/hooks/orchestrator_subagent_protocol.py .claude/settings.json CHANGELOG.md INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal-extractor- …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/CLOSED_LOOP_TRACE.json:258 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/CLOSED_LOOP_TRACE.json:340 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/CLOSED_LOOP_TRACE.json:630 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/725/traces/CLOSED_LOOP_TRACE.json:712 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221722/pr/724/STATE.json:232 — "command": "pre-commit run --files .claude/claude.md .claude/hooks/orchestrator_enforcement.py .claude/hooks/orchestrator_subagent_protocol.py .claude/settings.json CHANGELOG.md INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal- …[truncated]
proof/pr_merge/run_20260530_221722/pr/724/STATE.json:354 — "command": "pre-commit run --files .claude/claude.md .claude/hooks/orchestrator_enforcement.py .claude/hooks/orchestrator_subagent_protocol.py .claude/settings.json CHANGELOG.md INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal- …[truncated]
proof/pr_merge/run_20260530_203332/pr/724/COMMANDS_RUN.txt:149 — services/repo-truth-extractor/run_extraction_v4.py
proof/pr_merge/run_20260530_203332/pr/724/COMMANDS_RUN.txt:171 — $ pre-commit run --files .claude/claude.md .claude/hooks/orchestrator_enforcement.py .claude/hooks/orchestrator_subagent_protocol.py .claude/settings.json CHANGELOG.md INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal-extractor- …[truncated]
proof/pr_merge/run_20260530_203332/pr/724/STATE.json:228 — "command": "pre-commit run --files .claude/claude.md .claude/hooks/orchestrator_enforcement.py .claude/hooks/orchestrator_subagent_protocol.py .claude/settings.json CHANGELOG.md INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal- …[truncated]
proof/pr_merge/run_20260530_203332/pr/724/STATE.json:350 — "command": "pre-commit run --files .claude/claude.md .claude/hooks/orchestrator_enforcement.py .claude/hooks/orchestrator_subagent_protocol.py .claude/settings.json CHANGELOG.md INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal- …[truncated]
proof/pr_merge/run_20260530_203332/pr/725/COMMANDS_RUN.txt:137 — services/repo-truth-extractor/run_extraction_v4.py
proof/pr_merge/run_20260530_203332/pr/725/COMMANDS_RUN.txt:155 — $ pre-commit run --files INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal-extractor-usage.md install.sh scripts/deploy/deployment/stack_up_all.sh scripts/install-docker-mcp-servers.sh scripts/setup.sh services/dope-context/Dock …[truncated]
proof/pr_merge/run_20260530_203332/pr/725/STATE.json:212 — "command": "pre-commit run --files INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal-extractor-usage.md install.sh scripts/deploy/deployment/stack_up_all.sh scripts/install-docker-mcp-servers.sh scripts/setup.sh services/dope-co …[truncated]
proof/pr_merge/run_20260530_203332/pr/725/STATE.json:334 — "command": "pre-commit run --files INSTALL.md docs/02-how-to/install.md docs/02-how-to/universal-extractor-usage.md install.sh scripts/deploy/deployment/stack_up_all.sh scripts/install-docker-mcp-servers.sh scripts/setup.sh services/dope-co …[truncated]
proof/pr_merge/run_20260530_221237/pr/725/COMMANDS_RUN.txt:183 — services/repo-truth-extractor/run_extraction_v4.py
proof/pr_merge/run_20260530_221237/pr/725/COMMANDS_RUN.txt:211 — $ pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-readiness-2 …[truncated]
proof/pr_merge/run_20260530_221237/pr/725/STATE.json:233 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260530_221237/pr/725/STATE.json:315 — "command": "pre-commit run --files .Jules/palette.md .pre-commit-config.yaml INSTALL.md KNOWN_GAPS.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md claudedocs/beta-readiness-2026-05-29/00-MASTER-REPORT.md.v1.bak claudedocs/beta-r …[truncated]
proof/pr_merge/run_20260418_111828/pr/464/REVIEW_THREADS.json:184 — "body": "These prescan flags are appended to the runner args regardless of `effective_version`. If a user runs pipeline v4 and sets any of these options, `run_extraction_v4.py` will receive unknown CLI flags and fail. Add a guard that eithe …[truncated]

### OTHER (53)
config/runtime_authority_manifest.json:707 — "path": "services/repo-truth-extractor/run_extraction_v4.py",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:7489 — services/repo-truth-extractor/run_extraction_v4.py:21:from dataclasses import dataclass
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8226 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:15:    assert spec is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8227 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:17:    assert spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8228 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:25:    assert runner.numeric_step_sort_key("C9") < runner.numeric_step_sort_key("C10")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8229 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:42:    assert "generated_at" not in stripped
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8230 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:43:    assert "run_id" not in stripped
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8231 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:44:    assert "timestamp" not in stripped["items"][0]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8232 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:45:    assert "created_at" not in stripped["items"][1]["nested"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8233 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:58:    assert [row["id"] for row in items] == ["A", "B"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8234 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:59:    assert isinstance(items[0].get("evidence"), list)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8235 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:85:    assert payload["status"] == "FAIL"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8236 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:86:    assert payload["service_count_expected"] >= 1
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8237 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:87:    assert "missing_services" in payload
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8238 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:108:    assert observed == expected
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8239 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:109:    assert coverage["status"] == "PASS"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8240 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:110:    assert coverage["service_count_expected"] == len(expected)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8241 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:111:    assert coverage["service_count_observed"] == len(expected)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8242 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:118:    assert parsed["pipeline_version"] == "v4"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8243 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:119:    assert "/extraction/repo-truth-extractor/v4/runs/" in parsed["run_dir"]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8244 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:122:def test_build_v3_cmd_passes_routing_and_batch_flags() -> None:
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8245 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:154:    assert "--routing-policy cost" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8246 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:155:    assert "--executor process" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8247 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:156:    assert "--disable-escalation" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8248 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:157:    assert "--escalation-max-hops 3" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8249 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:158:    assert "--batch-mode" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8250 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:159:    assert "--batch-provider openai" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8251 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:160:    assert "--batch-poll-seconds 15" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8252 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:161:    assert "--batch-wait-timeout-seconds 120" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8253 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:162:    assert "--batch-max-requests-per-job 99" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8254 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:163:    assert "--ui rich" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8255 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:164:    assert "--pretty" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8256 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:165:    assert "--quiet" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8257 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:166:    assert "--jsonl-events" in cmd_text
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8258 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:185:    assert rc == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8259 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:186:    assert captured["env"]["REPO_TRUTH_EXTRACTOR_PROMPT_ROOT"] == str(prompt_root.resolve())
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8260 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:187:    assert captured["env"]["UPGRADES_PROMPT_ROOT"] == str(prompt_root.resolve())
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8261 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:215:        assert False, "Expected verify_resume_proof_prompt_paths to fail"
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8262 — services/repo-truth-extractor/tests/test_run_extraction_v4_core.py:217:        assert "non-v4 prompts" in str(exc)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14221 — services/repo-truth-extractor/tests/test_rte_v5_characterization.py:54:    assert extractor_commands._extractor_runner_path(repo_root, "v4").name == "run_extraction_v4.py"
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3542 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:19762:task-packets/generated/TP-RTE-COSTPROFILE-F-VERIFY-001.json:112:        "dopemux rte promptset audit --pipeline-version v4 --no-strict 2>&1 | tee proof/rte-cost-profile-redesign/TP- …[truncated]
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4540 — ./services/repo-truth-extractor/run_extraction_v4.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4694 — ./services/repo-truth-extractor/tests/test_run_extraction_v4_core.py
reports/rte-production-certification-audit-20260414.json:10 — "services/repo-truth-extractor/run_extraction_v4.py",
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7993 — diff --git a/services/repo-truth-extractor/run_extraction_v4.py b/services/repo-truth-extractor/run_extraction_v4.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7995 — --- a/services/repo-truth-extractor/run_extraction_v4.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7996 — +++ b/services/repo-truth-extractor/run_extraction_v4.py
reports/rte-production-certification-status.json:10 — "UV_CACHE_DIR=/tmp/uv-cache uv run --frozen pytest services/repo-truth-extractor/tests/test_run_extraction_v4_core.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_extraction_v5_opera …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:384 — services/repo-truth-extractor/run_extraction_v4.py |   2 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2442 — services/repo-truth-extractor/run_extraction_v4.py |   365 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2474 — .../tests/test_run_extraction_v4_core.py           |     2 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2421 — services/repo-truth-extractor/run_extraction_v4.py |   365 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2453 — .../tests/test_run_extraction_v4_core.py           |     2 -

**COUNT LINE**: RUNTIME:7 TESTS:19 CI:0 DOCS:103 SCRIPTS:0 ARTIFACTS:76 (OTHER:53)

---

## services/repo-truth-extractor/run_extraction.py (bare, no version suffix)

Pattern: `run_extraction(?!_v\d)(?!_pipeline)` (PCRE2)

### RUNTIME (21)
src/dopemux_github_specialist/cli.py:13 — from .gemini.adapter import run_extraction_adapter
src/dopemux_github_specialist/cli.py:38 — report = run_extraction_adapter(
src/dopemux_github_specialist/gemini/adapter.py:13 — def run_extraction_adapter(
src/dopemux/extraction/pipeline_orchestrator.py:319 — extraction_summary = self._run_extraction()
src/dopemux/extraction/pipeline_orchestrator.py:392 — def _run_extraction(self) -> Dict[str, Any]:
src/dopemux/cli.py:4408 — result = pipeline.run_extraction()
src/dopemux/cli.py:4637 — result = pipeline.run_extraction()
src/dopemux/ux/wizard/extraction.py:54 — def run_extraction(state: WizardState) -> StageResult:
src/dopemux/ux/wizard/runner.py:13 — from .extraction import run_extraction
src/dopemux/ux/wizard/runner.py:62 — (7, "Extraction", "🚀", run_extraction),
services/dopemux-gpt-researcher/backend/chatlog_extractor.py:119 — def run_extraction(self, start_phase: str = "Discovery", auto_confirm: bool = False) -> Dict[str, Any]:
services/dopemux-gpt-researcher/backend/chatlog_extractor.py:838 — results = extractor.run_extraction(args.start_phase, args.auto_confirm)
services/dopemux-gpt-researcher/research_api/chatlog_extractor.py:124 — def run_extraction(self, start_phase: str = "Discovery", auto_confirm: bool = False) -> Dict[str, Any]:
services/dopemux-gpt-researcher/research_api/chatlog_extractor.py:844 — results = extractor.run_extraction(args.start_phase, args.auto_confirm)
services/dopemux-gpt-researcher/backend/enhanced_chatlog_extractor.py:200 — async def run_extraction(
services/dopemux-gpt-researcher/backend/enhanced_chatlog_extractor.py:1008 — results = await extractor.run_extraction(
services/dopemux-gpt-researcher/research_api/enhanced_chatlog_extractor.py:205 — async def run_extraction(
services/dopemux-gpt-researcher/research_api/enhanced_chatlog_extractor.py:1013 — results = await extractor.run_extraction(
services/repo-truth-extractor/extraction_hygiene.py:323 — _VERSION_RE = re.compile(r"run_extraction_v(\d+)\.py$")
services/dopemux-gpt-researcher/backend/extraction_pipeline.py:218 — def run_extraction(self, files: Optional[List[Path]] = None) -> Dict[str, Any]:
services/repo-truth-extractor/run_extraction.py:26 — logger = logging.getLogger("run_extraction")

### TESTS (6)
tests/unit/test_wizard_interactivity.py:25 — from dopemux.ux.wizard.extraction import run_extraction
tests/unit/test_wizard_interactivity.py:119 — def test_run_extraction_uses_v5_upgrades_wrapper_with_resume_and_rich_ui(
tests/unit/test_wizard_interactivity.py:160 — result = run_extraction(
services/repo-truth-extractor/tests/test_pre_live_gate_v25.py:199 — if "run_extraction" in str(path)
services/repo-truth-extractor/tests/test_pre_live_gate_v25.py:377 — monkeypatch.setattr(gate, "load_module", lambda path, name: FakeRunner() if "run_extraction" in str(path) else type("FakeContract", (), {"compile_phase_contract_map": lambda self=None: {"steps": {}}, "write_phase_contract_map": lambda self, …[truncated]
services/repo-truth-extractor/tests/test_pre_live_gate_v25.py:490 — monkeypatch.setattr(gate, "load_module", lambda path, name: FakeRunner() if "run_extraction" in str(path) else type("FakeContract", (), {"compile_phase_contract_map": lambda self=None: {"steps": {}}, "write_phase_contract_map": lambda self, …[truncated]

### CI (0)
(none)

### DOCS (81)
docs/systems/gpt-researcher/enhanced-pipeline.md:134 — results = await extractor.run_extraction()
docs/03-reference/instructions/gemini-2.md:17 — - **NO LIVE RUNNER EXECUTION:** Never execute `run_extraction_v*.py` scripts, even with `--dry-run`. These scripts trigger expensive provider preflight probes that consume significant credits.
docs/03-reference/instructions/gemini.md:17 — - **NO LIVE RUNNER EXECUTION:** Never execute `run_extraction_v*.py` scripts, even with `--dry-run`. These scripts trigger expensive provider preflight probes that consume significant credits.
docs/03-reference/systems/gpt-researcher/enhanced-pipeline.md:134 — results = await extractor.run_extraction()
docs/05-audit-reports/rte-gemini-deep-pal-audit-2026-04-23.md:33 — - **Shadow Paths:** Multiple legacy runtimes (`v3`, `v4`, `run_extraction.py`) are still present in the directory. While not active in the v5 flow, they create potential for operator confusion and accidental invocation of unpatched logic.
docs/05-audit-reports/rte-gemini-deep-pal-audit-2026-04-23.md:70 — | CA-002 | LOW | Move legacy scripts (v3, v4, run_extraction.py) to `archive/`. | Low |
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:588 — - **NOT_RUN:** The [S6-OBS-3] dashboard-snapshot key-presence assertion (read-only audit contract; runtime construction not permitted). Human-verify command given inline. No `run_extraction_v*` / prescan / probe / LLM / network calls were m …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1441 — Key finding so far: `rte_config.py:126` (observed) sets `RUNNER_SCRIPT = CONFIG_FILE.with_name("run_extraction_v5.py")` — so v5 is the canonical runtime engine, and `run_extraction.py` (root, 400 lines) is a legacy stub that raises `NotImpl …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1479 — **Shadow / legacy:** `run_extraction_v3.py` (12,106 lines, identical docstring to v5 → v5 is its fork). Has its own live `--execute` path gated by `DPMX_LIVE_OK` (v3:11247-11251) and its own `RUNNER_SCRIPT=__file__` (v3:159). In non-test ru …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:201 — The extraction stage is in `.extraction` (`run_extraction`, line 13/62). That's where the live gating and per-phase confirmation live. Let me inspect the extraction stage module.
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:273 — - **`run_extraction.py`** (bare) = **dead/shadow**. Raises `NotImplementedError` on live (run_extraction.py:272); zero non-test consumers. Do not treat as authority.
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:284 — 1. **Three live runners, one engine.** v5 is terminal, but v3 (consent-gated, still imported by probe/repscan/tools) and the dead `run_extraction.py` coexist. Auditors touching v3 may mistake it for current behavior. Mitigation: treat ONLY  …[truncated]
claudedocs/rte-distributed-audit-2026-05-29.md:6 — **Posture:** **READ-ONLY.** No files modified, no `run_extraction_v*`/prescan/probe executed, no live LLM/network calls, no install scripts run. All execution-only checks are recorded as **NOT_RUN** with human-verify commands.
docs/04-explanation/branding/brand-rollout-plan-2026-04-21.md:240 — - Wire the runners (`run_extraction_v*.py`, `run_prescan.py`, `run_probe.py`) to emit events that the progress context consumes.
docs/archive/pipeline-v2/UPGRADE_legacy/readme-2.md:70 — - **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme-2.md:14 — Updated `run_extraction.py` with production-grade reliability:
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme-2.md:27 — - **Resume:** `python run_extraction.py --resume`
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme-2.md:58 — python UPGRADE/run_extraction.py
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme-2.md:63 — python UPGRADE/run_extraction.py --resume
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme-2.md:68 — python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme-2.md:73 — python UPGRADE/run_extraction.py --dry-run
docs/archive/pipeline-v2/UPGRADE_legacy/readme-3.md:70 — - **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order-2.md:45 — python UPGRADE/run_extraction.py --phases priority
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order-2.md:69 — python UPGRADE/run_extraction.py --phases docs
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order-2.md:163 — python UPGRADE/run_extraction.py --dry-run --phases priority
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order-2.md:207 — python UPGRADE/run_extraction.py --phases code
docs/archive/pipeline-v2/UPGRADE_legacy/README.md:70 — - **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
docs/archive/pipeline-v2/UPGRADE_legacy/EXECUTION_ORDER.md:45 — python UPGRADE/run_extraction.py --phases priority
docs/archive/pipeline-v2/UPGRADE_legacy/EXECUTION_ORDER.md:69 — python UPGRADE/run_extraction.py --phases docs
docs/archive/pipeline-v2/UPGRADE_legacy/EXECUTION_ORDER.md:163 — python UPGRADE/run_extraction.py --dry-run --phases priority
docs/archive/pipeline-v2/UPGRADE_legacy/EXECUTION_ORDER.md:207 — python UPGRADE/run_extraction.py --phases code
docs/archive/pipeline-v2/UPGRADE_legacy/RUNNER_README.md:14 — Updated `run_extraction.py` with production-grade reliability:
docs/archive/pipeline-v2/UPGRADE_legacy/RUNNER_README.md:27 — - **Resume:** `python run_extraction.py --resume`
docs/archive/pipeline-v2/UPGRADE_legacy/RUNNER_README.md:58 — python UPGRADE/run_extraction.py
docs/archive/pipeline-v2/UPGRADE_legacy/RUNNER_README.md:63 — python UPGRADE/run_extraction.py --resume
docs/archive/pipeline-v2/UPGRADE_legacy/RUNNER_README.md:68 — python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
docs/archive/pipeline-v2/UPGRADE_legacy/RUNNER_README.md:73 — python UPGRADE/run_extraction.py --dry-run
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme.md:14 — Updated `run_extraction.py` with production-grade reliability:
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme.md:27 — - **Resume:** `python run_extraction.py --resume`
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme.md:58 — python UPGRADE/run_extraction.py
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme.md:63 — python UPGRADE/run_extraction.py --resume
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme.md:68 — python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
docs/archive/pipeline-v2/UPGRADE_legacy/runner-readme.md:73 — python UPGRADE/run_extraction.py --dry-run
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order.md:45 — python UPGRADE/run_extraction.py --phases priority
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order.md:69 — python UPGRADE/run_extraction.py --phases docs
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order.md:163 — python UPGRADE/run_extraction.py --dry-run --phases priority
docs/archive/pipeline-v2/UPGRADE_legacy/execution-order.md:207 — python UPGRADE/run_extraction.py --phases code
docs/archive/pipeline-v2/UPGRADE/readme-2.md:70 — - **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
docs/archive/pipeline-v2/UPGRADE/runner-readme-2.md:14 — Updated `run_extraction.py` with production-grade reliability:
docs/archive/pipeline-v2/UPGRADE/runner-readme-2.md:27 — - **Resume:** `python run_extraction.py --resume`
docs/archive/pipeline-v2/UPGRADE/runner-readme-2.md:58 — python UPGRADE/run_extraction.py
docs/archive/pipeline-v2/UPGRADE/runner-readme-2.md:63 — python UPGRADE/run_extraction.py --resume
docs/archive/pipeline-v2/UPGRADE/runner-readme-2.md:68 — python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
docs/archive/pipeline-v2/UPGRADE/runner-readme-2.md:73 — python UPGRADE/run_extraction.py --dry-run
docs/archive/pipeline-v2/UPGRADE/readme-3.md:70 — - **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
docs/archive/pipeline-v2/UPGRADE/execution-order-2.md:45 — python UPGRADE/run_extraction.py --phases priority
docs/archive/pipeline-v2/UPGRADE/execution-order-2.md:69 — python UPGRADE/run_extraction.py --phases docs
docs/archive/pipeline-v2/UPGRADE/execution-order-2.md:163 — python UPGRADE/run_extraction.py --dry-run --phases priority
docs/archive/pipeline-v2/UPGRADE/execution-order-2.md:207 — python UPGRADE/run_extraction.py --phases code
docs/archive/pipeline-v2/UPGRADE/README.md:70 — - **`run_extraction.py`** - 🚀 Automated runner script (Grok API)
docs/archive/pipeline-v2/UPGRADE/EXECUTION_ORDER.md:45 — python UPGRADE/run_extraction.py --phases priority
docs/archive/pipeline-v2/UPGRADE/EXECUTION_ORDER.md:69 — python UPGRADE/run_extraction.py --phases docs
docs/archive/pipeline-v2/UPGRADE/EXECUTION_ORDER.md:163 — python UPGRADE/run_extraction.py --dry-run --phases priority
docs/archive/pipeline-v2/UPGRADE/EXECUTION_ORDER.md:207 — python UPGRADE/run_extraction.py --phases code
docs/archive/pipeline-v2/UPGRADE/RUNNER_README.md:14 — Updated `run_extraction.py` with production-grade reliability:
docs/archive/pipeline-v2/UPGRADE/RUNNER_README.md:27 — - **Resume:** `python run_extraction.py --resume`
docs/archive/pipeline-v2/UPGRADE/RUNNER_README.md:58 — python UPGRADE/run_extraction.py
docs/archive/pipeline-v2/UPGRADE/RUNNER_README.md:63 — python UPGRADE/run_extraction.py --resume
docs/archive/pipeline-v2/UPGRADE/RUNNER_README.md:68 — python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
docs/archive/pipeline-v2/UPGRADE/RUNNER_README.md:73 — python UPGRADE/run_extraction.py --dry-run
docs/archive/pipeline-v2/UPGRADE/runner-readme.md:14 — Updated `run_extraction.py` with production-grade reliability:
docs/archive/pipeline-v2/UPGRADE/runner-readme.md:27 — - **Resume:** `python run_extraction.py --resume`
docs/archive/pipeline-v2/UPGRADE/runner-readme.md:58 — python UPGRADE/run_extraction.py
docs/archive/pipeline-v2/UPGRADE/runner-readme.md:63 — python UPGRADE/run_extraction.py --resume
docs/archive/pipeline-v2/UPGRADE/runner-readme.md:68 — python UPGRADE/run_extraction.py --checkpoint-file /path/to/backup.json
docs/archive/pipeline-v2/UPGRADE/runner-readme.md:73 — python UPGRADE/run_extraction.py --dry-run
docs/archive/pipeline-v2/UPGRADE/execution-order.md:45 — python UPGRADE/run_extraction.py --phases priority
docs/archive/pipeline-v2/UPGRADE/execution-order.md:69 — python UPGRADE/run_extraction.py --phases docs
docs/archive/pipeline-v2/UPGRADE/execution-order.md:163 — python UPGRADE/run_extraction.py --dry-run --phases priority
docs/archive/pipeline-v2/UPGRADE/execution-order.md:207 — python UPGRADE/run_extraction.py --phases code
services/dopemux-gpt-researcher/backend/README_ENHANCED_PIPELINE.md:116 — results = await extractor.run_extraction()

### SCRIPTS (0)
(none)

### ARTIFACTS (10)
task-packets/generated/TP-RTE-DOCS-CANON-008.json:121 — "rg -n \"rte|extractor|truth|upgrades|LegacyReplacementCommand|run_extraction|run_repscan|PipelineRunner\" src/dopemux/cli.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth- …[truncated]
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/03_RTE_SURFACE_MAP.md:13 — - OBSERVED additional legacy wrapper: `services/repo-truth-extractor/run_extraction.py` exists and should be audited for current relevance.
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md:15 — | Multiple legacy extraction runtimes remain (`run_extraction.py`, v3, v4, v5). | PARTIALLY_FIXED | `services/repo-truth-extractor/run_extraction_v3.py`, `run_extraction_v4.py`, `run_extraction_v5.py`, `proof/TP-RTE-V3-CONSENT-004/PROOF.jso …[truncated]
proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json:14 — "shadow_paths_identified": ["run_extraction_v3.py", "run_extraction_v4.py", "run_extraction.py"],
proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json:48 — "task": "Decommission or move legacy runtimes (v3, v4, run_extraction.py) to archive.",
proof/TP-RTE-DOCS-CANON-008/PROOF.json:65 — "command": "git diff --name-only | rg '^(src/|services/|config/|pyproject\\.toml|package-lock\\.json|uv\\.lock|.*promptsets|services/repo-truth-extractor/(run_extraction_v[345]\\.py|run_repscan\\.py|lib/batch_clients\\.py))'",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1056 — "services/repo-truth-extractor/run_extraction.py",
proof/rte_deep_audit_gemini_007.md:57 — 4.  **P2: Version Abstraction (RM-004/RM-005):** Standardize on `run_extraction.py` and move legacy scripts to `archive/`.
proof/rte_deep_audit_gemini_007_stage9_challenge.md:10 — - **Reversibility of RM-004:** Renaming `run_extraction_v5.py` to `run_extraction.py` (RM-004) is listed as P2, but it's actually **P0 for future-proofing**. Delaying this makes the next version upgrade (v6) twice as expensive due to the ac …[truncated]
proof/rte_deep_audit_gemini_007_stage9_synthesis.md:10 — | RM-004 | Filename-Based Versioning | MEDIUM | LOW | P2 | Rename `run_extraction_v5.py` to `run_extraction.py` and manage versions via configuration. |

### OTHER (31)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:17320 — services/repo-truth-extractor/run_extraction.py:35:    ".config/mcp",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:17321 — services/repo-truth-extractor/run_extraction.py:259:    # But we passed REPO_EXCLUDES which excludes 'src', 'services', 'docs', 'tests'
docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py:17 — python run_extraction.py --phases priority          # Run priority phases only
docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py:18 — python run_extraction.py --phases all               # Run everything
docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py:19 — python run_extraction.py --resume --phases priority  # Resume from checkpoint
docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py:20 — python run_extraction.py --dry-run                  # Test without API calls
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4538 — ./services/repo-truth-extractor/run_extraction.py
reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch:9261 — +    monkeypatch.setattr(gate, "load_module", lambda path, name: FakeRunner() if "run_extraction" in str(path) else type("FakeContract", (), {"compile_phase_contract_map": lambda self=None: {"steps": {}}, "write_phase_contract_map": lambda  …[truncated]
docs/03-reference/planes/pm/_evidence/PM-INV-00.outputs/30_src_dopemux_cli.py.nl.txt:4607 — 4607	            result = pipeline.run_extraction()
docs/03-reference/planes/pm/_evidence/PM-INV-00.outputs/30_src_dopemux_cli.py.nl.txt:4799 — 4799	            result = pipeline.run_extraction()
docs/archive/pipeline-v2/UPGRADE/run_extraction.py:17 — python run_extraction.py --phases priority          # Run priority phases only
docs/archive/pipeline-v2/UPGRADE/run_extraction.py:18 — python run_extraction.py --phases all               # Run everything
docs/archive/pipeline-v2/UPGRADE/run_extraction.py:19 — python run_extraction.py --resume --phases priority  # Resume from checkpoint
docs/archive/pipeline-v2/UPGRADE/run_extraction.py:20 — python run_extraction.py --dry-run                  # Test without API calls
docs/03-reference/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_cli.py.txt:4607 — 4607	            result = pipeline.run_extraction()
docs/03-reference/planes/pm/_evidence/PM-FRIC-01.outputs/nl_src_dopemux_cli.py.txt:4799 — 4799	            result = pipeline.run_extraction()
docs/03-reference/planes/pm/_evidence/PM-ADHD-02.outputs/nl_src_dopemux_cli.py.txt:4607 — 4607	            result = pipeline.run_extraction()
docs/03-reference/planes/pm/_evidence/PM-ADHD-02.outputs/nl_src_dopemux_cli.py.txt:4799 — 4799	            result = pipeline.run_extraction()
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1580 — diff --git a/docs/archive/pipeline-v2/UPGRADE/run_extraction.py b/docs/archive/pipeline-v2/UPGRADE/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1582 — --- a/docs/archive/pipeline-v2/UPGRADE/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1583 — +++ b/docs/archive/pipeline-v2/UPGRADE/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1601 — diff --git a/docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py b/docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1603 — --- a/docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:1604 — +++ b/docs/archive/pipeline-v2/UPGRADE_legacy/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7963 — diff --git a/services/repo-truth-extractor/run_extraction.py b/services/repo-truth-extractor/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7965 — --- a/services/repo-truth-extractor/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:7966 — +++ b/services/repo-truth-extractor/run_extraction.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:16388 — from .gemini.adapter import run_extraction_adapter
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:69 — docs/archive/pipeline-v2/UPGRADE/run_extraction.py |   3 +-
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:70 — .../pipeline-v2/UPGRADE_legacy/run_extraction.py   |   3 +-
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:382 — services/repo-truth-extractor/run_extraction.py    |   4 +-

**COUNT LINE**: RUNTIME:21 TESTS:6 CI:0 DOCS:81 SCRIPTS:0 ARTIFACTS:10 (OTHER:31)

---

## services/repo-truth-extractor/run_repscan.py (run_repscan / repscan)

Pattern: `repscan`

### RUNTIME (11)
src/dopemux/commands/extractor_commands.py:505 — def _run_repscan_runner(
src/dopemux/commands/extractor_commands.py:517 — runner = resolved_root / "services" / "repo-truth-extractor" / "run_repscan.py"
src/dopemux/cli.py:3263 — from .commands.extractor_commands import extractor, _run_extractor_runner, _run_repscan_runner
src/dopemux/cli.py:4888 — "repscan",
src/dopemux/cli.py:4909 — def repscan_passthrough(
src/dopemux/cli.py:4930 — def _build_repscan_args(
src/dopemux/cli.py:5072 — This command wraps `run_repscan.py`, which is part of the legacy v3
src/dopemux/cli.py:5085 — # Defense in depth: run_repscan.py independently requires --allow-legacy-v3-scan
src/dopemux/cli.py:5088 — _run_repscan_runner(
src/dopemux/cli.py:5089 — args=_build_repscan_args(
services/repo-truth-extractor/run_extraction_v3.py:110 — # profile. This legacy runner (used by run_repscan/run_probe) has no cost-profile

### TESTS (13)
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/tests/TEST_AND_CI_EVIDENCE.md:2666 — tests/unit/test_cli_repscan_passthrough.py
tests/unit/test_cli_repscan_passthrough.py:10 — def test_legacy_repscan_cli_is_disabled_with_canonical_replacement() -> None:
tests/unit/test_cli_repscan_passthrough.py:12 — with patch("dopemux.cli._run_repscan_runner") as mocked:
tests/unit/test_cli_repscan_passthrough.py:16 — "repscan",
tests/unit/test_cli_repscan_passthrough.py:34 — with patch("dopemux.cli._run_repscan_runner") as mocked:
tests/unit/test_cli_repscan_passthrough.py:57 — with patch("dopemux.cli._run_repscan_runner") as mocked:
services/repo-truth-extractor/tests/test_run_repscan.py:11 — RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_repscan.py"
services/repo-truth-extractor/tests/test_run_repscan.py:17 — spec = importlib.util.spec_from_file_location("run_repscan", RUNNER_PATH)
services/repo-truth-extractor/tests/test_run_repscan.py:36 — run_id = "repscan_v1_fixture"
services/repo-truth-extractor/tests/test_run_repscan.py:70 — def test_repscan_refuses_without_legacy_v3_opt_in(tmp_path: Path, monkeypatch) -> None:
services/repo-truth-extractor/tests/test_run_repscan.py:84 — "blocked_repscan",
services/repo-truth-extractor/tests/test_run_repscan.py:97 — raise AssertionError("run_repscan should require --allow-legacy-v3-scan")
services/repo-truth-extractor/tests/test_run_repscan.py:109 — run_id = "repscan_auto_fixture"

### CI (0)
(none)

### DOCS (24)
TASK_ORCH_MCP_PLUGIN_SURFACE.md:201 — - **DPMX_LIVE_OK consent gate**: [src/dopemux/cli.py:4906–4916](src/dopemux/cli.py#L4906) — duplicated check (cli.py + `run_repscan.py`); defense in depth. Pattern is reusable for any orchestrator T5+ operation.
claudedocs/rte-cost-profile-plan-b-design-2026-06-04.md:91 — Shipped: strict-cell profile values corrected to OpenAI-only (catalog says anthropic-via-OpenRouter is NOT `supports_json_schema_strict`, and the 57 CE/AGG steps require strict primary — user confirmed keeping strict cells OpenAI-only); str …[truncated]
claudedocs/rte-truth-program-2026-07/A3d-prompts-WXZ-promptgen.md:101 — - `render_promptset` and `run_sync` are invoked **only** from `tests/test_universal_extractor.py` (lines 699, 957–1041) and internally (`sync_engine.py:29` imports `render_promptset`). No production entrypoint (`run_extraction_v5.py`, `run_ …[truncated]
claudedocs/rte-truth-program-2026-07/A3d-prompts-WXZ-promptgen.md:116 — - `rte_promptset.py` (prompt_root → v4), `run_repscan.py`, `tests/test_universal_extractor.py`, `.github/workflows/ci-complete.yml`
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:30 — Now I have a critical finding. The authority map says v3 is referenced in non-test runtime "only by run_repscan.py, run_probe.py, tools/phase0_serialize_partitions.py". But I found **two more critical references the map missed**:
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:121 — Let me read the engine and check how the optimize-pass output (skip_list, model_routing_hints) is consumed downstream by the runner. Also `run_repscan.py` and `run_probe.py`.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:207 — Scope audited: `run_prescan.py`, `lib/prescan/*` (engine, code_prescan, batch_planner, classifier, duplicate_detector, cost_estimator, grok_passes, provider_catalog, token_counter, models, schemas), `lib/intelligence_router.py`, `run_repsca …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:278 — Runtime code (canonical, per Truth Order): `lib/prescan/*`, `lib/intelligence_router.py`, `run_extraction_v5.py`, `run_prescan.py`, `run_repscan.py`, `run_probe.py`. Schema (`lib/prescan/schemas.py`) treated as subordinate to engine output  …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:811 — Now let me read the two critical runner helpers (`_run_extractor_runner` at 481, `_run_repscan_runner` at 505) and the command bodies in `extractor_commands.py` that get aliased into `rte`. This is the core of the consent/execute gating ana …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1088 — Interesting — `repscan` is disabled and points to `dopemux rte scan` (cli.py:4824), but I noticed `rte` does NOT have a `scan` subcommand registered (lines 5596-5603 only register list/run/doctor/status/preflight/validate-live/trace/wizard) …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1090 — Let me check: (1) does `rte scan` exist (referenced by repscan refusal and run-prescan.md indirectly)? (2) The `extract truth-run` alias (line 4914 block + the extract group). (3) The `upgrades validate-live` import-origin gate vs README. L …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1092 — `rte scan` DOES exist — it's defined at cli.py:4958 via `@rte.command("scan", ...)`. Good, so the repscan refusal pointer is valid. Let me read the `rte scan` command (4958-5027) to understand what it does and whether it's a surprise-cost p …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1477 — - `run_repscan.py`, `run_probe.py`, `run_fl_int.py` — operator sub-tools layered on a runner.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1479 — **Shadow / legacy:** `run_extraction_v3.py` (12,106 lines, identical docstring to v5 → v5 is its fork). Has its own live `--execute` path gated by `DPMX_LIVE_OK` (v3:11247-11251) and its own `RUNNER_SCRIPT=__file__` (v3:159). In non-test ru …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:274 — - **`run_extraction_v3.py`** = independent legacy engine, **consent-gated** (`--execute` + `DPMX_LIVE_OK=1`, v3:11225-11234). "Legacy but still imported" — live non-test consumers exist: `run_probe.py`, `run_repscan.py`, `tools/phase0_seria …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:284 — 1. **Three live runners, one engine.** v5 is terminal, but v3 (consent-gated, still imported by probe/repscan/tools) and the dead `run_extraction.py` coexist. Auditors touching v3 may mistake it for current behavior. Mitigation: treat ONLY  …[truncated]
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:94 — - gated legacy scan: `dopemux rte scan --allow-legacy-v3-scan`, which delegates to `run_repscan.py` and the legacy v3 chain
docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md:153 — Evidence: `src/dopemux/cli.py` labels `dopemux upgrades` as a legacy compatibility alias for `dopemux rte`, blocks `dopemux extractor` through `LegacyReplacementCommand`, makes `dopemux truth` raise a refusal, and gates `dopemux rte scan` w …[truncated]
docs/audit/rte-opus-uiux-claude-design-audit/findings-ledger.md:237 — - Defense-in-depth comment at `cli.py:4916-4918` says `run_repscan.py` independently requires the same flag.
docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md:732 — | CLI-0057 | dopemux CLI | src/dopemux/cli.py | repscan_passthrough | cli_command | cli | support | dopemux operator control surface | cli_command | unknown | deferred | deferred | Do not imply authority; mark UNKNOWN or deferred. | src/dop …[truncated]
docs/05-audit-reports/repo-cli-system-recovery-tranche-2026-05-02.md:75 — `uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_cli_upgrades_commands.py`
reports/dopemux-cli-command-audit-2026-05-01.md:286 — | safe/session/shell-setup/theme/layouts/launch/dope/quick/task/wire-conport/extractpro/extract-chatlog/repscan/dashboard | 18 | Mixed helper, compatibility, and operational commands. |
reports/dopemux-cli-command-reference-2026-05-01.md:57 — | `repscan` | 1 | Dopemux local command module. | Mixed read/write behavior depends on subcommands; inspect leaf rows. |
reports/dopemux-cli-command-reference-2026-05-01.md:285 — | `dopemux repscan` | command | 🔬 Repository Audit: Run deterministic repo scan and prompt synthesis | executes local Python callback | `--phase; --run-id; --promptgen; --promptpack; --promptgen-only; --prompt-root; --profiles-dir; --legacy …[truncated]

### SCRIPTS (0)
(none)

### ARTIFACTS (108)
task-packets/TP-DMX-REPOHYG-007.json:35 — "uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_cli_upgrades_commands.py",
task-packets/TP-DMX-REPOHYG-007.json:127 — "uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_cli_upgrades_commands.py",
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:79 — "tests/unit/test_cli_repscan_passthrough.py",
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:96 — "pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py",
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:97 — "pre-commit run --files src/dopemux/cli.py src/dopemux/commands/extractor_commands.py tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py task-packets/RTE-UX-PKT …[truncated]
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:204 — "tests/unit/test_cli_repscan_passthrough.py",
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:220 — "git diff -- src/dopemux/cli.py src/dopemux/commands/extractor_commands.py tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py"
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:234 — "tests/unit/test_cli_repscan_passthrough.py",
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:275 — "pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py",
task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:344 — - `tests/unit/test_cli_repscan_passthrough.py` only for exact expected output
task-packets/generated/TP-RTE-DOCS-CANON-008.json:61 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:121 — "rg -n \"rte|extractor|truth|upgrades|LegacyReplacementCommand|run_extraction|run_repscan|PipelineRunner\" src/dopemux/cli.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth- …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:122 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:141 — "services/repo-truth-extractor/run_repscan.py"
task-packets/generated/TP-RTE-DOCS-CANON-008.json:149 — "Remaining dopemux upgrades, dopemux extractor, dopemux truth, direct runner, v3/v4, and run_repscan mentions must be classified according to runtime evidence.",
task-packets/generated/TP-RTE-DOCS-CANON-008.json:153 — "rg -n \"dopemux upgrades|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v3|run_extraction_v4|run_repscan|python services/repo-truth-extractor/run_extraction_v5.py\" README.md docs/00-MASTER-INDEX.md docs/02-how-to/extraction …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:164 — "No current operator doc presents dopemux upgrades, dopemux extractor, dopemux truth, direct runner invocation, v3, v4, or run_repscan as the primary v5 RTE operator path."
task-packets/generated/TP-RTE-V3-CONSENT-004.json:40 — "services/repo-truth-extractor/run_repscan.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:54 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:81 — "Inspect v5, v4, v3, run_repscan, dopemux CLI routing, and focused operator-safety tests."
task-packets/generated/TP-RTE-V3-CONSENT-004.json:162 — "Inspect run_repscan.py and dopemux rte scan wiring.",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:167 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_repscan.py services/repo-truth-extractor/tests/test_truth_run_cli.py"
task-packets/generated/TP-RTE-V3-CONSENT-004.json:171 — "services/repo-truth-extractor/run_repscan.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:172 — "services/repo-truth-extractor/tests/test_run_repscan.py",
task-packets/generated/TP-RTE-V3-CONSENT-004.json:176 — "dopemux rte scan refuses safely by default and direct run_repscan requires explicit legacy consent before delegation."
task-packets/generated/TP-RTE-V3-CONSENT-004.json:180 — "services/repo-truth-extractor/run_repscan.py"
task-packets/generated/TP-RTE-V3-CONSENT-004.json:198 — "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py",
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:70 — - legacy `dopemux repscan` replacement surface
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:79 — - `tests/unit/test_cli_repscan_passthrough.py`
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:86 — | legacy `repscan --phase` help | `📊 Target Phase: Phase code or ALL for the repo scan ritual.` | `Phase code or ALL for the legacy repo scan.` | Replacement/legacy scan guidance should be direct; removed ornamental emoji and ritual phrasin …[truncated]
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:87 — | legacy `repscan --run-id` help | `🆔 Ritual Session: Unique identifier for the scan run.` | `Scan run identifier.` | Run identifiers are operator controls; concise label is clearer. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:88 — | legacy `repscan --promptgen` help | `🧠 Prompt Synthesis: Mode for automated prompt generation.` | `Prompt generation mode.` | Removed ornamental label while preserving meaning. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:89 — | legacy `repscan --promptpack` help | `📦 Prompt Package: Specific promptpack to use for the ritual.` | `Prompt package to use.` | Removed ritual phrasing from operator help. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:90 — | legacy `repscan --promptgen-only` help | `⚡ Synthesis Only: Execute only the prompt generation phase.` | `Run only the prompt generation phase.` | Clear procedural instruction without decorative marker. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:91 — | legacy `repscan --prompt-root` help | `🔬 Prompt Source: Root directory for ritual prompts.` | `Root directory for prompts.` | Shorter, direct path guidance. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:92 — | legacy `repscan --profiles-dir` help | `📂 Profile Registry: Path to the ritual profiles directory.` | `Prompt profile directory.` | Removed ritual phrasing; preserved target meaning. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:93 — | legacy `repscan --legacy-runner` help | `⏪ Legacy Engine: Path to the legacy v3 runner.` | `Path to the legacy v3 runner.` | Removed ornamental emoji/label from legacy execution boundary. |
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:94 — | legacy `repscan` docstring | `🔬 Repository Audit: Run deterministic repo scan and prompt synthesis` / `Engages ... extraction rituals.` | `Run the legacy deterministic repo scan and prompt synthesis path.` / `This legacy command is disabl …[truncated]
out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md:199 — - PASS: `uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py`
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:157 — "services/repo-truth-extractor/run_repscan.py",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:240 — "services/repo-truth-extractor/run_repscan.py",
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:94 — - gated legacy scan: `dopemux rte scan --allow-legacy-v3-scan`, which delegates to `run_repscan.py` and the legacy v3 chain
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/21_SYSTEM_REPOTRUTHEXTRACTOR.md:153 — Evidence: `src/dopemux/cli.py` labels `dopemux upgrades` as a legacy compatibility alias for `dopemux rte`, blocks `dopemux extractor` through `LegacyReplacementCommand`, makes `dopemux truth` raise a refusal, and gates `dopemux rte scan` w …[truncated]
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/03_RTE_SURFACE_MAP.md:14 — - OBSERVED legacy scan wrapper: `services/repo-truth-extractor/run_repscan.py`; `dopemux rte scan` requires explicit `--allow-legacy-v3-scan`.
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/03_RTE_SURFACE_MAP.md:42 — - OBSERVED focused test themes include operator safety, promptset truth/linting, batch strict response format, strict passthrough attestations, prescan corpus/walker, v3 consent, run_repscan gating, phase contracts, and pre-live gate v25.
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/04_RTE_RUNTIME_POINTERS.md:28 — | legacy scan opt-in | `src/dopemux/cli.py:4884-4929`; `run_repscan.py:74-75` | v3 scan remains available only with explicit opt-in. |
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:65 — "services/repo-truth-extractor/run_repscan.py",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:195 — "services/repo-truth-extractor/run_repscan.py": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md:9 — | `dopemux rte scan` delegates to legacy v3 scan route. | PARTIALLY_FIXED | `proof/TP-RTE-V3-CONSENT-004/PROOF.json`, `src/dopemux/cli.py:4884-4929`, `services/repo-truth-extractor/run_repscan.py:74-75` | It is disabled by default and requi …[truncated]
proof/TP-DCP-0003/PROOF.json:100 — "stdout": "schemas/dcp/dcp_mutation_class.schema.json:5:  \"description\": \"REPO_VALIDATED tier vocabulary (T0-T6, TX, TU from approval_policy.yaml + policy.py) / PROVISIONAL for Dopetask and bridge postures. Classifies mutation posture an …[truncated]
proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json:85 — "tests/unit/test_cli_repscan_passthrough.py",
proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json:98 — "surface": "legacy repscan/rte scan option help",
proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json:102 — "surface": "legacy repscan docstring",
proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json:187 — "uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py",
proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json:204 — "command": "uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py",
proof/repo-cli-system-recovery-tranche-2026-05-02.proof.json:103 — "command": "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_cli_upgrades_commands.py",
proof/repo-cli-system-recovery-tranche-2026-05-02.proof.json:109 — "command": "uv run --frozen --extra test python -m pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_cli_upgrades_commands.py",
proof/TP-RTE-DOCS-CANON-008/PROOF.json:55 — "command": "python - <<'PY'\nfrom pathlib import Path\npaths = [Path('README.md'), Path('docs/00-MASTER-INDEX.md'), *Path('docs/02-how-to/extraction').glob('*.md'), Path('docs/03-reference/extraction/pipeline-reliability.md'), *Path('docs/0 …[truncated]
proof/TP-RTE-DOCS-CANON-008/PROOF.json:65 — "command": "git diff --name-only | rg '^(src/|services/|config/|pyproject\\.toml|package-lock\\.json|uv\\.lock|.*promptsets|services/repo-truth-extractor/(run_extraction_v[345]\\.py|run_repscan\\.py|lib/batch_clients\\.py))'",
proof/TP-RTE-DOCS-CANON-008/PROOF.json:125 — "Remaining mentions of `dopemux extractor`, `dopemux truth`, `dopemux extract truth-run`, `PipelineRunner`, `run_repscan`, v3, and direct runner invocation include legacy, compatibility, deprecated, refusal, gated, advanced, debug, manual,  …[truncated]
proof/TP-RTE-DOCS-CANON-008/IMPLEMENTER_REPORT.md:6 — - Reclassified `dopemux upgrades`, `dopemux extractor`, `dopemux truth`, hidden `dopemux extract truth-run`, v3/v4, `run_repscan.py`, and direct runner usage according to runtime evidence.
proof/TP-RTE-DOCS-CANON-008/IMPLEMENTER_REPORT.md:31 — - `services/repo-truth-extractor/run_repscan.py`
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:135 — "services/repo-truth-extractor/run_repscan.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:16 — "services/repo-truth-extractor/run_repscan.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:18 — "services/repo-truth-extractor/tests/test_run_repscan.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:30 — "F1-HIGH-2": "Narrowed/addressed for the inspected route: dopemux rte scan refuses by default before launching run_repscan.py, and run_repscan.py itself requires --allow-legacy-v3-scan before creating v3 scan artifacts or delegating to v3."
proof/TP-RTE-V3-CONSENT-004/PROOF.json:36 — "run_repscan.py created v3 run artifacts and delegated to run_extraction_v3.py without a wrapper-level legacy opt-in.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:37 — "dopemux rte scan called run_repscan.py without an operator-facing legacy-v3 refusal."
proof/TP-RTE-V3-CONSENT-004/PROOF.json:45 — "dopemux rte scan refuses by default; explicit --allow-legacy-v3-scan is required before invoking run_repscan.py.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:46 — "run_repscan.py also refuses by default without --allow-legacy-v3-scan, so direct wrapper invocation cannot silently enter the v3 scan route."
proof/TP-RTE-V3-CONSENT-004/PROOF.json:85 — "command": "RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:95 — "command": "pre-commit run --files services/repo-truth-extractor/run_extraction_v3.py services/repo-truth-extractor/run_repscan.py services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/tes …[truncated]
proof/TP-RTE-V3-CONSENT-004/PROOF.json:102 — "services/repo-truth-extractor/tests/test_run_repscan.py",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:114 — "run_repscan.py remains a legacy v3 wrapper when --allow-legacy-v3-scan is explicitly supplied; this packet blocks silent use but does not replace it with a v5 scan implementation.",
proof/TP-RTE-V3-CONSENT-004/PROOF.json:120 — "Whether every external operator practice has stopped using direct run_repscan.py is UNKNOWN; direct run_repscan.py now fails closed unless explicitly opted in."
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:10 — - `dopemux rte scan` and direct `run_repscan.py` now refuse by default unless `--allow-legacy-v3-scan` is explicit.
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:14 — - Runtime authority: `services/repo-truth-extractor/run_extraction_v5.py`, `run_extraction_v4.py`, `run_extraction_v3.py`, `run_repscan.py`, `src/dopemux/cli.py`, and `src/dopemux/commands/extractor_commands.py`.
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:23 — - `services/repo-truth-extractor/run_repscan.py`
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:25 — - `services/repo-truth-extractor/tests/test_run_repscan.py`
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:41 — - `run_repscan.py` refuses by default and requires `--allow-legacy-v3-scan`.
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:52 — - `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py`: exit 0, 2 …[truncated]
proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md:60 — - `F1-HIGH-2`: narrowed/addressed for the inspected `dopemux rte scan` and `run_repscan.py` paths by default refusal plus explicit legacy opt-in.
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:179 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:323 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:373 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:474 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:735 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:775 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1444 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1483 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2099 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2210 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2260 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2418 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2433 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2448 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2463 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2588 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2651 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2676 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2689 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2726 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2768 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2811 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:3186 — "pytest -q tests/unit/test_cli_audit_remediations.py tests/unit/test_cli_repscan_passthrough.py",
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:280 — services/repo-truth-extractor/tests/test_run_repscan.py ...              [ 83%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-002/pytest_full_run.txt:242 — services/repo-truth-extractor/tests/test_run_repscan.py ...              [ 84%]
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-FULLSUITE-REPAIR-001/pytest_full_run_post_repair.txt:242 — services/repo-truth-extractor/tests/test_run_repscan.py ...              [ 84%]

### OTHER (33)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8945 — services/repo-truth-extractor/tests/test_run_repscan.py:18:    assert spec is not None and spec.loader is not None
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8946 — services/repo-truth-extractor/tests/test_run_repscan.py:56:    assert rc == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8947 — services/repo-truth-extractor/tests/test_run_repscan.py:59:    assert (run_root / "00_inputs" / "REPO_FINGERPRINT.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8948 — services/repo-truth-extractor/tests/test_run_repscan.py:60:    assert (run_root / "00_inputs" / "BUILD_SURFACE.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8949 — services/repo-truth-extractor/tests/test_run_repscan.py:61:    assert (run_root / "00_inputs" / "ENTRYPOINT_CANDIDATES.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8950 — services/repo-truth-extractor/tests/test_run_repscan.py:62:    assert (run_root / "00_inputs" / "DEPENDENCY_GRAPH_HINTS.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8951 — services/repo-truth-extractor/tests/test_run_repscan.py:63:    assert (run_root / "00_inputs" / "ARCHETYPES.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8952 — services/repo-truth-extractor/tests/test_run_repscan.py:64:    assert (run_root / "PROFILE_SELECTION.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8953 — services/repo-truth-extractor/tests/test_run_repscan.py:65:    assert (run_root / "promptpacks" / "PROMPTPACK.v1.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8954 — services/repo-truth-extractor/tests/test_run_repscan.py:66:    assert (run_root / "promptpacks" / "PROMPTPACK.v1.sha256.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8955 — services/repo-truth-extractor/tests/test_run_repscan.py:67:    assert (run_root / "RUN_PROMPTPACK_FINGERPRINT.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8956 — services/repo-truth-extractor/tests/test_run_repscan.py:95:        assert exc.code == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8957 — services/repo-truth-extractor/tests/test_run_repscan.py:97:        raise AssertionError("run_repscan should require --allow-legacy-v3-scan")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8958 — services/repo-truth-extractor/tests/test_run_repscan.py:99:    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8959 — services/repo-truth-extractor/tests/test_run_repscan.py:160:    assert rc == 0
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8960 — services/repo-truth-extractor/tests/test_run_repscan.py:161:    assert len(calls) == 2
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8961 — services/repo-truth-extractor/tests/test_run_repscan.py:162:    assert "--coverage-report" not in calls[0]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8962 — services/repo-truth-extractor/tests/test_run_repscan.py:163:    assert "--coverage-report" in calls[1]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8963 — services/repo-truth-extractor/tests/test_run_repscan.py:164:    assert (run_root / "promptpacks" / "PROMPTPACK.v2.json").exists()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:8964 — services/repo-truth-extractor/tests/test_run_repscan.py:165:    assert (run_root / "promptpacks" / "PROMPT_ADJUSTMENTS.json").exists()
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3031 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:17264:task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md:97:      "pre-commit run --files src/dopemux/cli.py src/dopemux/commands/extractor_commands.py tests/unit/test_cli_upgrades_com …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3964 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:23704:task-packets/generated/TP-RTE-DOCS-CANON-008.json:149:        "Remaining dopemux upgrades, dopemux extractor, dopemux truth, direct runner, v3/v4, and run_repscan mentions must be c …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:3965 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:23705:task-packets/generated/TP-RTE-DOCS-CANON-008.json:164:        "No current operator doc presents dopemux upgrades, dopemux extractor, dopemux truth, direct runner invocation, v3, v4, …[truncated]
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt:4031 — audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt:24960:task-packets/generated/TP-RTE-V3-CONSENT-004.json:81:        "Inspect v5, v4, v3, run_repscan, dopemux CLI routing, and focused operator-safety tests."
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4545 — ./services/repo-truth-extractor/run_repscan.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4709 — ./services/repo-truth-extractor/tests/test_run_repscan.py
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:6063 — ./tests/unit/test_cli_repscan_passthrough.py
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2444 — services/repo-truth-extractor/run_repscan.py       |     8 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2423 — services/repo-truth-extractor/run_repscan.py       |     8 -
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:8028 — diff --git a/services/repo-truth-extractor/tests/test_run_repscan.py b/services/repo-truth-extractor/tests/test_run_repscan.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:8030 — --- a/services/repo-truth-extractor/tests/test_run_repscan.py
reports/work-recovery/2026-03-05/stashes/stashat__2___patch.diff:8031 — +++ b/services/repo-truth-extractor/tests/test_run_repscan.py
reports/work-recovery/2026-03-05/stashes/stashat__2___stat.txt:387 — .../repo-truth-extractor/tests/test_run_repscan.py |   2 +-

**COUNT LINE**: RUNTIME:11 TESTS:13 CI:0 DOCS:24 SCRIPTS:0 ARTIFACTS:108 (OTHER:33)

---

## services/repo-truth-extractor/run_prescan.py (run_prescan only)

Pattern: `run_prescan`

### RUNTIME (5)
services/repo-truth-extractor/run_prescan.py:8 — python run_prescan.py \\
services/repo-truth-extractor/benchmarking/registry/registry_loader.py:215 — SERVICE_ROOT / "run_prescan.py",
services/repo-truth-extractor/benchmarking/registry/registry_loader.py:382 — prompt_inventory_refs=["services/repo-truth-extractor/run_prescan.py"],
services/repo-truth-extractor/benchmarking/registry/registry_loader.py:508 — "services/repo-truth-extractor/run_prescan.py",
services/repo-truth-extractor/benchmarking/executors/prescan_adapter.py:10 — SCRIPT = Path(__file__).resolve().parents[2] / "run_prescan.py"

### TESTS (2)
services/repo-truth-extractor/tests/test_task_scoring.py:37 — executor_links={"script": "run_prescan.py"},
services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py:398 — def test_doctor_preflight_and_auth_doctor_do_not_run_prescan_or_create_run_artifacts(

### CI (0)
(none)

### DOCS (28)
llm-plans/RTE_V5_FULL_PRESCAN_INTEGRATION_PLAN.md:15 — - `services/repo-truth-extractor/run_prescan.py`
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:207 — Scope audited: `run_prescan.py`, `lib/prescan/*` (engine, code_prescan, batch_planner, classifier, duplicate_detector, cost_estimator, grok_passes, provider_catalog, token_counter, models, schemas), `lib/intelligence_router.py`, `run_repsca …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:255 — - **[S3-08] LOW — `run_prescan.py --no-code/--no-git/--no-cost-estimate/--no-batch-mode` flags are dead (paired `store_true` defaults make the positive flag always True)**
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:256 — - files: `run_prescan.py:70-129` (`--code default=True`, `--git default=True`, `--cost-estimate default=True`, `--batch-mode default=True`), `:183-188` (config uses `args.code and not args.no_code`, etc.)
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:259 — - falsifying check: `python run_prescan.py --help` and confirm both `--code` and `--no-code` exist with `--code` defaulting enabled; then verify `--no-code` flips `enable_code_prescan` False. Already consistent with code at `:183`.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:278 — Runtime code (canonical, per Truth Order): `lib/prescan/*`, `lib/intelligence_router.py`, `run_extraction_v5.py`, `run_prescan.py`, `run_repscan.py`, `run_probe.py`. Schema (`lib/prescan/schemas.py`) treated as subordinate to engine output  …[truncated]
docs/02-how-to/extraction/run-prescan.md:50 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:68 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:80 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:85 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:90 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:99 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:114 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:136 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:151 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:204 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:211 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:220 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:229 — python run_prescan.py \
docs/02-how-to/extraction/run-prescan.md:239 — python run_prescan.py \
docs/03-reference/extraction/prescan-pipeline.md:308 — python run_prescan.py \
docs/03-reference/extraction/prescan-pipeline.md:344 — python run_prescan.py --repo-root . --no-git
docs/90-adr/rte-cost-profiles-and-optimizer-wiring.md:99 — - **Pre-existing test failures** on `test_run_extraction_v5_operator_safety.py::test_doctor_preflight_and_auth_doctor_do_not_run_prescan_or_create_run_artifacts` were observed during validation. Not caused by this change; flagged for a sepa …[truncated]
docs/03-reference/systems/repo-truth-extractor/benchmark-storage-contract.md:91 — - `services/repo-truth-extractor/run_prescan.py`
docs/03-reference/systems/repo-truth-extractor/benchmark-storage-contract.md:185 — - `run_prescan.py --dry-run` against the small repo fixture
docs/04-explanation/branding/brand-rollout-plan-2026-04-21.md:211 — Surface: a live progress panel shown while `run_extraction_v5.py`, `run_prescan.py`, and `run_probe.py` execute. Suppressed in non-TTY contexts; falls back to `brand_log` lines.
docs/04-explanation/branding/brand-rollout-plan-2026-04-21.md:240 — - Wire the runners (`run_extraction_v*.py`, `run_prescan.py`, `run_probe.py`) to emit events that the progress context consumes.
docs/04-explanation/branding/design-system-audit-2026-04-21.md:124 — | 16 | `services/repo-truth-extractor/` | [services/repo-truth-extractor/](../services/repo-truth-extractor/) | **No operator surface yet.** Entry points are CLI runners (`run_extraction_v5.py`, `run_prescan.py`, `run_probe.py`). Output is  …[truncated]

### SCRIPTS (0)
(none)

### ARTIFACTS (22)
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:134 — "services/repo-truth-extractor/run_prescan.py",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:156 — "services/repo-truth-extractor/run_prescan.py",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:239 — "services/repo-truth-extractor/run_prescan.py",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:64 — "services/repo-truth-extractor/run_prescan.py",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:194 — "services/repo-truth-extractor/run_prescan.py": "runtime",
proof/pr_merge/run_20260418_111828/pr/480/traces/STATE_RECOMPUTE_REPORT.json:260 — "path": "services/repo-truth-extractor/run_prescan.py",
proof/pr_merge/run_20260418_111828/pr/480/traces/STATE_RECOMPUTE_REPORT.json:554 — "path": "services/repo-truth-extractor/run_prescan.py",
proof/pr_merge/run_20260418_111828/pr/480/traces/CLOSED_LOOP_TRACE.json:277 — "path": "services/repo-truth-extractor/run_prescan.py",
proof/pr_merge/run_20260418_111828/pr/480/traces/CLOSED_LOOP_TRACE.json:571 — "path": "services/repo-truth-extractor/run_prescan.py",
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:518 — _ test_doctor_preflight_and_auth_doctor_do_not_run_prescan_or_create_run_artifacts _
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:519 — services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py:399: in test_doctor_preflight_and_auth_doctor_do_not_run_prescan_or_create_run_artifacts
proof/rte-cost-profile-redesign/TP-RTE-COSTPROFILE-F-VERIFY-001/pytest_full_run.txt:578 — FAILED services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py::test_doctor_preflight_and_auth_doctor_do_not_run_prescan_or_create_run_artifacts
proof/repo-remaining-work-disposition-2026-05-02.proof.json:1398 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1197 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1234 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1627 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1655 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1712 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1779 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:1859 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:2148 — "services/repo-truth-extractor/run_prescan.py",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:3245 — "services/repo-truth-extractor/run_prescan.py",

### OTHER (19)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13183 — services/repo-truth-extractor/run_prescan.py:11:        --passes dedup,discover,feasibility,optimize \\
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13184 — services/repo-truth-extractor/run_prescan.py:32:# Canonical ordered pass list — used both as the CLI default and for '--passes all'
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13185 — services/repo-truth-extractor/run_prescan.py:57:    # Passes
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13186 — services/repo-truth-extractor/run_prescan.py:59:        "--passes",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13187 — services/repo-truth-extractor/run_prescan.py:63:            "Comma-separated grok passes to run. "
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13188 — services/repo-truth-extractor/run_prescan.py:64:            "Use 'none' to skip all passes, or 'all' to run every pass. "
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13189 — services/repo-truth-extractor/run_prescan.py:141:        help="Skip expensive operations (no grok passes, no git enrichment)",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13190 — services/repo-truth-extractor/run_prescan.py:194:    # Parse passes — special-case 'none' and 'all' before CSV split
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13191 — services/repo-truth-extractor/run_prescan.py:195:    _passes_raw = (args.passes or "").strip().lower()
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13192 — services/repo-truth-extractor/run_prescan.py:196:    if _passes_raw in ("none", ""):
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13193 — services/repo-truth-extractor/run_prescan.py:197:        passes: list[str] = []
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13194 — services/repo-truth-extractor/run_prescan.py:198:    elif _passes_raw == "all":
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13195 — services/repo-truth-extractor/run_prescan.py:199:        passes = list(ALL_PASSES)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13196 — services/repo-truth-extractor/run_prescan.py:201:        passes = [p.strip().lower() for p in args.passes.split(",") if p.strip()]
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13197 — services/repo-truth-extractor/run_prescan.py:207:        passes = []
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13198 — services/repo-truth-extractor/run_prescan.py:208:        logger.info("🏜️  DRY RUN: Skipping code, git, and grok passes")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13199 — services/repo-truth-extractor/run_prescan.py:212:    logger.info(f"   Passes: {', '.join(passes) if passes else 'none'}")
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13200 — services/repo-truth-extractor/run_prescan.py:219:    result = engine.run(passes=passes, incremental=args.incremental)
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4543 — ./services/repo-truth-extractor/run_prescan.py

**COUNT LINE**: RUNTIME:5 TESTS:2 CI:0 DOCS:28 SCRIPTS:0 ARTIFACTS:22 (OTHER:19)

---

## prompts/ subdirs: prompts/v3, phase_fl_int, phase_s, phase_s_int, prompts/prescan

Pattern: `prompts/v3|phase_fl_int|phase_s_int|prompts/phase_s\b|prompts/prescan`

### RUNTIME (6)
services/repo-truth-extractor/s_int/run_s_int.py:23 — return _service_root() / "prompts" / "phase_s_int"
services/repo-truth-extractor/benchmarking/registry/seed_records.py:292 — "phase_fl_int_registry.json",
services/repo-truth-extractor/benchmarking/registry/registry_loader.py:432 — prompt_inventory_refs=["services/repo-truth-extractor/prompts/phase_s/PROMPT_SP11_CONTRACT_LINTER.md"],
services/repo-truth-extractor/benchmarking/registry/registry_loader.py:509 — "services/repo-truth-extractor/prompts/phase_s/registry.json",
services/repo-truth-extractor/fl_int/run_fl_int.py:26 — return _service_root() / "prompts" / "phase_fl_int"
services/repo-truth-extractor/fl_int/models.py:11 — REGISTRY_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "phase_fl_int"

### TESTS (19)
tests/unit/test_repo_truth_extractor_prompt_governance.py:151 — "FL_INT": SERVICE_ROOT / "prompts" / "phase_fl_int" / "registry.json",
tests/unit/test_repo_truth_extractor_prompt_governance.py:152 — "S_INT": SERVICE_ROOT / "prompts" / "phase_s_int" / "registry.json",
tests/unit/test_repo_truth_extractor_prompt_governance.py:242 — assert "services/repo-truth-extractor/prompts/phase_s/registry.json" in validator_suite.source_files
tests/unit/test_run_extraction_v3_phase_m.py:67 — prompt_files = sorted((Path("services/repo-truth-extractor/prompts/v3")).glob("PROMPT_M*.md"))
services/repo-truth-extractor/tests/test_s_int_prompt_contracts.py:9 — prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_s_int"
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:192 — def test_phase_s_int_audit_passes() -> None:
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:193 — """Verify phase_s_int audit passes with current state."""
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:196 — result = module._audit_phase_s_int(root)
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:204 — def test_phase_fl_int_audit_passes() -> None:
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:205 — """Verify phase_fl_int audit passes with current state."""
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:208 — result = module._audit_phase_fl_int(root)
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:232 — for pop in ["v4", "phase_s", "phase_s_int", "phase_fl_int", "prescan"]:
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:242 — assert results["phase_s_int"]["prompt_count"] == 5
services/repo-truth-extractor/tests/test_promptset_v4_lint.py:243 — assert results["phase_fl_int"]["prompt_count"] == 8
services/repo-truth-extractor/tests/test_registry_unified_contracts.py:9 — "FL_INT": SERVICE_ROOT / "prompts" / "phase_fl_int" / "registry.json",
services/repo-truth-extractor/tests/test_registry_unified_contracts.py:10 — "S_INT": SERVICE_ROOT / "prompts" / "phase_s_int" / "registry.json",
services/repo-truth-extractor/tests/test_fl_int_prompt_contracts.py:11 — prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_fl_int"
services/repo-truth-extractor/tests/test_fl_int_standalone_runner.py:21 — / "phase_fl_int"
services/repo-truth-extractor/tests/test_snapshot_capture.py:39 — assert "services/repo-truth-extractor/prompts/phase_s/registry.json" in validator_suite.source_files

### CI (0)
(none)

### DOCS (62)
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:69 — 2. `prompts/phase_s/registry.json` declares phase `SP` with steps SP0-SP12 (13 steps), files `PROMPT_SP*.md`
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:70 — 3. `prompts/phase_s_int/registry.json` declares some phase with S16-S20
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:74 — Now let me look at the actual prompt content for fabrication-risk "legacy context" blocks, and check `phases.py` for `REQUIRED_PROMPT_STEP_IDS`, and the phase_s_int registry.
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:79 — 2. `prompts/phase_s/registry.json` declares phase `SP` (SP0-SP12) — but `phase_s_registry_dir` (rte_promptset.py:65-76) resolves the SP registry FROM the `phase_s` directory. So phase "S" in registry mode resolves SP prompts. There's an int …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:288 — I have the three core files. The authority map flagged a "registry-bootstrapping paradox" and a separate Phase S/SP registry (`prompts/phase_s/registry.json`). Let me verify the registry files and how the wrappers connect to runtime (v5) an …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:293 — 2. The **`prompts/phase_s/registry.json`** declares `"phase": "SP"` but lives in a directory named `phase_s`, and the docs are split: `PHASE_S_SYSTEM_TRUTHS_GPT52.md` describes Phase S steps S1/S2, while the registry/prompts inside are all  …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:309 — **The paradox**: `resolve_phase_s_prompts` (Phase S, "registry" mode) loads `load_phase_s_registry()` — which loads `prompts/phase_s/registry.json` declaring `phase: "SP"` with steps `SP0..SP12`. So when Phase **S** runs in registry mode, i …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:316 — - **Phase SP** = registry pipeline prompts (SP0..SP12 from `prompts/phase_s/registry.json`)
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:326 — Let me verify the remaining coupling questions: (1) what `S_PROMPTS_MODES` allows and whether `registry` is a valid value for Phase S; (2) the `_validate_s_steps` constraint (S0-S12 only) vs registry returning SP* — does selecting `--s-step …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:338 — Let me verify: (1) whether SP4/SP5/etc. are in `repo_truth_map.json` under phase "SP" (so their contracts resolve), and whether phase "S" steps S0-S12 exist there too; (2) confirm v4 S-prompts exist so legacy mode works. Then check the regi …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:366 — **Scope audited:** `phases.py`, `rte_phase_wrappers.py`, `PHASE_*.md` (all 8), plus the coupling surfaces required to verify them: `rte_promptset.py` (registry resolution), `run_extraction_v5.py` (phase dispatch, prompt resolution, step fil …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:368 — **Authority-map claims I verified as TRUE:** (a) `phases.py` is canonical for phase IDs/dirs/DAG/`REQUIRED_PROMPT_STEP_IDS` and v5 imports it directly (v5:58, 185+); (b) Phase S/SP use a separate registry `prompts/phase_s/registry.json` dec …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:373 — - files: `run_extraction_v5.py:6612-6618` (`get_phase_prompts("S")` → `_resolve_phase_s_prompts(get_active_s_prompts_mode())`); `rte_promptset.py:311-352` (`resolve_phase_s_prompts`: legacy → `legacy_phase_prompt_specs("S")`; else loads SP  …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:390 — - **[S4-HIGH-2] HIGH — Registry/dir naming inversion: directory `prompts/phase_s/` and functions `phase_s_registry_dir`/`load_phase_s_registry`/`validate_phase_s_registry` all say "S", but the payload and every error message assert `phase = …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:391 — - files: `rte_promptset.py:65-76` (`phase_s_registry_dir` → `…/phase_s`), `:79-89` (`phase_s_registry_path` → `phase_s/registry.json`), `:212-226` (`validate_phase_s_registry` requires `payload["phase"] == "SP"` and version=1), `:224` error …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:394 — - falsifying check: `grep '"phase"' prompts/phase_s/registry.json` returns `"phase": "SP"` while the dir is `phase_s` — already confirmed; disproof would require the file to declare `"phase": "S"` (it does not).
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:397 — - files: `phases.py:152-166` (S: required `("R",)`, optional `("X","T","Z","MANUAL")`; SP: required `("R",)`, optional `("X","T","Z")`); `rte_phase_wrappers.py:296-320` (`plan_s_phase` hard-reads `dirs["R"]/norm`, then `extend_input_sources …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:409 — - files: `rte_promptset.py:212-272` (validator checks: version==1, phase=="SP", `observed == expected` step set, `prompt_path` relative + within root + exists, `routing_tier` ∈ valid tiers, `outputs` non-empty list — **no validation of `inp …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:412 — - falsifying check: temporarily set `prompts/phase_s/registry.json` `SP5.prior_step_ids = ["SP99"]` (nonexistent) in a scratch copy and run `validate_phase_s_registry` — if it raises, dependency validation exists and this is disproven. (NOT …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:771 — - evidence: observed. Repo-wide grep for `repo-truth-extractor/archive`, `legacy_artifact_gates`, and `R_REQUIRED_ARTIFACT_GROUPS` returns **no** runtime reference to these files: the `R_REQUIRED_ARTIFACT_GROUPS` symbol is defined fresh in  …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1452 — Let me confirm two fragmentation risks before writing: (1) the v3-vs-v5 duplicated-docstring fork and whether v3 has a live `__main__` that could still be invoked, and (2) the prompt-truth split (base_prompts vs prompts/v3 vs promptsets/v4/ …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1460 — 3. **Prompt-truth precedence is layered** (observed `rte_promptset.py:9-23`): env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` > legacy `UPGRADES_PROMPT_ROOT` > `promptsets/v4/prompts/` (if exists) > `prompts/v3/`. Phase S/SP has a *separate* registr …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1483 — **Where prompt + registry truth lives** (resolution order, `rte_promptset.py:9-23`): env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` → legacy `UPGRADES_PROMPT_ROOT` → `promptsets/v4/prompts/` (if present) → `prompts/v3/`. Phase S/SP uses a *separate …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1488 — 3. **Multi-rooted prompt truth.** Prompt content can resolve from env override, `promptsets/v4/prompts/`, or `prompts/v3/`, while Phase S/SP forks to a JSON registry. The `promptset_sha256` fingerprint (rte_promptset.py:528-579) only pins w …[truncated]
claudedocs/rte-truth-program-2026-07/A3d-prompts-WXZ-promptgen.md:32 — | PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS | 5 | 5 | 5 | 4 | 5 | Merge+README+QA. Procedure step 3 emits `FREEZE_CHECKSUMS` but output list is `FREEZE_MANIFEST/README/QA` (DEF-4). Legacy Context references **v3** prompt corpus path (`prompts/v …[truncated]
claudedocs/rte-truth-program-2026-07/A3d-prompts-WXZ-promptgen.md:43 — - **DEF-7 (LOW):** Z9 Legacy Context references the **v3** prompt corpus (`services/repo-truth-extractor/prompts/v3/PROMPT_*.md`) for fingerprinting — stale path now that v4 is canonical. Marked "intent only", so low impact, but update.
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:245 — Now I have the full picture. The task asked for "two registry.json files" but I found 4 registry.json files plus the promptset.yaml truth. v5 has its own complete engine (`main()` at 21502, `OperatorArgumentParser` at 1829) and does NOT del …[truncated]
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:258 — 4. else `prompts/v3` (line 23) ← legacy fallback
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:278 — Default resolution: env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` → legacy `UPGRADES_PROMPT_ROOT` → **`promptsets/v4/prompts/`** (default) → `prompts/v3/` (fallback).
claudedocs/rte-distributed-audit-SALVAGE-2026-05-28.md:280 — - **Internal-phase truth:** 4× `registry.json` — `prompts/{prescan,phase_s,phase_s_int,phase_fl_int}/registry.json` (prescan registry is governance-only; real prompts are Python constants in `lib/prescan/grok_passes.py`).
claudedocs/rte-distributed-audit-2026-05-29.md:44 — - **[S4-HIGH-2] HIGH** — Naming inversion: dir `prompts/phase_s/` + functions `*_phase_s_registry` all say "S", but the payload and every error message assert `phase=="SP"`; the co-located `PHASE_S_SYSTEM_TRUTHS_GPT52.md` documents Phase S. …[truncated]
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-3.md:50 — - `services/repo-truth-extractor/prompts/v3/`
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace-2.md:50 — - `services/repo-truth-extractor/prompts/v3/`
docs/90-adr/adr-218-repo-truth-extractor-hard-cutover-namespace.md:50 — - `services/repo-truth-extractor/prompts/v3/`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:63 — - Canonical phase-SP registry: `services/repo-truth-extractor/prompts/phase_s/registry.json`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:64 — - Canonical prescan governance registry: `services/repo-truth-extractor/prompts/prescan/registry.json`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:133 — | `services/repo-truth-extractor/prompts/phase_s/registry.json` | canonical | Governs SP post-review registry-driven prompts and outputs | Verified by `tests/unit/test_repo_truth_extractor_prompt_governance.py` |
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:134 — | `services/repo-truth-extractor/prompts/phase_s/PROMPT_SP11_CONTRACT_LINTER.md` | canonical | High-value launch-relevant contract-lint prompt referenced by registry and snapshot tests | Registry and validator-suite snapshot test reference  …[truncated]
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:135 — | `services/repo-truth-extractor/prompts/prescan/registry.json` | canonical_governance | Canonical governance metadata for prescan steps, schemas, and intended providers | Verified by `tests/unit/test_repo_truth_extractor_prompt_governance. …[truncated]
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:137 — | `services/repo-truth-extractor/prompts/phase_fl_int/registry.json` | compatibility | Present as a registry population checked by governance tests, but not demonstrated here as the canonical first-live runtime path | Governance test checks …[truncated]
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:138 — | `services/repo-truth-extractor/prompts/phase_s_int/registry.json` | compatibility | Same status as `phase_fl_int`; registry exists and is tested, but this packet does not prove it as the canonical pre-live path | Governance test checks pr …[truncated]
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:146 — - `services/repo-truth-extractor/prompts/prescan/registry.json` says prescan prompts are Python constants in `lib/prescan/grok_passes.py`; therefore the registry is governance metadata, not the canonical prompt text source
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:163 — 5. `services/repo-truth-extractor/prompts/phase_s/registry.json`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:164 — 6. `services/repo-truth-extractor/prompts/prescan/registry.json`
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:210 — | `services/repo-truth-extractor/prompts/phase_s/registry.json` | canonical_prompt_registry | Direct registry authority for SP prompt steps and outputs | yes |
docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md:211 — | `services/repo-truth-extractor/prompts/prescan/registry.json` | canonical_governance_registry | Governs prescan step metadata and explains registry-vs-runtime split | yes |
docs/03-reference/extraction/fl-int-postprocess.md:17 — - services/repo-truth-extractor/prompts/phase_fl_int/registry.json
docs/03-reference/extraction/fl-int-postprocess.md:38 — - `services/repo-truth-extractor/prompts/phase_fl_int/registry.json`
docs/03-reference/extraction/fl-int-postprocess.md:39 — - `services/repo-truth-extractor/prompts/phase_fl_int/schemas/`
docs/03-reference/extraction/fl-int-postprocess.md:203 — These two final object-shaped JSON outputs are governed by the standalone `phase_fl_int` schemas instead of the v4 artifact registry.
reports/work-recovery/2026-03-05/worktrees/fix-routing__untracked_snapshot/benchmark/prompts/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md:110 — - Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
docs/03-reference/systems/repo-truth-extractor/benchmark-storage-contract.md:88 — - `services/repo-truth-extractor/prompts/phase_s/registry.json`
services/repo-truth-extractor/README.md:390 — - v3 prompts: `services/repo-truth-extractor/prompts/v3/`
services/repo-truth-extractor/README.md:392 — - FL_INT standalone prompts: `services/repo-truth-extractor/prompts/phase_fl_int/`
tools/prompt_rewrite_v4/benchmark/prompts/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md:118 — - Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
services/repo-truth-extractor/prompts/v3/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md:12 — - Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md:85 — - Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q11_ARTIFACT_COLLISION_REPORT.md:20 — - `services/repo-truth-extractor/prompts/phase_s/registry.json`
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:78 — │    promptset.yaml (1076 lines)    │  prompts/v3/ (500+ files)          │
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:79 — │    artifacts.yaml (2113 lines)    │  prompts/phase_fl_int/ (8 files)   │
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:80 — │    model_map.yaml (3831 lines)    │  prompts/phase_s_int/ (5 files)    │
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:81 — │    prompts/ (500+ step files)     │  prompts/phase_s/ (standalone)     │

### SCRIPTS (20)
scripts/create_llm_archive.sh:52 — mkdir -p "${staging_root}/services/repo-truth-extractor/prompts/v3" \
scripts/create_llm_archive.sh:56 — find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_W*.md' -exec cp {} "${staging_root}/services/repo-truth-extractor/prompts/v3/" \;
scripts/create_llm_archive.sh:57 — find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_B*.md' -exec cp {} "${staging_root}/services/repo-truth-extractor/prompts/v3/" \;
scripts/create_llm_archive.sh:58 — find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_G*.md' -exec cp {} "${staging_root}/services/repo-truth-extractor/prompts/v3/" \;
scripts/create_llm_archive.sh:59 — find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_Q*.md' -exec cp {} "${staging_root}/services/repo-truth-extractor/prompts/v3/" \;
tools/prompt_rewrite_v4/fix_prompts.py:5 — files = glob.glob('services/repo-truth-extractor/prompts/v3/PROMPT_[CDR]*.md')
scripts/repo_truth_extractor_promptset_audit_v4.py:60 — choices=["v4", "phase_s", "phase_s_int", "phase_fl_int", "prescan", "all"],
scripts/repo_truth_extractor_promptset_audit_v4.py:721 — def _audit_phase_s_int(repo_root: Path) -> Dict[str, Any]:
scripts/repo_truth_extractor_promptset_audit_v4.py:724 — prompts_dir = repo_root / "services" / "repo-truth-extractor" / "prompts" / "phase_s_int"
scripts/repo_truth_extractor_promptset_audit_v4.py:752 — "population": "phase_s_int",
scripts/repo_truth_extractor_promptset_audit_v4.py:760 — def _audit_phase_fl_int(repo_root: Path) -> Dict[str, Any]:
scripts/repo_truth_extractor_promptset_audit_v4.py:763 — prompts_dir = repo_root / "services" / "repo-truth-extractor" / "prompts" / "phase_fl_int"
scripts/repo_truth_extractor_promptset_audit_v4.py:769 — "population": "phase_fl_int",
scripts/repo_truth_extractor_promptset_audit_v4.py:780 — "population": "phase_fl_int",
scripts/repo_truth_extractor_promptset_audit_v4.py:805 — "population": "phase_fl_int",
scripts/repo_truth_extractor_promptset_audit_v4.py:906 — elif population == "phase_s_int":
scripts/repo_truth_extractor_promptset_audit_v4.py:907 — return _audit_phase_s_int(repo_root)
scripts/repo_truth_extractor_promptset_audit_v4.py:908 — elif population == "phase_fl_int":
scripts/repo_truth_extractor_promptset_audit_v4.py:909 — return _audit_phase_fl_int(repo_root)
scripts/repo_truth_extractor_promptset_audit_v4.py:922 — for pop in ["v4", "phase_s", "phase_s_int", "phase_fl_int", "prescan"]:

### ARTIFACTS (56)
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/16_UPLOAD_ORDER.md:42 — 30. `services/repo-truth-extractor/prompts/phase_s/registry.json`
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/16_UPLOAD_ORDER.md:43 — 31. `services/repo-truth-extractor/prompts/prescan/registry.json`
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/17_SOURCE_EXCERPT_INDEX.md:26 — | `services/repo-truth-extractor/prompts/phase_s/registry.json` | full registry | SP/Phase S prompt registry | Phase S warning crosscheck. | prompts |
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/05_PROMPTSET_INVENTORY.md:12 — | `services/repo-truth-extractor/prompts/phase_s/registry.json` | SP/Phase S registry | OBSERVED registry-backed Phase S/SP surface | Phase S warning in prior audit | Prior audit warned Phase S legacy usage; closure not found. |
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/05_PROMPTSET_INVENTORY.md:13 — | `services/repo-truth-extractor/prompts/phase_s_int/registry.json` | integrated Phase S prompts | OBSERVED registry and schemas | UNKNOWN current runtime use | Needs audit against `run_phase_S` and `run_phase_SP`. |
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/05_PROMPTSET_INVENTORY.md:14 — | `services/repo-truth-extractor/prompts/phase_fl_int/registry.json` | feature/design ledger integrated prompts | OBSERVED registry and schemas | UNKNOWN current runtime use | Audit schema and prompt contract drift. |
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/05_PROMPTSET_INVENTORY.md:15 — | `services/repo-truth-extractor/prompts/prescan/registry.json` | prescan metadata registry | OBSERVED registry | Prior pre-live report says prompt text lives in Python constants | Risk: registry may be governance metadata, not canonical pr …[truncated]
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/05_PROMPTSET_INVENTORY.md:17 — | `services/repo-truth-extractor/prompts/v3/` | legacy v3 prompt archive | OBSERVED large v3 prompt tree | Legacy v3 execution gated by proof #605 | Risk if v3 prompts can still influence current outputs through opt-in paths. |
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:76 — "services/repo-truth-extractor/prompts/phase_s/registry.json",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:77 — "services/repo-truth-extractor/prompts/prescan/registry.json",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:78 — "services/repo-truth-extractor/prompts/phase_fl_int/registry.json",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:79 — "services/repo-truth-extractor/prompts/phase_s_int/registry.json",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:120 — "full services/repo-truth-extractor/prompts/v3/ upload in first pass",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:206 — "services/repo-truth-extractor/prompts/phase_s/registry.json": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:207 — "services/repo-truth-extractor/prompts/prescan/registry.json": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:208 — "services/repo-truth-extractor/prompts/phase_fl_int/registry.json": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/15_UPLOAD_MANIFEST.json:209 — "services/repo-truth-extractor/prompts/phase_s_int/registry.json": "runtime",
out/rte-55pro-audit-pack/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/02_OPUS_FINDINGS_CROSSWALK.md:14 — | Phase S legacy prompt usage versus SP registry-backed prompt authority. | STILL_OPEN | `proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json`, `services/repo-truth-extractor/prompts/phase_s/registry.json`, `services/repo-truth-extractor/ …[truncated]
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:168 — "services/repo-truth-extractor/prompts/phase_s/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:169 — "services/repo-truth-extractor/prompts/prescan/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:170 — "services/repo-truth-extractor/prompts/phase_fl_int/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:171 — "services/repo-truth-extractor/prompts/phase_s_int/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:251 — "services/repo-truth-extractor/prompts/phase_s/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:252 — "services/repo-truth-extractor/prompts/prescan/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:253 — "services/repo-truth-extractor/prompts/phase_fl_int/registry.json",
task-packets/generated/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001.json:254 — "services/repo-truth-extractor/prompts/phase_s_int/registry.json",
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:146 — "services/repo-truth-extractor/prompts/phase_s/registry.json",
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:147 — "services/repo-truth-extractor/prompts/prescan/registry.json",
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:148 — "services/repo-truth-extractor/prompts/phase_fl_int/registry.json",
proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json:149 — "services/repo-truth-extractor/prompts/phase_s_int/registry.json",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:423 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_F0_design_claims_raw.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:424 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_F1_design_claims_classified.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:425 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_F2_design_contradictions.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:426 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_F4_canonical_design.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:427 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L0_feature_candidates_raw.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:428 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L1_feature_candidates_normalized.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:429 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L3_feature_ledger_routing.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:430 — "services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L4_master_feature_ledger.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:431 — "services/repo-truth-extractor/prompts/phase_fl_int/registry.json",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:432 — "services/repo-truth-extractor/prompts/phase_s/config/contract_rules.json",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:433 — "services/repo-truth-extractor/prompts/phase_s/config/dedupe_sort_rules.json",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:434 — "services/repo-truth-extractor/prompts/phase_s/config/promotion_rules.json",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:435 — "services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S16_mcp_split_validity.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:436 — "services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S17_hook_surface_map.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:437 — "services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S18_contract_coverage.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:438 — "services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S19_gradecard.md",
proof/repo-deep-remaining-work-audit-2026-05-02.proof.json:439 — "services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S20_v1_release_plan.md",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:29 — "services/repo-truth-extractor/prompts/phase_s/registry.json",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:30 — "services/repo-truth-extractor/prompts/prescan/registry.json"
proof/rte-prelive-audit-pack-2026-04-23.proof.json:64 — "path": "services/repo-truth-extractor/prompts/phase_s/registry.json",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:69 — "path": "services/repo-truth-extractor/prompts/prescan/registry.json",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:79 — "path": "services/repo-truth-extractor/prompts/phase_fl_int/registry.json",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:84 — "path": "services/repo-truth-extractor/prompts/phase_s_int/registry.json",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:130 — "path": "services/repo-truth-extractor/prompts/phase_s/registry.json",
proof/rte-prelive-audit-pack-2026-04-23.proof.json:136 — "path": "services/repo-truth-extractor/prompts/prescan/registry.json",
proof/TP-DOPMUX-COVERAGE-POLICY-0001/TEST_OUTPUT_FULL.txt:387 — E           run_extraction_v3.PromptsetBlockedError: Promptset blocked for phase R: invalid promptset (/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/v3/PROMPT_R10_*.md, /Users/hue/code/dopemux-mvp/services/repo-truth-ext …[truncated]

### OTHER (134)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:369 — ./services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S16_mcp_split_validity.md
audit_inputs/dcp-runner-recon/MCP_RECON.txt:9817 — services/repo-truth-extractor/tests/test_snapshot_capture.py:39:    assert "services/repo-truth-extractor/prompts/phase_s/registry.json" in validator_suite.source_files
audit_inputs/dcp-runner-recon/MCP_RECON.txt:13910 — services/repo-truth-extractor/prompts/v3/PROMPT_M0_RUNTIME_EXPORT_INVENTORY.md:9:  - ~/.config/mcp/**
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14051 — services/repo-truth-extractor/tests/test_promptset_v4_lint.py:192:def test_phase_s_int_audit_passes() -> None:
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14052 — services/repo-truth-extractor/tests/test_promptset_v4_lint.py:193:    """Verify phase_s_int audit passes with current state."""
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14057 — services/repo-truth-extractor/tests/test_promptset_v4_lint.py:204:def test_phase_fl_int_audit_passes() -> None:
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14058 — services/repo-truth-extractor/tests/test_promptset_v4_lint.py:205:    """Verify phase_fl_int audit passes with current state."""
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14071 — services/repo-truth-extractor/tests/test_promptset_v4_lint.py:242:    assert results["phase_s_int"]["prompt_count"] == 5
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14072 — services/repo-truth-extractor/tests/test_promptset_v4_lint.py:243:    assert results["phase_fl_int"]["prompt_count"] == 8
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14445 — services/repo-truth-extractor/prompts/v3/PROMPT_D0_INVENTORY___PARTITION_PLAN.md:22:  - planes (pm/memory/orchestrator/mcp/hooks)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14475 — services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S18_contract_coverage.md:5:Assess Trinity, plane, tool, and proof-contract coverage using only supplied evidence.
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14906 — services/repo-truth-extractor/prompts/v3/PROMPT_H0_INVENTORY___PARTITION_PLAN.md:11:- If something is commonly expected (~/.config/mcp, ~/.dopemux) but not present in context, record it as MISSING (not guessed).
audit_inputs/dcp-runner-recon/MCP_RECON.txt:14933 — services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S19_gradecard.md:9:- Do not invent strengths or weaknesses.
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15079 — services/repo-truth-extractor/prompts/prescan/schemas/dedup.json:4:  "required": ["duplicate_assessments"],
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15080 — services/repo-truth-extractor/prompts/prescan/schemas/dedup.json:6:    "duplicate_assessments": {
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15132 — services/repo-truth-extractor/prompts/prescan/schemas/optimize.json:48:      "required": ["files_skipped", "files_compressed", "estimated_token_reduction_pct"],
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15133 — services/repo-truth-extractor/prompts/prescan/schemas/optimize.json:51:        "files_compressed": {"type": "integer"},
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15259 — services/repo-truth-extractor/prompts/prescan/schemas/discover.json:33:    "ghost_assessments": {
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15375 — services/repo-truth-extractor/prompts/prescan/registry.json:4:  "note": "Prescan prompts are Python constants in lib/prescan/grok_passes.py. This registry provides governance metadata only.",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15376 — services/repo-truth-extractor/prompts/prescan/registry.json:8:      "source_file": "lib/prescan/grok_passes.py",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15377 — services/repo-truth-extractor/prompts/prescan/registry.json:10:      "outputs": ["duplicate_assessments", "version_chain_summaries", "divergent_pairs"],
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15378 — services/repo-truth-extractor/prompts/prescan/registry.json:16:      "source_file": "lib/prescan/grok_passes.py",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15379 — services/repo-truth-extractor/prompts/prescan/registry.json:18:      "outputs": ["hidden_features", "drift_signals", "ghost_assessments", "rediscovery_candidates"],
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15380 — services/repo-truth-extractor/prompts/prescan/registry.json:24:      "source_file": "lib/prescan/grok_passes.py",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15381 — services/repo-truth-extractor/prompts/prescan/registry.json:32:      "source_file": "lib/prescan/grok_passes.py",
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15486 — services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L1_feature_candidates_normalized.md:10:- Never merge across different evidence classes unless the supplied evidence directly supports it.
audit_inputs/dcp-runner-recon/MCP_RECON.txt:15764 — services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L4_master_feature_ledger.md:2:You are a conservative feature-ledger assembler. Output JSON only.
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_surfaces.txt:675 — ./services/repo-truth-extractor/prompts/phase_fl_int/PROMPT_L3_feature_ledger_routing.md
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_surfaces.txt:676 — ./services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S16_mcp_split_validity.md
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/mcp_inventory_raw.txt:368 — ./services/repo-truth-extractor/prompts/phase_s_int/PROMPT_S16_mcp_split_validity.md
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:95817 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_B*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:95830 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_G*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:95843 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_Q*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:95856 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_W*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117387 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117392 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117398 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117403 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117409 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117414 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117420 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117425 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117431 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117436 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117442 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117447 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117453 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117458 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117464 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117469 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117475 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:117480 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:123814 — +        "<< 'EOF'\nUsage:\n  scripts/create_llm_archive.sh [--next-batch]\n\nModes:\n  --next-batch  Create targeted \"next batch\" archive for audit handoff:\n                1) Repo Truth Extractor prompts for W/B/G/Q\n                2) …[truncated]
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:220237 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_B*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:220250 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_G*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:220263 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_Q*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:220276 — +        "excerpt_snippet": "find services/repo-truth-extractor/prompts/v3 -maxdepth 1 -type f -name 'PROMPT_W*.md' -exec cp {} \"${staging_root}/services/repo-truth-extractor/prompts/v3/\" \\",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241807 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241812 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241818 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241823 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241829 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241834 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241840 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241845 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241851 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241856 — +      "to_path": "services/repo-truth-extractor/prompts/v3"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241862 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241867 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241873 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241878 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241884 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241889 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241895 — +        "excerpt_snippet": "services/repo-truth-extractor/prompts/v3/",
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:241900 — +      "to_path": "services/repo-truth-extractor/prompts/v3/"
reports/work-recovery/2026-03-05/stashes/stashat__4___patch.diff:248234 — +        "<< 'EOF'\nUsage:\n  scripts/create_llm_archive.sh [--next-batch]\n\nModes:\n  --next-batch  Create targeted \"next batch\" archive for audit handoff:\n                1) Repo Truth Extractor prompts for W/B/G/Q\n                2) …[truncated]
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2270 — .../prompts/phase_s/PROMPT_S10_REDACTION_PASS.md   |    38 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2271 — .../prompts/phase_s/PROMPT_S11_CONTRACT_LINTER.md  |    38 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2274 — .../prompts/phase_s/PROMPT_S2_DECISION_DOSSIER.md  |     6 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2275 — .../prompts/phase_s/PROMPT_S3_ARCH_PROOF_HOOKS.md  |     6 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2276 — .../prompts/phase_s/PROMPT_S4_TRUTH_PACK_INDEX.md  |     6 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2277 — .../prompts/phase_s/PROMPT_S5_DECISION_GRAPH.md    |     6 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2278 — .../prompts/phase_s/PROMPT_S6_LEANTIME_ANALYSIS.md |     6 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2279 — .../prompts/phase_s/PROMPT_S7_DEDUPE_SORT.md       |    43 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2280 — .../prompts/phase_s/PROMPT_S8_DRIFT_CHECK.md       |    50 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2282 — .../prompts/phase_s/registry.json                  |    13 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2283 — .../prompts/phase_s_int/S16_mcp_split_validity.md  |    18 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2284 — .../prompts/phase_s_int/S17_hook_surface_map.md    |    18 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2285 — .../prompts/phase_s_int/S18_contract_coverage.md   |    18 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2286 — .../prompts/phase_s_int/S19_gradecard.md           |    18 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2287 — .../prompts/phase_s_int/S20_v1_release_plan.md     |    18 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2288 — .../prompts/phase_s_int/schemas/S16.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2289 — .../prompts/phase_s_int/schemas/S17.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2290 — .../prompts/phase_s_int/schemas/S18.json           |    19 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2291 — .../prompts/phase_s_int/schemas/S19.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2292 — .../prompts/phase_s_int/schemas/S20.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2294 — .../prompts/v3/PROMPT_C1_SERVICE_ENTRYPOINTS.md    |    10 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2296 — .../prompts/v3/PROMPT_C3_DOPE_MEMORY_SURFACES.md   |    14 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2300 — .../prompts/v3/PROMPT_C7_API___DASHBOARDS.md       |    10 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2302 — .../prompts/v3/PROMPT_C9_MERGE___NORMALIZE___QA.md |    20 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2305 — .../prompts/v3/PROMPT_D2_DEEP_EXTRACTION.md        |    23 +-
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2312 — .../prompts/v3/PROMPT_R2_EVENTBUS_WIRING_TRUTH.md  |     9 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2315 — .../prompts/v3/PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md  |     9 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2317 — .../prompts/v3/PROMPT_R7_CONFLICT_LEDGER.md        |     9 -
reports/work-recovery/2026-03-05/active-branches/codex__pr-ops__diffstat_vs_main.txt:2318 — .../prompts/v3/PROMPT_R8_RISK_REGISTER_TOP20.md    |     9 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2249 — .../prompts/phase_s/PROMPT_S10_REDACTION_PASS.md   |    38 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2250 — .../prompts/phase_s/PROMPT_S11_CONTRACT_LINTER.md  |    38 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2253 — .../prompts/phase_s/PROMPT_S2_DECISION_DOSSIER.md  |     6 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2254 — .../prompts/phase_s/PROMPT_S3_ARCH_PROOF_HOOKS.md  |     6 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2255 — .../prompts/phase_s/PROMPT_S4_TRUTH_PACK_INDEX.md  |     6 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2256 — .../prompts/phase_s/PROMPT_S5_DECISION_GRAPH.md    |     6 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2257 — .../prompts/phase_s/PROMPT_S6_LEANTIME_ANALYSIS.md |     6 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2258 — .../prompts/phase_s/PROMPT_S7_DEDUPE_SORT.md       |    43 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2259 — .../prompts/phase_s/PROMPT_S8_DRIFT_CHECK.md       |    50 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2261 — .../prompts/phase_s/registry.json                  |    13 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2262 — .../prompts/phase_s_int/S16_mcp_split_validity.md  |    18 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2263 — .../prompts/phase_s_int/S17_hook_surface_map.md    |    18 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2264 — .../prompts/phase_s_int/S18_contract_coverage.md   |    18 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2265 — .../prompts/phase_s_int/S19_gradecard.md           |    18 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2266 — .../prompts/phase_s_int/S20_v1_release_plan.md     |    18 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2267 — .../prompts/phase_s_int/schemas/S16.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2268 — .../prompts/phase_s_int/schemas/S17.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2269 — .../prompts/phase_s_int/schemas/S18.json           |    19 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2270 — .../prompts/phase_s_int/schemas/S19.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2271 — .../prompts/phase_s_int/schemas/S20.json           |    20 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2273 — .../prompts/v3/PROMPT_C1_SERVICE_ENTRYPOINTS.md    |    10 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2275 — .../prompts/v3/PROMPT_C3_DOPE_MEMORY_SURFACES.md   |    14 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2279 — .../prompts/v3/PROMPT_C7_API___DASHBOARDS.md       |    10 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2281 — .../prompts/v3/PROMPT_C9_MERGE___NORMALIZE___QA.md |    20 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2284 — .../prompts/v3/PROMPT_D2_DEEP_EXTRACTION.md        |    23 +-
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2291 — .../prompts/v3/PROMPT_R2_EVENTBUS_WIRING_TRUTH.md  |     9 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2294 — .../prompts/v3/PROMPT_R5_WORKFLOWS_TRUTH_GRAPH.md  |     9 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2296 — .../prompts/v3/PROMPT_R7_CONFLICT_LEDGER.md        |     9 -
reports/work-recovery/2026-03-05/active-branches/fix-routing__diffstat_vs_main.txt:2297 — .../prompts/v3/PROMPT_R8_RISK_REGISTER_TOP20.md    |     9 -

**COUNT LINE**: RUNTIME:6 TESTS:19 CI:0 DOCS:62 SCRIPTS:20 ARTIFACTS:56 (OTHER:134)

---

## services/repo-truth-extractor/base_prompts/

Pattern: `base_prompts`

### RUNTIME (2)
services/repo-truth-extractor/lib/promptgen/sync_engine.py:90 — Defaults to <extractor_root>/base_prompts/.
services/repo-truth-extractor/lib/promptgen/sync_engine.py:126 — template_dir = extractor_root / "base_prompts"

### TESTS (0)
(none)

### CI (0)
(none)

### DOCS (3)
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1452 — Let me confirm two fragmentation risks before writing: (1) the v3-vs-v5 duplicated-docstring fork and whether v3 has a live `__main__` that could still be invoked, and (2) the prompt-truth split (base_prompts vs prompts/v3 vs promptsets/v4/ …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:1483 — **Where prompt + registry truth lives** (resolution order, `rte_promptset.py:9-23`): env `REPO_TRUTH_EXTRACTOR_PROMPT_ROOT` → legacy `UPGRADES_PROMPT_ROOT` → `promptsets/v4/prompts/` (if present) → `prompts/v3/`. Phase S/SP uses a *separate …[truncated]
docs/04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md:77 — │  promptsets/v4/ (138 files)       │  base_prompts/ (5 templates)       │

### SCRIPTS (0)
(none)

### ARTIFACTS (0)
(none)

### OTHER (5)
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4491 — ./services/repo-truth-extractor/base_prompts/PROMPT_A0_CONTROL_INVENTORY.md
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4492 — ./services/repo-truth-extractor/base_prompts/PROMPT_C0_CODE_INVENTORY.md
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4493 — ./services/repo-truth-extractor/base_prompts/PROMPT_D0_DOCS_INVENTORY.md
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4494 — ./services/repo-truth-extractor/base_prompts/PROMPT_E0_EXECUTION_INVENTORY.md
audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/find_files_max4.txt:4495 — ./services/repo-truth-extractor/base_prompts/PROMPT_G0_GOVERNANCE_INVENTORY.md

**COUNT LINE**: RUNTIME:2 TESTS:0 CI:0 DOCS:3 SCRIPTS:0 ARTIFACTS:0 (OTHER:5)

---

## archive/legacy_prompts/ and archive/legacy_artifact_gates/

Pattern: `legacy_prompts|legacy_artifact_gates`

### RUNTIME (0)
(none)

### TESTS (1)
services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py:130 — def test_v5_phase_s_always_returns_legacy_prompts() -> None:

### CI (0)
(none)

### DOCS (8)
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:664 — - `archive/legacy_prompts` and `archive/legacy_artifact_gates` are **never referenced** anywhere — confirmed dead pollution. The grep hits for "archive/" are all about `docs/archive/` (a different path) and `SYSTEM_ARCHIVE/`, not this servi …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:703 — Let me do final verification: (a) confirm README still documents the archive dir as if live (the worktree grep showed README:394 referencing legacy_prompts), (b) confirm output_safety has no write/path operations (it's pure-transform — veri …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:707 — The README at HEAD (`755bf3846`) no longer references `archive/legacy_prompts` (that hit was only in worktree copies, not main). But README:79-87 still documents v3 runner invocations as live operator commands while the engine is v5 — that' …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:769 — - **[S8-006] OBS — `archive/legacy_prompts/` (38 files) and `archive/legacy_artifact_gates/` (2 files) are unreferenced dead pollution, not reachable legacy scripts**
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:770 — - files: `services/repo-truth-extractor/archive/legacy_prompts/*.md` (38), `archive/legacy_artifact_gates/{R_REQUIRED_ARTIFACT_GROUPS_BASE,FULL}.json` (2).
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:771 — - evidence: observed. Repo-wide grep for `repo-truth-extractor/archive`, `legacy_artifact_gates`, and `R_REQUIRED_ARTIFACT_GROUPS` returns **no** runtime reference to these files: the `R_REQUIRED_ARTIFACT_GROUPS` symbol is defined fresh in  …[truncated]
claudedocs/rte-audit-RAW-harvest-2026-05-28.md:773 — - falsifying check: `grep -rn "archive/legacy_prompts\|archive/legacy_artifact_gates" --include="*.py" services/repo-truth-extractor/ | grep -v tests/` — any non-test runtime hit disproves "unreferenced." (Ran: none.)
services/repo-truth-extractor/README.md:394 — - legacy prompt archive: `services/repo-truth-extractor/archive/legacy_prompts/`

### SCRIPTS (0)
(none)

### ARTIFACTS (0)
(none)

### OTHER (7)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10239 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_Q0_PIPELINE_PROOF_INVENTORY.md:13:    - checks[]: {check_id, description, passed, evidence_refs[]}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10240 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_Q0_PIPELINE_PROOF_INVENTORY.md:16:  • Structural QA only; do not assess semantic correctness of artifacts.
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10419 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_E3_EXEC_QA___COVERAGE.md:14:- Check partitions all processed
audit_inputs/dcp-runner-recon/MCP_RECON.txt:10932 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_B0_BOUNDARY_INVENTORY___SOURCES_AND_PARTITIONS.md:19:- execution graph (where boundaries might be bypassed)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11683 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_W1_WORKFLOW_EXTRACT___STRUCTURED.partX.md:23:  - interfaces[] (db/event/file/http/mcp/hook/env)
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11881 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_W3_CROSS_SERVICE_COORDINATION.md:10:    - couplings[]: {kind(home_state/repo_state/env/mcp/compose), description, evidence_refs[]}
audit_inputs/dcp-runner-recon/MCP_RECON.txt:11953 — services/repo-truth-extractor/archive/legacy_prompts/PROMPT_H9_COVERAGE_QA___DRIFT___SAFETY_CHECKS.md:16:4) What home-vs-repo couplings exist (paths/env/mcp/router drift)?

**COUNT LINE**: RUNTIME:0 TESTS:1 CI:0 DOCS:8 SCRIPTS:0 ARTIFACTS:0 (OTHER:7)

---

## src/dopemux/extractor/runner.py + src/dopemux/upgrades/runner.py (PipelineRunner)

Pattern: `PipelineRunner|from dopemux\.extractor|from dopemux\.upgrades|dopemux\.upgrades import`

### RUNTIME (7)
src/dopemux/upgrades/__init__.py:5 — from .runner import PipelineRunner
src/dopemux/upgrades/__init__.py:8 — __all__ = ['PipelineRunner', 'ContextGatherer']
src/dopemux/upgrades/runner.py:12 — class PipelineRunner:
src/dopemux/extractor/__init__.py:5 — from .runner import PipelineRunner
src/dopemux/extractor/__init__.py:8 — __all__ = ['PipelineRunner', 'ContextGatherer']
src/dopemux/extractor/runner.py:33 — class PipelineRunner:
src/dopemux/extractor/runner.py:237 — prompt_content = f"# PHASE {phase} INSTRUCTIONS\nGenerated by Dopemux PipelineRunner."

### TESTS (0)
(none)

### CI (0)
(none)

### DOCS (31)
docs/research/mcp-customization/dopemux-constraints/TRUTH_SYSTEMS.md:212 — - Legacy `PipelineRunner` shortcut is not the same as the v5 extraction service.
docs/research/mcp-customization/dopemux-constraints/system-boundaries.md:75 — | `dopemux core` | Primary CLI/runtime package, kernel integration, extractor command wiring, routing/provider config loading, operator control surface. | Canonical repo-truth extraction runtime for v5. | `dopemux truth` is legacy `Pipeline …[truncated]
docs/research/mcp-customization/dopemux-constraints/system-boundaries.md:83 — | `repo-truth-extractor` | Canonical multi-phase repo-truth extraction, v4 compatibility wrapper, and extraction artifacts. | Representation through the legacy `dopemux truth` / `PipelineRunner` path. | Canonical CLI path is extractor/upgra …[truncated]
docs/research/mcp-customization/dopemux-constraints/system-boundaries.md:100 — - Extraction -> `repo-truth-extractor`. Legacy `dopemux truth` remains drift because it routes through `PipelineRunner` instead of the canonical extractor v5 path.
docs/research/mcp-customization/dopemux-constraints/TRUTH_DATA_EVENTS.md:167 — - `dopemux truth` in `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` bypasses this path and invokes legacy `PipelineRunner`.
docs/research/mcp-customization/dopemux-constraints/TRUTH_DATA_EVENTS.md:224 — - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` `truth` command uses legacy `PipelineRunner`, while `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/README.md` and extractor commands point to v5.
docs/research/mcp-customization/dopemux-constraints/PROJECT.md:171 — - repo-truth extraction has a legacy-versus-current split. The extractor service and command family point to the v5 runner, but `dopemux` still exposes legacy `PipelineRunner`-based truth flows.
docs/research/mcp-customization/dopemux-constraints/TRUTH_INTERFACES.md:32 — - `dopemux truth` is a legacy shortcut to `PipelineRunner`, not the same path used by `dopemux extractor` / `dopemux upgrades`.
docs/research/mcp-customization/dopemux-constraints/TRUTH_INTERFACES.md:336 — - `dopemux truth` -> `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` -> `PipelineRunner` in `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`
docs/research/mcp-customization/dopemux-constraints/TRUTH_CANONICALS.md:212 — - `src/dopemux/cli.py` `truth` command instantiates `PipelineRunner`.
docs/research/mcp-customization/dopemux-constraints/TRUTH_CANONICALS.md:213 — - `PipelineRunner` emits legacy trace behavior and dry-run/execution ritual language.
docs/research/mcp-customization/dopemux-constraints/TRUTH_CANONICALS.md:216 — - Legacy alias/drift: `dopemux truth` via `PipelineRunner`
CHANGELOG.md:26 — - `dopemux truth`, `dopemux upgrades trace`, and `dopemux extractor trace` now delegate to the canonical v5 runtime contract instead of legacy `PipelineRunner` behavior.
docs/05-audit-reports/rte-production-certification-audit-20260414.md:57 — | `src/dopemux/cli.py` `truth` command | `legacy / broken` | Delegates to `PipelineRunner`, not the v5 runtime. |
docs/05-audit-reports/rte-production-certification-audit-20260414.md:69 — | `dopemux extractor trace` | `PipelineRunner` | legacy non-canonical trace simulator | `NON-PRODUCTION` |
docs/05-audit-reports/rte-production-certification-audit-20260414.md:70 — | `dopemux truth` | `PipelineRunner.run_all()` | broken legacy shortcut | `BLOCKED` |
docs/05-audit-reports/rte-production-certification-audit-20260414.md:79 — - `src/dopemux/cli.py:5153-5198` routes `dopemux truth` to `PipelineRunner`.
docs/05-audit-reports/rte-production-certification-audit-20260414.md:320 — - PipelineRunner probe:
docs/04-explanation/root-relocated/docs-audit.md:48 — - **Extractor Reality:** Old docs pointed to `dopemux truth` as the primary path. Truth: `run_extraction_v5.py` is the canonical extractor runtime; `dopemux truth` relies on legacy `PipelineRunner`.
docs/04-explanation/root-relocated/docs-audit.md:58 — 5. **Legacy Systems:** Status of `services/dope-query`, `services/taskmaster`, and `dopemux truth` (v4 PipelineRunner vs v5) require formal deprecation or removal.
PROJECT.md:160 — - repo-truth extraction has a legacy-versus-current split. The extractor service and command family point to the v5 runner, but `dopemux` still exposes legacy `PipelineRunner`-based truth flows.
docs/03-reference/systems/system-boundaries.md:81 — | `dopemux core` | Primary CLI/runtime package, kernel integration, extractor command wiring, routing/provider config loading, operator control surface. | Canonical repo-truth extraction runtime for v5. | `dopemux truth` is legacy `Pipeline …[truncated]
docs/03-reference/systems/system-boundaries.md:89 — | `repo-truth-extractor` | Canonical multi-phase repo-truth extraction, v4 compatibility wrapper, and extraction artifacts. | Representation through the legacy `dopemux truth` / `PipelineRunner` path. | Canonical CLI path is extractor/upgra …[truncated]
docs/03-reference/systems/system-boundaries.md:106 — - Extraction -> `repo-truth-extractor`. Legacy `dopemux truth` remains drift because it routes through `PipelineRunner` instead of the canonical extractor v5 path.
docs/03-reference/governance/docs-vs-repo-diff.md:52 — | DVSRD-013 | `dopemux truth` and extractor v5 are equivalent repo-truth paths. | Truth docs state `dopemux extractor` / `dopemux upgrades` resolve to `run_extraction_v5.py`, while `dopemux truth` uses legacy `PipelineRunner`. | Legacy CLI  …[truncated]
docs/03-reference/truth/truth-systems.md:213 — - Legacy `PipelineRunner`/`dopemux truth` shortcut is not the same as the v5 extraction service.
docs/03-reference/truth/truth-data-events.md:227 — - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` now makes `dopemux rte` the canonical operator family and turns `dopemux truth` into a legacy/refusal surface. Older docs may still mention the historical `PipelineRunner` path and must not …[truncated]
docs/03-reference/truth/truth-canonicals.md:223 — - Older `PipelineRunner` surfaces remain legacy drift and are not the v5 path.
docs/archive/unclassified-top-level/repo-truth/truth-canonicals.md:226 — - Fact: `dopemux truth` still exists and uses `PipelineRunner`.
docs/archive/unclassified-top-level/repo-truth/truth-interfaces.md:41 — - Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` still exposes a direct `truth` command backed by `PipelineRunner` from `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`.
docs/archive/unclassified-top-level/repo-truth/truth-interfaces.md:65 — - Fact: `dopemux truth` and `dopemux extract truth-run` both target repo-truth extraction, but through different runners: `PipelineRunner` versus direct `run_extraction_v5.py`.

### SCRIPTS (0)
(none)

### ARTIFACTS (15)
out/DMX-AUTHORITY-SERIES-MASTER.md:287 — | D-010 | Repo truth extraction     | `run_extraction_v5.py` strongest runtime.                                         | Legacy `dopemux truth` / PipelineRunner still exists.                    | Repo Truth Extractor docs.                  …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/08_TRUTH_SYSTEMS.md:213 — - Legacy `PipelineRunner`/`dopemux truth` shortcut is not the same as the v5 extraction service.
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/02_PROJECT.md:160 — - repo-truth extraction has a legacy-versus-current split. The extractor service and command family point to the v5 runner, but `dopemux` still exposes legacy `PipelineRunner`-based truth flows.
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/11_TRUTH_CANONICALS.md:223 — - Older `PipelineRunner` surfaces remain legacy drift and are not the v5 path.
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/04_SYSTEM_BOUNDARIES.md:81 — | `dopemux core` | Primary CLI/runtime package, kernel integration, extractor command wiring, routing/provider config loading, operator control surface. | Canonical repo-truth extraction runtime for v5. | `dopemux truth` is legacy `Pipeline …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/04_SYSTEM_BOUNDARIES.md:89 — | `repo-truth-extractor` | Canonical multi-phase repo-truth extraction, v4 compatibility wrapper, and extraction artifacts. | Representation through the legacy `dopemux truth` / `PipelineRunner` path. | Canonical CLI path is extractor/upgra …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/04_SYSTEM_BOUNDARIES.md:106 — - Extraction -> `repo-truth-extractor`. Legacy `dopemux truth` remains drift because it routes through `PipelineRunner` instead of the canonical extractor v5 path.
task-packets/generated/TP-DMX-COLDSTART-SALVAGE-COLDSTART-LIB-101.json:77 — "task": "Inspect repo truth before editing. Read install.sh functions: detect_platform (line 960), install_with_brew/apt/dnf/pacman (1159/1197/1227/1258), resolve_secret_value (453), resolve_existing_env_value (373), read_secret_from_keycha …[truncated]
out/chatgpt-project-upload-set/TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP/UPLOAD_FILES/10_TRUTH_DATA_EVENTS.md:227 — - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` now makes `dopemux rte` the canonical operator family and turns `dopemux truth` into a legacy/refusal surface. Older docs may still mention the historical `PipelineRunner` path and must not …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:61 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:121 — "rg -n \"rte|extractor|truth|upgrades|LegacyReplacementCommand|run_extraction|run_repscan|PipelineRunner\" src/dopemux/cli.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth- …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:122 — "rg -n \"dopemux upgrades|dopemux rte|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v5|run_extraction_v4|run_extraction_v3|run_repscan|canonical|legacy|deprecated|compatibility|go-live|unattended|bounded|provider|batch\" REA …[truncated]
task-packets/generated/TP-RTE-DOCS-CANON-008.json:153 — "rg -n \"dopemux upgrades|dopemux extractor|dopemux truth|PipelineRunner|run_extraction_v3|run_extraction_v4|run_repscan|python services/repo-truth-extractor/run_extraction_v5.py\" README.md docs/00-MASTER-INDEX.md docs/02-how-to/extraction …[truncated]
proof/TP-RTE-DOCS-CANON-008/PROOF.json:55 — "command": "python - <<'PY'\nfrom pathlib import Path\npaths = [Path('README.md'), Path('docs/00-MASTER-INDEX.md'), *Path('docs/02-how-to/extraction').glob('*.md'), Path('docs/03-reference/extraction/pipeline-reliability.md'), *Path('docs/0 …[truncated]
proof/TP-RTE-DOCS-CANON-008/PROOF.json:125 — "Remaining mentions of `dopemux extractor`, `dopemux truth`, `dopemux extract truth-run`, `PipelineRunner`, `run_repscan`, v3, and direct runner invocation include legacy, compatibility, deprecated, refusal, gated, advanced, debug, manual,  …[truncated]

### OTHER (4)
config/runtime_authority_manifest.json:722 — "reason": "Legacy PipelineRunner path is not the canonical v5 extraction runtime."
reports/rte-production-certification-audit-20260414.json:105 — "target": "PipelineRunner",
reports/rte-production-certification-audit-20260414.json:111 — "target": "PipelineRunner.run_all()",
reports/rte-production-certification-status.json:56 — "dopemux truth no longer depends on PipelineRunner.",

**COUNT LINE**: RUNTIME:7 TESTS:0 CI:0 DOCS:31 SCRIPTS:0 ARTIFACTS:15 (OTHER:4)

---
