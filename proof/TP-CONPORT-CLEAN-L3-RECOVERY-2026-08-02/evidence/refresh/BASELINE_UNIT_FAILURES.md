# Baseline unit failures (not introduced by #1188)

Identical FAIL on `origin/main` (`fb710ef405`) and #1188:

- `tests/unit/test_cli_upgrades_commands.py::test_truth_command_is_deprecated`
- `tests/unit/test_cli_upgrades_commands.py::test_truth_command_rejects_legacy_deep_mode`
- `tests/unit/test_pm_source_events.py::test_emit_pm_promotable_source_event_rejects_bare_non_repo_workspace_root`

#1188 does not modify these tests or their production code paths.
Classification: **BASELINE_EXISTING**. Not repaired in this PR.
