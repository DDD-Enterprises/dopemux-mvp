# Plan: RTE Audit Fixes (CA-001, CA-003)

## Objective
Address the corrective actions identified in the DMX-RTE-AUDIT-2026-04-23 audit report to ensure the Repo Truth Extractor (RTE) pipeline is fully compliant with v5 standards, free of legacy drift, and properly gates live execution with PAL validation.

## Scope & Impact
- `services/repo-truth-extractor/rte_promptset.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
- `pal_validation.json` (new file)

## Implementation Steps

### 1. CA-001: Migrate Phase S to Registry-Backed Prompt Architecture
- **Update `rte_promptset.py`:** Remove the legacy override logic for Phase S (`set_active_s_prompts_mode` and `get_active_s_prompts_mode` emitting warnings and forcing legacy). Update these functions to embrace the registry-backed pipeline (like Phase SP).
- **Update `run_extraction_v5.py`:** Ensure Phase S execution logic correctly resolves its prompts using the registry-backed functions (`resolve_phase_s_prompts`) rather than relying on legacy fallback structures.

### 2. CA-003: Formalize PAL Validation File Location
- **Create Baseline File:** Create `pal_validation.json` at the repository root containing a minimal valid structure (e.g., `{"routes": []}`).
- **Update Validator:** Modify `services/repo-truth-extractor/validate_pre_live_gate_v25.py` so that if `config.pal_validation_file` is not explicitly provided via arguments, it defaults to checking `REPO_ROOT / "pal_validation.json"`. This ensures the gate naturally finds the file without requiring extra command-line flags during standard execution.

## Verification & Testing
- Run `pytest services/repo-truth-extractor/tests/` to ensure the changes to Phase S prompt resolution do not break critical tests or promptset linting.
- Perform a dry run: `python services/repo-truth-extractor/run_extraction_v5.py --phase S --dry-run` to verify Phase S executes correctly via the registry.
- Run the pre-live validator: `python services/repo-truth-extractor/validate_pre_live_gate_v25.py --target-policy cost` and verify it automatically locates and parses the new `pal_validation.json`.
