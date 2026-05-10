# TP-RTE-V3-CONSENT-004 Implementer Report

## 1. Change summary

Implemented a bounded RTE safety slice for legacy v3 execution:

- `_extractor_runner_path` now fails closed for unknown pipeline versions instead of falling back to v3.
- `run_extraction_v3.py` now requires `--execute` and `DPMX_LIVE_OK=1` before live-capable v3 operations.
- `dopemux rte run --execute` now forwards `--execute` to the selected runner.
- `dopemux rte scan` and direct `run_repscan.py` now refuse by default unless `--allow-legacy-v3-scan` is explicit.

## 2. Authority used

- Runtime authority: `services/repo-truth-extractor/run_extraction_v5.py`, `run_extraction_v4.py`, `run_extraction_v3.py`, `run_repscan.py`, `src/dopemux/cli.py`, and `src/dopemux/commands/extractor_commands.py`.
- Repo guidance: `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`.
- Tracked reference authority for absent root truth files: `docs/research/mcp-customization/dopemux-constraints/*.md`.
- Task Packet schema: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
- Packet/index convention: `task-packets/INDEX.md`.

## 3. Files changed

- `services/repo-truth-extractor/run_extraction_v3.py`
- `services/repo-truth-extractor/run_repscan.py`
- `services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py`
- `services/repo-truth-extractor/tests/test_run_repscan.py`
- `services/repo-truth-extractor/tests/test_truth_run_cli.py`
- `src/dopemux/cli.py`
- `src/dopemux/commands/extractor_commands.py`
- `task-packets/INDEX.md`
- `task-packets/generated/TP-RTE-V3-CONSENT-004.json`
- `proof/TP-RTE-V3-CONSENT-004/PROOF.json`
- `proof/TP-RTE-V3-CONSENT-004/IMPLEMENTER_REPORT.md`

## 4. Exact safety behavior now enforced

- Known pipeline versions are `v5`, `v4`, and `v3`; unknown programmatic values raise a `ClickException`.
- v3 live-capable operations are phase execution, async submit/finalize, batch watch, and batch retrieve.
- v3 live-capable operations require both `--execute` and `DPMX_LIVE_OK=1`.
- v3 refusal happens before run context resolution, latest pointer writes, run manifest writes, phase directory creation, provider calls, model calls, and batch calls.
- `dopemux rte scan` refuses by default and requires `--allow-legacy-v3-scan`.
- `run_repscan.py` refuses by default and requires `--allow-legacy-v3-scan`.

## 5. Validation results with exit codes

- `python -m json.tool task-packets/generated/TP-RTE-V3-CONSENT-004.json >/dev/null`: exit 0
- `Draft7Validator` against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`: exit 0
- `python -m compileall -q src/dopemux services/repo-truth-extractor`: exit 0
- `python services/repo-truth-extractor/run_extraction_v3.py --help >/tmp/rte_v3_help.txt`: exit 0
- `python services/repo-truth-extractor/run_extraction_v4.py --help >/tmp/rte_v4_help.txt`: exit 0
- `python services/repo-truth-extractor/run_extraction_v5.py --help >/tmp/rte_v5_help.txt`: exit 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`: exit 0, 43 passed
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_run_extraction_v3_consent.py services/repo-truth-extractor/tests/test_truth_run_cli.py services/repo-truth-extractor/tests/test_run_repscan.py`: exit 0, 28 passed, 2 skipped
- `git diff --check`: exit 0
- `pre-commit run --files ...`: exit 0

## 6. Findings closed/narrowed

- `F1-CRIT-1`: addressed for v3 live-capable execution.
- `F1-CRIT-2`: addressed for programmatic pipeline-version routing.
- `F1-HIGH-2`: narrowed/addressed for the inspected `dopemux rte scan` and `run_repscan.py` paths by default refusal plus explicit legacy opt-in.

## 7. Residual risks

- Full repository tests were not run.
- Two existing CLI import tests skipped because `litellm` is not installed in this environment.
- Explicit `--allow-legacy-v3-scan` still permits legacy scan artifact generation; this packet blocks silent routing but does not create a v5 scan replacement.
- Root truth-file pathing remains drifted; tracked research/reference equivalents were used.

## 8. PR/commit details

- Branch: `codex/tp-rte-v3-consent-004`
- Worktree: `/Users/hue/.codex/worktrees/tp-rte-v3-consent-004`
- Initial commit SHA: `96397e51072a6abe79fd7912d72f38282834bf73`
- PR URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/605
- Subsequent review-feedback commits extend this packet; see PR commit log for the live trail.
