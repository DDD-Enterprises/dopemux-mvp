# Changeset Map — TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001

## File 1: `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

### REPOCTRL_QA.json (line ~43)
Added:
```yaml
  allow_empty_array_fields:
  - issues
  - status
```

### HOMECTRL_QA.json (line ~921)
Added:
```yaml
  allow_empty_array_fields:
  - issues
  - status
```

### CLI_COMMAND_SURFACE.json (line ~1909)
Added:
```yaml
  allow_empty_array_fields:
  - subcommands
```

---

## File 2: `services/repo-truth-extractor/lib/phase_contract_map.py`

### `_artifact_rules_by_key()` (line ~86–98)
Added to the returned dict for each artifact rule:
```python
"allow_empty_array_fields": [
    str(value).strip()
    for value in row.get("allow_empty_array_fields", [])
    if str(value).strip()
],
```

### `compile_phase_contract_map()` artifacts_payload block (line ~288–300)
Added to `artifacts_payload[artifact_name]`:
```python
"allow_empty_array_fields": list(artifact_rule.get("allow_empty_array_fields") or []),
```

---

## File 3: `services/repo-truth-extractor/lib/structured_output_contracts.py`

### `describe_contract_failure()` (line ~434–472)
Added after `required_keys = sorted(...)`:
```python
allow_empty_arrays = set(artifact_meta.get("allow_empty_array_fields") or [])
```

Changed the empty-value check from:
```python
if item.get(key) in (None, "", []):
```
To:
```python
val = item.get(key)
empty_vals: tuple = (None, "") if key in allow_empty_arrays else (None, "", [])
if val in empty_vals:
```

### New function: `normalize_required_array_fields()`
Added after `artifacts_pass_contract_gate()`:
- Accepts `items: List[Dict]` and `artifact_meta: Dict`
- For each field in `allow_empty_array_fields`: coerces `None`, `""`, or missing → `[]`
- Returns `(normalized_items, coercions)` where each coercion records `item_id`, `field`,
  `from_type`, `to_type`

---

## File 4: `services/repo-truth-extractor/run_extraction_v5.py`

### Import block (line ~89–142)
Added imports:
```python
artifact_contract as _artifact_contract,
normalize_required_array_fields,
```
Both in the `try` (lib import) and `except` (dynamic module load) paths.

### `validate_success_partition_output()` — Resume fix (line ~8215–8219)
Changed hard-fail on `failure_type_request_meta` to a logged warning:
```python
_has_request_meta_failure_type = isinstance(request_meta, dict) and bool(
    request_meta.get("failure_type")
)
if _has_request_meta_failure_type:
    logger.warning(
        "[RESUME_WARN] failure_type in request_meta but continuing to artifact check ..."
    )
```
Execution continues to artifact presence and contract gate checks.

### `validate_success_partition_output()` — Pre-gate normalization
Before calling `artifacts_pass_contract_gate()`, iterates artifacts and calls
`normalize_required_array_fields(art_payload["items"], art_meta)` for each, logging
each coercion. Replaces artifacts with normalized versions before the contract check.

---

## File 5: `services/repo-truth-extractor/tests/test_tp_rtx_v5_phase_recovery_hardening.py` (NEW)

Test groups:
- **T1**: `TestT1H9IssuesShapeVariants` — parametrized over 5 issues field variants
- **T2**: `TestT2ResumeValidation` — 4 resume decision scenarios (a/b/c/d)
- **T3**: `TestT3PhaseASubcommandsRegression` — parametrized over 5 subcommands variants
- **T4**: `TestT4CrossPhaseRepoctrlQa` — parametrized + contract_map assertions
