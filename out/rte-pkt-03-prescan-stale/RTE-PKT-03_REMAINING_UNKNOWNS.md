# RTE-PKT-03 Remaining Unknowns

- `--prescan-dir` appears to be defined as a CLI argument but was not observed wired into `RunnerConfig` in the inspected runner path. This packet guarded `--prescan-import-dir`, which is the active import path observed in `run_integrated_prescan_stage()`.
- Full downstream prescan influence labeling remains out of scope for this packet and belongs to RTE-PKT-04-PRESCAN-INFLUENCE.
- The broad selector `pytest services/repo-truth-extractor/tests -k 'prescan and import' -q` currently fails because it catches an out-of-scope CodePrescan test expecting an `imports` field. This packet did not change `services/repo-truth-extractor/lib/prescan/code_prescan.py`.
- Existing pytest configuration emits `PytestConfigWarning: Unknown config option: asyncio_mode`.
- Accepted imports require exact normalized root path matches. Importing artifacts generated from a different worktree path for the same commit is intentionally rejected unless a later packet defines a different compatibility rule.

