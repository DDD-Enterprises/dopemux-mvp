# TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001 Worktree Inventory

Generated on 2026-04-04 in `/Users/hue/code/dopemux-mvp`.

## Tracked Modified Files

| Path | State | Classification | Commit Bucket | Commit Now | Rationale |
| --- | --- | --- | --- | --- | --- |
| `docs/05-audit-reports/ADR-197-P0-STAGE1-STAGE2-IMPLEMENTATION-PR-PLAN-2026-02-06.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/AUDIT-SUMMARY-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/COMPLETE-AUDIT-SUMMARY-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/DEPLOYMENT-READY-SUMMARY.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/EXHAUSTIVE-AUDIT-PLAN.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/FINAL-AUDIT-REPORT-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/FINAL-AUDIT-REPORT.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/OPTIMIZED-AUDIT-PLAN.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/PHASE-1-COMPLETE.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/PHASE-3-REMAINING-SERVICES-QUICK-SCAN.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/PHASE-4-DOCUMENTATION-VALIDATION-COMPLETE.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/PHASE-6-INTEGRATION-TESTS-ASSESSMENT.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/PLAN.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/ROADMAP-REMAINING-WORK.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/START-HERE-NEXT-SESSION.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `docs/05-audit-reports/ULTIMATE-AUDIT-COMPLETION-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Unrelated docs deletion outside repo-truth-extractor prelive recovery scope. |
| `services/repo-truth-extractor/run_extraction_v5.py` | modified | `UNRESOLVED` | `leave_uncommitted` | no | File contains mixed uncommitted TP001 spend-cap work, TP002 repair-provenance work, TP003 bounded live validator enforcement, and supporting plumbing in one file. File-level ownership is not truthful enough for recovery commit boundaries. |
| `services/repo-truth-extractor/validate_pre_live_gate_v25.py` | modified | `RECOVER_TP002` | `commit_2_tp002_code` | yes | Validator classification changes are coherent and map to TP-002/002A bounded validator readiness and operator-verdict semantics. |
| `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py` | modified | `RECOVER_TP002` | `commit_3_tp002_tests` | yes | Regression coverage matches the validator changes in `validate_pre_live_gate_v25.py`. |

## Untracked Files And Directories

| Path | State | Classification | Commit Bucket | Commit Now | Rationale |
| --- | --- | --- | --- | --- | --- |
| `.codex-tmp-doc-placement/` | untracked dir | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Tooling scratch output, not packet-owned code. |
| `.codex-worktrees/` | untracked dir | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Tooling worktree cache, not packet-owned code. |
| `LIVE_LOG.txt` | untracked | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Runtime log output. |
| `LIVE_LOG_2.txt` | untracked | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Runtime log output. |
| `LIVE_LOG_3.txt` | untracked | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Runtime log output. |
| `LIVE_LOG_FINAL.txt` | untracked | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Runtime log output. |
| `config/pricing.yaml` | untracked | `UNRESOLVED` | `leave_uncommitted` | no | Likely TP001 spend-cap authority, but depends on unresolved mixed runner changes in `run_extraction_v5.py`. |
| `llm-plans/STABILIZE_PR384_EXTRACTOR_TESTS.md` | untracked | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Planning note outside recovery packet scope. |
| `llm-plans/TP-GIT-CONSOLIDATION-0009-STABILIZATION.md` | untracked | `UNRELATED_DRIFT` | `leave_uncommitted` | no | Planning note outside recovery packet scope. |
| `reports/repo-truth-extractor/pre_live_gate_v25/...` | untracked generated tree | `GENERATED_OR_IGNORED` | `leave_uncommitted` | no | Generated validator outputs; evidence only, not code recovery. |
| `services/repo-truth-extractor/tests/test_run_extraction_v5_cost_cap.py` | untracked | `UNRESOLVED` | `leave_uncommitted` | no | TP001 test depends on unresolved mixed runner code in `run_extraction_v5.py`. |
| `services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py` | untracked | `UNRESOLVED` | `leave_uncommitted` | no | Mixed TP002 and TP003 assertions depend on unresolved mixed runner code in `run_extraction_v5.py`. |

## Recovery Decision

- Recover now: `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- Recover now: `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
- Leave uncommitted: all docs deletions, `run_extraction_v5.py`, untracked spend-cap and runner-adjacent files, generated outputs, and tool scratch state
