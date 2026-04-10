# Replayed Commit Log

## Required Source Slice

Source authority came from `TP-CODEX-RTE-MERGE-PREP-001/clean_replay_plan.md` and `required_commit_source_map.md`.

## Replay Results

| Source SHA | Subject | Earliest source branch | Replay action | Result | Replay SHA / note |
| --- | --- | --- | --- | --- | --- |
| `c660ab9df` | `fix(repo-truth-extractor): recover deferred tp002-owned changes` | `feature/pm-jules-010-to-runtime-freeze-v2-clean` | `cherry-pick` | `conflict resolved` | `d4fc167d79e96b22f78109bd4e91f33ca3edf2af` |
| `2144d4e36` | `fix(repo-truth-extractor): recover TP001 spend-cap logic from mixed runner` | `feature/pm-jules-010-to-runtime-freeze-v2-clean` | `cherry-pick` | `conflict resolved` | `de544c1379b2b259b9aab97bff0f7172e4f28366` |
| `e14690d0d` | `fix(repo-truth-extractor): recover TP003 bounded execution logic from mixed runner` | `feature/pm-jules-010-to-runtime-freeze-v2-clean` | `cherry-pick` | `conflict resolved` | `ff29dd457c78f2f63e51e3882a6310e4a7df5633` |
| `0db7b8528` | `fix(repo-truth-extractor): recover missing TP001 usage summary logic` | `feature/pm-jules-010-to-runtime-freeze-v2-clean` | `cherry-pick` | `already preserved / empty replay` | `git cherry-pick --skip` after empty delta |
| `91868d873` | `feat(repo-truth-extractor): implement JSON repair provenance tracking and unify run status` | `feature/pm-jules-010-to-runtime-freeze-v2-clean` | `cherry-pick` | `conflict resolved` | `52d651b01033b889680f888c2bdb278e3297e77f` |
| `6bc14c7bd` | `fix(repo-truth-extractor): correct narrow post-tp004 live defects` | `codex/rte-prelive-005-bounded-live-reattempt` | `cherry-pick` | `conflict resolved` | `1052feba2d77d7ad14f008819ad073dfa61d9084` |
| `d88a1bcc4` | `fix(repo-truth-extractor): correct narrow bounded-live truth defect` | `codex/rte-prelive-006-coherent-bounded-live-reattempt` | `cherry-pick` | `already preserved / empty replay` | `git cherry-pick --skip` after empty delta |
| `9317a169d` | `fix(repo-truth-extractor): correct narrow post-tp006 artifact truth contradiction` | `codex/rte-prelive-006-coherent-bounded-live-reattempt` | `cherry-pick` | `already preserved / empty replay` | `git cherry-pick --skip` after empty delta |

## Replay-Repair Delta

- Additional replay-repair commit created: `c7250ecaf5dd069dc324b5f538a9285dd03853d8`
- Subject: `fix(repo-truth-extractor): restore selected-step validator replay integrity`
- Reason: replay conflict resolution left `validate_pre_live_gate_v25.py` without `return scope` and without step-filtered observed contract-map keys. The branch did not validate until this bounded fix was applied.
