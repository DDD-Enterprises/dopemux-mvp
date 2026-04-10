# PR Diff Summary

- Packet: `TP-CODEX-RTE-MAIN-PR-001`
- Source branch: `codex/rte-merge-exec-001`
- Target branch: `main`
- Source branch tip at inspection: `3749d3b2a8d1cb0746e6e98a1c4e36e0e746b9c5`
- Target branch tip at inspection: `e4bf2d148886cee0883c2afda5bdfd0a9591f840`
- Total commits ahead of `main`: `8`

## Full Branch Diff vs `main`

`git diff --stat main...codex/rte-merge-exec-001` shows 11 changed files:

- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/IMPLEMENTER_REPORT.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/PROOF.json`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/bounded_target_replay_readiness.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/final_replay_exec_verdict.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/replay_branch_creation.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/replay_branch_validation.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/replay_conflict_resolution.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/replayed_commit_log.md`
- `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/verification_commands.txt`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`

## Runtime Diff Scope

The runtime code diff is limited to exactly two files:

- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`

The additional changed files are proof artifacts from `TP-CODEX-RTE-MERGE-EXEC-001`, not extra runtime surfaces.
