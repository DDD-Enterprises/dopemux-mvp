---
title: repo-truth-extractor staged patch salvage classification
doc_type: audit-report
status: active
created: '2026-03-26'
updated: '2026-03-26'
owner: codex
summary: Classification of archived staged extractor changes before selective salvage into the recovery branch.
---

# Salvage Classification

Source artifact:
`reports/work-recovery/2026-03-26/primary-worktree-extractor-staged/staged.patch`

## Salvageable extractor work
- `services/repo-truth-extractor/tests/_v5_smoke_helpers.py`
  - Reason: isolated offline helper for deterministic smoke verification.
- `services/repo-truth-extractor/tests/fixtures/golden_repo_min/README.md`
  - Reason: minimal offline fixture content for smoke coverage.
- `services/repo-truth-extractor/tests/fixtures/golden_repo_min/docs/example.md`
  - Reason: minimal offline fixture content for smoke coverage.
- `services/repo-truth-extractor/tests/test_v5_golden_fixture_smoke.py`
  - Reason: deterministic offline artifact smoke test.
- `services/repo-truth-extractor/tests/test_v5_resume_smoke.py`
  - Reason: resume and existing-run validation coverage using offline fixtures.
- `services/repo-truth-extractor/tests/test_v5_verify_phase_output_smoke.py`
  - Reason: phase verification smoke coverage using offline fixtures.
- `services/repo-truth-extractor/tests/test_v5_observability_improvements.py`
  - Reason: focused coverage for connection reuse, retry-delay accounting, and repair-counter snapshot semantics.
- `services/repo-truth-extractor/tests/test_repair_counters_thread_safety.py`
  - Reason: focused concurrency coverage for global repair counters.
- `services/repo-truth-extractor/run_extraction_v5.py` (selected hunks only)
  - Reason: minimal runtime support for the salvageable observability and thread-safety tests.
  - Accepted hunk classes only: shared HTTP session helper, retry-delay accumulation, repair-counter lock and snapshot, coverage-manifest emission of repair counters.

## Needs manual reimplementation
- `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
  - Reason: broad contract churn and model-routing rewrites; provenance too weak for wholesale salvage.
- `services/repo-truth-extractor/run_extraction_v3.py`
  - Reason: patch mixes routing refresh, execution-step filtering, salvage behavior changes, and contract changes.
- `services/repo-truth-extractor/run_extraction_v5.py` (all non-selected hunks)
  - Reason: patch mixes unverified model changes, new routing policies, prompt inventory drift, and audit behavior not yet revalidated.
- `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
  - Reason: depends on `validate_pre_live_gate_v25.py`, which is not present in the verified recovery baseline.
- `services/repo-truth-extractor/tests/test_audit_tp008_drift.py`
  - Reason: coupled to routing/model contract changes not yet re-verified.
- `services/repo-truth-extractor/tests/test_phase_d_contract_hardening.py`
  - Reason: coupled to contract-lane route changes not yet re-verified.
- `services/repo-truth-extractor/tests/test_phase_d_contract_map.py`
  - Reason: coupled to contract-lane route changes not yet re-verified.
- `services/repo-truth-extractor/tests/test_phase_d_json_salvage.py`
  - Reason: changes parser contract behavior; requires direct runtime review.
- `services/repo-truth-extractor/tests/test_promptpack_v1_v2.py`
  - Reason: coupled to contract-lane route changes not yet re-verified.
- `services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py`
  - Reason: depends on routing/preflight semantics not yet re-verified.
- `services/repo-truth-extractor/tests/test_run_extraction_v3_escalation.py`
  - Reason: coupled to v3 routing/model changes not yet re-verified.
- `services/repo-truth-extractor/tests/test_run_extraction_v3_model_routing.py`
  - Reason: coupled to v3 routing/model changes not yet re-verified.
- `services/repo-truth-extractor/tests/test_run_extraction_v5_soft_gate_logging.py`
  - Reason: depends on unresolved routing target changes.
- `services/repo-truth-extractor/tests/test_run_extraction_v5_ui_events.py`
  - Reason: depends on unresolved routing target changes.

## Historical drift / unrelated
- None observed in the archived staged patch.
- The patch is extractor-only, but several changes are deferred because their runtime authority is unresolved, not because they are unrelated.
