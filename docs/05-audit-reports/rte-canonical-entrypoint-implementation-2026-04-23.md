# RTE Canonical Entrypoint Implementation Report

**Packet:** `TP-DMX-RTECANON-001`  
**Date:** `2026-04-23`  
**Branch:** `codex/rte-canonical-operator-entrypoint`

## Summary

This change establishes `dopemux rte` as the canonical operator-facing command family for Repo Truth Extractor while keeping the v5 runtime itself unchanged. The implementation aligns wrapper defaults and validator target policy to the v5 runtime's current `cost` default, preserves v5 resume semantics, and demotes divergent legacy surfaces.

## Authority And Scope

Primary authority:

- `services/repo-truth-extractor/run_extraction_v5.py`
- `src/dopemux/cli.py`
- `src/dopemux/commands/extract_commands.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- `services/repo-truth-extractor/tests/test_truth_run_cli.py`

Secondary authority:

- `services/repo-truth-extractor/README.md`
- `docs/05-audit-reports/rte-gemini-deep-pal-audit-2026-04-23.md`

Non-goals:

- no live extraction run
- no prompt content edits
- no changes to `run_extraction_v5.py` semantics

## Pre-Change Drift

Observed before implementation:

- `run_extraction_v5.py` defaulted to routing policy `cost`
- `src/dopemux/cli.py` defaulted v5 wrapper policy to `balanced_openrouter`
- `validate_pre_live_gate_v25.py` defaulted target policy to `balanced_openrouter`
- canonical operator guidance was split across `dopemux upgrades`, `dopemux extract truth-run`, and top-level `dopemux truth`
- `dopemux truth` was a reduced-surface alias that could preserve a parallel operator path instead of forcing the canonical family

## Implemented Canonical Mapping

Canonical family:

- `dopemux rte run`
- `dopemux rte list`
- `dopemux rte doctor`
- `dopemux rte status`
- `dopemux rte preflight`
- `dopemux rte validate-live`
- `dopemux rte trace`
- `dopemux rte promptset audit`

Compatibility surfaces retained:

- `dopemux upgrades ...`
  - retained as an exact-policy compatibility alias to the same command callbacks now mounted under `dopemux rte`
- `dopemux extract truth-run`
  - retained as a compatibility alias to the v5 runtime path
  - default routing policy aligned to `cost`
  - operator messaging now identifies `dopemux rte run` as canonical

Legacy surface hard-refused:

- `dopemux truth`
  - now exits fail-closed with an explicit redirect to `dopemux rte`
  - avoids preserving a reduced-surface top-level operator alternative

## Policy And Resume Alignment

Aligned to runtime truth:

- `src/dopemux/cli.py`
  - `_V5_DEFAULT_ROUTING_POLICY = "cost"`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - `DEFAULT_TARGET_POLICY = "cost"`
- `src/dopemux/commands/extract_commands.py`
  - `truth-run --routing-policy` default set to `cost`

Resume behavior preserved:

- `_build_truth_run_command(...)` still omits `--run-id` when `resume=True` and no explicit run id is supplied
- display behavior still points operators at `latest_run_id.txt` for implicit resume

## Validation Evidence

Executed:

- `python -m json.tool task-packets/TP-DMX-RTECANON-001.json`
- `python -m json.tool proof/rte-canonical-entrypoint-implementation-2026-04-23.proof.json`
- `python -m py_compile src/dopemux/cli.py src/dopemux/commands/extract_commands.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/validate_pre_live_gate_v25.py services/repo-truth-extractor/tests/test_truth_run_cli.py`
- `git diff --check -- src/dopemux/cli.py src/dopemux/commands/extract_commands.py src/dopemux/commands/extractor_commands.py services/repo-truth-extractor/validate_pre_live_gate_v25.py services/repo-truth-extractor/README.md docs/05-audit-reports/rte-canonical-entrypoint-implementation-2026-04-23.md proof/rte-canonical-entrypoint-implementation-2026-04-23.proof.json task-packets/TP-DMX-RTECANON-001.json task-packets/INDEX.md`

Validated directly:

- touched Python files compile successfully
- packet and proof artifacts are valid JSON
- diff hygiene passes on the allowed file set

Inspected and encoded in focused tests, but not executed in this environment:

- `dopemux rte` registration and mounted commands
- `dopemux extract truth-run` option surface
- `truth-run` default routing policy set to `cost`
- helper command construction preserving explicit and implicit resume behavior

Environment blockers:

- `python -m pytest ...` could not run because `pytest` is not installed in the active interpreter
- direct `PYTHONPATH=src python -c 'from dopemux.cli import cli'` import checks could not run because `click` is not installed in the active interpreter

## Remaining Compatibility Debt

Known retained debt after this packet:

- `dopemux upgrades` still exists as a legacy alias because broader removal would be a larger operator migration
- `dopemux extract truth-run` still exists for compatibility, so operator discovery still depends on help text and docs being accurate
- `proof/*` remains gitignored in this checkout, so proof artifacts validate locally but require explicit force-add if they are meant to be committed
- packet-targeted pytest coverage remains unexecuted in this environment until the repo dev dependencies are installed

## Verdict

`dopemux rte` is now the explicit canonical operator family in code and docs for Repo Truth Extractor. Wrapper policy inheritance and validator default policy are aligned to the v5 runtime's current `cost` default. The remaining drift is compatibility debt, not split default behavior.
