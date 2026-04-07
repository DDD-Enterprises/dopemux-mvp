# Coherence Verdict

- Authoritative routing policy: `balanced_grok_openrouter`
- Authoritative run id: `tp_codex_rte_prelive_005_phase_a_step_a2_v13`
- Source of truth:
  - `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-005/PROOF.json`
  - `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-005/live_run_execution_record.md`
  - `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260405T090026Z/VALIDATION_SCOPE.json`
  - `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260405T090026Z/ONLINE_PREFLIGHT_RESULTS.json`
- Wrong artifacts before repair:
  - `live_execution_plan.md`
  - `bounded_live_validator_recheck.md`
  - `IMPLEMENTER_REPORT.md`
  - `verification_commands.txt`
- Mismatch source: hand-authored proof-bundle documentation drift from an earlier `balanced_xai` attempt, not runtime invocation drift and not proof-writer code drift.
- Post-repair result: the authoritative packet artifacts now agree on routing policy and run identity.
