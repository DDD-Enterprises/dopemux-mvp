# Root Cause Summary — TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001

## Version / Path Mismatch (Non-Actionable)

- **v5 runner**: `services/repo-truth-extractor/run_extraction_v5.py`
- **Run artifacts output path**: `extraction/repo-truth-extractor/v3/runs/FULL_RUN/`
  (v3 path convention, no v5/ directory exists)
- **Resolution**: Documented only. The runner uses `V3_RUNS_ROOT` internally as the canonical
  path constant. Code fixes go in the v5 runner; artifact output path stays as-is.

---

## Phase A Root Causes

### A99 / A_P0017 — Structured Output Schema Missing `evidence` in `required` (ALREADY FIXED)

- **Symptom**: OpenAI 400 error, `failure_type: payload`
- **Root cause**: `_generic_item_schema()` in `structured_output_contracts.py` did not include
  all properties in the `required` array for the strict JSON schema sent to OpenAI.
- **Fix**: Commit `8b0c30ebc` — `fix: include all properties in strict schema required array`.
  `_generic_item_schema()` at line 235 now computes `all_required = sorted(properties.keys())`.
- **Status**: Non-actionable. Already fixed and landed.

### A12 / A_P0004 — `contract_empty_key:subcommands` in `CLI_COMMAND_SURFACE.json`

- **Symptom**: Model correctly emits `subcommands: []` (no sub-commands for this command),
  but the contract gate rejects it with `contract_empty_key:subcommands`.
- **Root cause**: `describe_contract_failure()` in `structured_output_contracts.py` treated
  `[]` identically to `None`/`""` for ALL required fields — `(None, "", [])` was the rejection
  tuple. An empty array is semantically valid for `subcommands`.
- **Fix**: Add `allow_empty_array_fields: [subcommands]` to the `CLI_COMMAND_SURFACE.json`
  artifact entry in `artifacts.yaml`. Propagate through `phase_contract_map.py`.
  Modify `describe_contract_failure()` to skip `[]` rejection for fields in that set.

---

## Phase H Root Causes

### H9 / H_P0001, H_P0006 — `contract_empty_key:issues` in `HOMECTRL_QA.json`

**Two-stage failure:**

1. **Initial partition output**: `artifacts: []` (model returned empty list) →
   produces `missing_artifacts` failure type.
2. **Repair invoked**: repair model returns `HOMECTRL_QA` items with `issues: []`
   or `issues` missing → repair output fails `contract_empty_key:issues` → infinite
   fail-loop because repair also produces `[]`.

- **Root cause**: `describe_contract_failure()` uses `item.get(key) in (None, "", [])` for
  ALL required fields. `issues` is in `prompt_required_item_fields` (from
  `PROMPT_A99_MERGE___QA.md` line 206: `required_item_fields: id, status, checks, issues,
  evidence`). An empty `issues: []` is semantically valid ("no issues found"). The repair
  also emits `[]` when there are no issues, creating an infinite failure loop.
- **Fix**: Same mechanism as A12. Add `allow_empty_array_fields: [issues, status]` to both
  `HOMECTRL_QA.json` and `REPOCTRL_QA.json` in `artifacts.yaml`.

---

## Resume Short-Circuit Root Cause

### `failure_type_request_meta` — Immediate Hard-Fail on Valid Artifacts

- **Code path**: `validate_success_partition_output()` in `run_extraction_v5.py`,
  lines 8215–8219 (pre-fix).
- **Symptom**: H9 raw partition files (`H9__H_P0001.json`) contain `failure_type: "schema"`
  in `request_meta` (failure metadata embedded in the output file from a prior failed attempt).
  Resume reads this file and immediately returns `False, "failure_type_request_meta"` at
  line 8219 — BEFORE checking artifacts or running the contract gate.
- **Impact**: Partitions with valid artifacts (items with `issues: []`) were flagged for RERUN
  even when their artifact content was fully valid.
- **Fix**: Demote `failure_type_request_meta` from a hard-fail to a logged warning. Continue
  to artifact presence and contract gate checks. Only return False if those checks also fail.
