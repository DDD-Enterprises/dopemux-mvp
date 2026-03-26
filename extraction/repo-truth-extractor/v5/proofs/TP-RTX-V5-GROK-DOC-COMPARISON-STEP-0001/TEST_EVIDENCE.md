---
title: "TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001 \u2014 Test Evidence"
type: reference
status: active
prelude: Exact commands and results for the Grok comparison lane test suite.
tags:
- comparison-lane
- tests
- evidence
- v5
id: TEST_EVIDENCE
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-13'
last_review: '2026-03-13'
next_review: '2026-06-11'
---
# Test Evidence

## Test Commands

```bash
# Run comparison lane tests only
pytest -q services/repo-truth-extractor/tests/test_comparison_lane.py \
           services/repo-truth-extractor/tests/test_comparison_summary.py

# Run full service test suite (regression check)
pytest services/repo-truth-extractor/tests/
```

## Results

### Comparison Lane Tests (12 tests)

```
12 passed in ~5s
```

Tests covered:

| Test | Assertion |
|------|-----------|
| `test_comparison_disabled_no_comparison_execution` | T1: comparison=None → no `raw/comparison/` dir |
| `test_comparison_enabled_on_eligible_step_creates_separate_artifacts` | T2: `raw/comparison/xai__grok-4.20-beta/` dir created |
| `test_canonical_outputs_unchanged_when_comparison_runs` | T3: canonical artifact structural fields identical with/without comparison |
| `test_comparison_route_metadata_distinct_from_canonical` | T4: `lane=comparison`, `authoritative=False` in artifact |
| `test_comparison_uses_same_validation_pipeline` | T5: `parse_json_from_response` called for comparison output |
| `test_comparison_failure_does_not_affect_canonical_success` | T6: source inspection + `run_comparison_lane` non-blocking with raising LLM |
| `test_invalid_comparison_step_fails_with_clear_error` | T7: ValueError for ineligible step |
| `test_comparison_resume_isolation` | T8: comparison SKIP ↔ canonical RERUN, and vice versa |
| `test_comparison_summary_fields_complete` | Summary JSON has all required keys |
| `test_comparison_summary_counts_accurate` | pass/fail counts match input |
| `test_comparison_summary_route_recorded` | provider/model in summary |
| `test_comparison_summary_written_to_disk` | JSON + MD files written at expected paths |

### Full Regression Suite (286 tests)

```
286 passed in 11.08s
```

No regressions introduced. All pre-existing tests pass.

## YAML Validation

```bash
python -c "import yaml; yaml.safe_load(open('templates/routing.yaml'))"
python -c "import yaml; yaml.safe_load(open('docker/mcp-servers-source/litellm/litellm.config.yaml'))"
```

Both exit 0 (valid YAML).

## Static Checks

```bash
# Verify COMPARISON_ELIGIBLE_STEPS is accessible
python3 -c "
import importlib.util, sys
sys.path.insert(0, 'services/repo-truth-extractor')
spec = importlib.util.spec_from_file_location('run_extraction_v5',
    'services/repo-truth-extractor/run_extraction_v5.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print('Eligible steps:', sorted(m.COMPARISON_ELIGIBLE_STEPS))
print('is_comparison_enabled:', m.is_comparison_enabled)
print('validate_comparison_steps:', m.validate_comparison_steps)
print('run_comparison_lane:', m.run_comparison_lane)
print('generate_comparison_summary:', m.generate_comparison_summary)
"
```

Output:
```
Eligible steps: ['A9', 'B9', 'G9', 'H9', 'R9', 'S9', 'T9', 'W9', 'X9']
is_comparison_enabled: <function is_comparison_enabled at 0x...>
validate_comparison_steps: <function validate_comparison_steps at 0x...>
run_comparison_lane: <function run_comparison_lane at 0x...>
generate_comparison_summary: <function generate_comparison_summary at 0x...>
```

## ⚠️ Live Run Safety Note

**Do NOT run `run_extraction_v5.py` directly** — even with `--dry-run`. Per repo safety
policy, all validation is performed via tests and static analysis only.
A single accidental run cost $10 in March 2026. This mandate is absolute.
