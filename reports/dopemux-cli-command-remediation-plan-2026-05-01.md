# Dopemux CLI Command Remediation Plan

Date: 2026-05-01
Workspace: `[repo workspace path redacted]`

## Summary

This plan translates `reports/dopemux-cli-command-audit-2026-05-01.md` into implementation slices. The current pass implemented the first remediation set and left remaining authority gaps explicit instead of inventing missing behavior.

## Remediation Ledger

| Priority | Finding | Impacted commands | Fix direction | Status in this pass | Validation |
|---|---|---|---|---|---|
| P0/P1 | Shell interpolation and weak failure propagation in MCP commands | `mcp up`, `mcp logs`, `mcp status`, `servers up/logs/status` | Use argv subprocess calls, validate service names from `compose.yml`, use truthful nonzero exits on Docker failures | Implemented | `tests/unit/test_cli_audit_remediations.py` |
| P1 | Broken routing mode write uses undefined `content` | `routing api`, `routing direct` | Deterministically load YAML, preserve fields, write `mode`, fail closed on invalid config | Implemented | `tests/unit/test_cli_audit_remediations.py` |
| P1 | Decisions command self-import swallows registration failure | `decisions`, `decisions energy`, `decisions patterns` | Remove bogus self-import and keep only runtime-backed groups until real callbacks exist | Implemented | `tests/unit/test_cli_audit_remediations.py` |
| P1 | Code-agent commands returned success on missing dependency/failure | `code repair`, `code analyze`, `code status` | Resolve repo-local `services/genetic_agent`, raise Click errors on dependency or operation failure | Implemented | `tests/unit/test_cli_audit_remediations.py` |
| P1 | PR merge specialist self-check failed in module-entry smoke context | `pr-merge self-check` | Keep preflight evidence truthful but treat environment-dependent preflight failure as nonfatal under `--allow-dirty` | Implemented | `tests/pr_merge_specialist/test_policy_and_validation.py::test_module_entrypoint_works_without_pythonpath` |
| P1 | Speculative train accepted ineligible mixed strategy | `pr-merge queue-drain` train path | Classify `MIXED` PRs before clean merge-ready shortcut so train filtering can defer staged strategies | Implemented | `tests/pr_merge_specialist/test_queue_drain_integration.py::test_train_filters_ineligible_strategies` |
| P2 | Operator-facing status names drifted | `update`, `code` | Add public `status` aliases and keep old generated names hidden for compatibility | Implemented | `tests/unit/test_cli_audit_remediations.py` |
| P2 | Profile placeholder commands were live | `profile copy/edit/delete/current` | Register real profile lifecycle callbacks from `src/dopemux/profile_commands.py` | Implemented | `tests/unit/test_cli_audit_remediations.py`; existing profile tests |
| P2 | Native hook registration duplicated and swallowed invalid JSON | `native-hooks register` | Consolidate registration, reject invalid existing settings, write atomically with backup | Implemented | `tests/unit/test_cli_audit_remediations.py` |
| P2 | Duplicate `pr-merge` and `instances` registration | root `pr-merge`, `instances`, `native-hooks` | Remove earlier duplicate Click registration and keep one authoritative registration path | Implemented | full help sweep planned below |
| P2 | Docs/code drift around CLI import and TaskX naming | docs/reference and reports | Update system docs with current root-help truth and link command/audit/remediation artifacts | Implemented in docs sync slice | `git diff --check`; help sweep |
| P3 | Detailed command behavior was not available as a report | all command paths | Generate a command reference from runtime Click traversal plus source inspection | Implemented | `reports/dopemux-cli-command-reference-2026-05-01.md` |

## Remaining Work After This Pass

- Decide whether `dopemux decisions review/list/stats/...` should be reintroduced, and if so identify the canonical ConPort/decision-plane implementation before adding callbacks.
- Add broader integration tests for real Docker Compose, launchd, tmux, and external GitHub flows in an environment where those side effects are explicitly authorized.
- Consider moving native-hook registration into a dedicated command module to reduce the size of `src/dopemux/cli.py`; this pass only removed duplicate runtime registration.

## Validation Performed

- `uv run --frozen python -m dopemux --help`
  - Exit: `0`
- Full subprocess help sweep from runtime Click traversal, including hidden compatibility aliases
  - Paths: `236`
  - Failures: `0`
- `uv run --frozen --extra test python -m pytest tests/unit/test_cli_audit_remediations.py tests/pr_merge_specialist/test_policy_and_validation.py::test_module_entrypoint_works_without_pythonpath tests/pr_merge_specialist/test_queue_drain_integration.py::test_train_filters_ineligible_strategies -q`
  - Exit: `0`
- `uv run --frozen --extra test python -m pytest tests/test_cli.py tests/test_cli_mcp_startup.py tests/unit/test_cli_*.py tests/unit/test_extractor_command_authority.py tests/unit/test_cli_upgrades_commands.py tests/unit/test_profile_cli_registration.py tests/unit/dopemux/ui/cockpit/test_cockpit_command.py tests/test_mobile_cli.py tests/pr_merge_specialist -q`
  - Exit: `0`
- `git diff --check`
  - Exit: `0`
