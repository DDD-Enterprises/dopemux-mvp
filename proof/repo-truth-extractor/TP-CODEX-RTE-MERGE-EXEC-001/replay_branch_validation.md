# Replay Branch Validation

## Commands Run

```bash
git status --short
python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/validate_pre_live_gate_v25.py
pytest -q services/repo-truth-extractor/tests/ -k "cost_cap or validator or phase_execution_step_filter or validator_repair_provenance"
env XAI_API_KEY="$XAI_API_KEY" python services/repo-truth-extractor/validate_pre_live_gate_v25.py --target-policy balanced_grok_openrouter --target-phases A --step A2 --allow-online-preflight
git diff --stat main...HEAD
```

## Results

- `git status --short`: clean
- `py_compile`: passed
- targeted pytest slice: passed
  - output: `29 passed`
- validator command:
  - first attempt failed because replay conflict resolution dropped validator step-scope integrity
  - bounded repair applied and committed as `c7250ecaf`
  - second attempt passed with:
    - `verdict = CONDITIONAL_GO`
    - `operator_verdict = GO_NOW`
    - no run-scoped blockers
    - only condition: `PAL_REQUIRED_UNAVAILABLE`
- bounded diff versus `main`:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/validate_pre_live_gate_v25.py`

## Final Validation Status

- replay branch integrity: `PASS`
- bounded validator integrity for `A/A2`: `PASS`
- replay branch clean after validation: `PASS`
