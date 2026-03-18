# Test Evidence — TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001

## Command

```bash
pytest -q services/repo-truth-extractor/tests/test_tp_rtx_v5_phase_recovery_hardening.py -v
```

## Result

```
23 passed in 1.03s
```

## Full Test Run (All Tests — No Regressions)

```bash
pytest services/repo-truth-extractor/tests/ \
  --ignore=services/repo-truth-extractor/tests/test_live_llm_guard.py \
  --ignore=services/repo-truth-extractor/tests/test_provider_preflight_openrouter.py \
  -q
```

```
266 passed in 10.99s
```

## Test Groups Confirmed Passing

| Group | Tests | Status |
|-------|-------|--------|
| T1 — H9 issues shape variants | 6 tests (5 parametrized + 2 direct) | PASS |
| T2 — Resume validation | 4 tests (a/b/c/d scenarios) | PASS |
| T3 — Phase A subcommands regression | 6 tests (5 parametrized + 1 contract_map) | PASS |
| T4 — Cross-phase REPOCTRL_QA | 7 tests (4 parametrized + 3 assertions) | PASS |
| **Total** | **23** | **PASS** |

## Key Behavioral Assertions

1. `describe_contract_failure()` returns `None` for `HOMECTRL_QA` item with `issues: []`
   when `allow_empty_array_fields` contains `"issues"`.
2. `normalize_required_array_fields()` coerces `None`/`""`/missing → `[]` for fields in
   `allow_empty_array_fields`, recording coercions.
3. `validate_success_partition_output()` returns `True, "valid_success"` for a partition file
   that has `failure_type` in `request_meta` but valid artifacts.
4. `validate_success_partition_output()` returns `False` for a file with `failure_type` in
   `request_meta` AND missing/empty artifacts.
5. `CLI_COMMAND_SURFACE.json` artifact in phase_contract_map has `subcommands` in
   `allow_empty_array_fields`.
6. `REPOCTRL_QA.json` and `HOMECTRL_QA.json` artifacts in phase_contract_map have `issues`
   in `allow_empty_array_fields`.
