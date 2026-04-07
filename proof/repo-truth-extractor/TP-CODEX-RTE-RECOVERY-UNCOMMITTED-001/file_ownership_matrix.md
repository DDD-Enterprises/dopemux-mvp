# TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001 File Ownership Matrix

## Bucket Definitions

- `RECOVER_TP001`: spend ledger truth, runtime spend cap enforcement, forced-breach proof behavior, recovery semantics, batch accounting contract wording
- `RECOVER_TP002`: validator authority, repair provenance, bounded validator classification, PAL/provider readiness classification
- `RECOVER_TP003`: bounded live CLI contract, bounded live pricing authority, step-scoped spend/cap route narrowing, bounded live run artifact audit support
- `CANDIDATE_TP004`: execution scope consistency, authoritative run truth, artifact contradiction handling
- `UNRELATED_DRIFT`: unrelated tracked or untracked changes outside this recovery packet
- `GENERATED_OR_IGNORED`: generated evidence, logs, scratch outputs, local worktrees
- `UNRESOLVED`: mixed ownership or incomplete dependency chain; do not commit in recovery

## Matrix

| Path | State | Bucket | Reason | Target Commit | Commit Now |
| --- | --- | --- | --- | --- | --- |
| `docs/05-audit-reports/ADR-197-P0-STAGE1-STAGE2-IMPLEMENTATION-PR-PLAN-2026-02-06.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/AUDIT-SUMMARY-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/COMPLETE-AUDIT-SUMMARY-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/DEPLOYMENT-READY-SUMMARY.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/EXHAUSTIVE-AUDIT-PLAN.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/FINAL-AUDIT-REPORT-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/FINAL-AUDIT-REPORT.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/OPTIMIZED-AUDIT-PLAN.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/PHASE-1-COMPLETE.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/PHASE-3-REMAINING-SERVICES-QUICK-SCAN.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/PHASE-4-DOCUMENTATION-VALIDATION-COMPLETE.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/PHASE-6-INTEGRATION-TESTS-ASSESSMENT.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/PLAN.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/ROADMAP-REMAINING-WORK.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/START-HERE-NEXT-SESSION.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `docs/05-audit-reports/ULTIMATE-AUDIT-COMPLETION-2025-10-16.md` | deleted | `UNRELATED_DRIFT` | Docs deletion unrelated to repo-truth-extractor prelive recovery. | `leave_uncommitted` | no |
| `services/repo-truth-extractor/run_extraction_v5.py` | modified | `UNRESOLVED` | Mixed file spans TP001 spend cap, TP002 repair provenance, TP003 validator enforcement, and plumbing; file-level packet ownership is not singular. | `leave_uncommitted` | no |
| `services/repo-truth-extractor/validate_pre_live_gate_v25.py` | modified | `RECOVER_TP002` | Adds bounded validator conditions/operator verdict classification and route-readiness behavior, which matches TP002/002A. | `commit_2_tp002_code` | yes |
| `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py` | modified | `RECOVER_TP002` | Regression coverage for bounded validator/operator-verdict semantics in TP002/002A. | `commit_3_tp002_tests` | yes |
| `config/pricing.yaml` | untracked | `UNRESOLVED` | TP001-related, but not safely committable without separating matching runner changes. | `leave_uncommitted` | no |
| `services/repo-truth-extractor/tests/test_run_extraction_v5_cost_cap.py` | untracked | `UNRESOLVED` | TP001 tests depend on unresolved mixed runner file. | `leave_uncommitted` | no |
| `services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py` | untracked | `UNRESOLVED` | Mixed TP002/TP003 test file depends on unresolved mixed runner file. | `leave_uncommitted` | no |
| `reports/repo-truth-extractor/pre_live_gate_v25/...` | untracked generated tree | `GENERATED_OR_IGNORED` | Generated validator outputs only. | `leave_uncommitted` | no |
| `.codex-tmp-doc-placement/` | untracked dir | `GENERATED_OR_IGNORED` | Tool scratch directory. | `leave_uncommitted` | no |
| `.codex-worktrees/` | untracked dir | `GENERATED_OR_IGNORED` | Tool worktree cache. | `leave_uncommitted` | no |
| `LIVE_LOG*.txt` | untracked | `GENERATED_OR_IGNORED` | Runtime logs only. | `leave_uncommitted` | no |
| `llm-plans/*.md` | untracked | `UNRELATED_DRIFT` | Planning notes outside packet scope. | `leave_uncommitted` | no |

## Staging Map

- `commit_1_docs_proof`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/worktree_inventory.md`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/file_ownership_matrix.md`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/IMPLEMENTER_REPORT.md`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/verification_commands.txt`

- `commit_2_tp002_code`
  - `services/repo-truth-extractor/validate_pre_live_gate_v25.py`

- `commit_3_tp002_tests`
  - `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`

- `commit_4_docs_proof_closeout`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/PROOF.json`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/unresolved_drift_register.md`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/IMPLEMENTER_REPORT.md`
