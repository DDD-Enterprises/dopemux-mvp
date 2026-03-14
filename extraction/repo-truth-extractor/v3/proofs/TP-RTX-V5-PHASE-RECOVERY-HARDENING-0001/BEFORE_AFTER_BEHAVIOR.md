# Before/After Behavior — TP-RTX-V5-PHASE-RECOVERY-HARDENING-0001

## Case 1: HOMECTRL_QA item with `issues: []`

### Before (broken)

```python
# describe_contract_failure() at line 462:
if item.get(key) in (None, "", []):
    reason = "contract_empty_key:issues"
    return {"failure_reason": "contract_empty_key:issues", ...}
# Result: RERUN triggered
```

### After (fixed)

```python
allow_empty_arrays = {"issues", "status"}  # from allow_empty_array_fields
val = item.get("issues")  # val = []
empty_vals = (None, "")   # [] excluded for "issues"
if val in empty_vals:     # [] not in (None, "") → False → no failure
    ...
# Result: describe_contract_failure() returns None → SKIP
```

**Concrete payload example:**
```json
{
  "artifact_name": "HOMECTRL_QA.json",
  "payload": {
    "schema": "HOMECTRL_QA@v1",
    "items": [{
      "id": "H9:partition1:file1",
      "path": "home/user/.config/some_tool.py",
      "line_range": [1, 50],
      "status": "PASS",
      "checks": ["file_exists", "syntax_valid"],
      "issues": [],
      "evidence": ["no issues detected"]
    }]
  }
}
```
- **Before**: `contract_empty_key:issues` → RERUN → repair → same result → infinite loop
- **After**: passes contract gate → SKIP

---

## Case 2: CLI_COMMAND_SURFACE item with `subcommands: []`

### Before (broken)

```json
{
  "id": "cmd:git",
  "path": "src/cli/git_wrapper.py",
  "line_range": [1, 100],
  "subcommands": [],
  "evidence": ["git has no wrapper subcommands"]
}
```
- **Before**: `contract_empty_key:subcommands` → RERUN
- **After**: `[]` allowed → SKIP

---

## Case 3: Resume with `failure_type` in `request_meta`

### Before (broken)

```json
{
  "phase": "H", "step_id": "H9", "partition_id": "H_P0001",
  "request_meta": {"failure_type": "schema", "model": "gpt-4o"},
  "artifacts": [{"artifact_name": "HOMECTRL_QA.json", "payload": {...valid...}}]
}
```

Code at line 8218:
```python
if isinstance(request_meta, dict) and request_meta.get("failure_type"):
    return False, "failure_type_request_meta"
# Result: immediate RERUN before artifacts are ever checked
```

### After (fixed)

```python
_has_request_meta_failure_type = True
logger.warning("[RESUME_WARN] failure_type in request_meta but continuing to artifact check ...")
# continues → artifact check → contract gate → issues: [] normalized to [] → SKIP
```
- **Before**: immediate RERUN (artifacts never checked)
- **After**: warning logged, artifacts validated, if valid → SKIP

---

## Case 4: `normalize_required_array_fields` coercion

**Input item with `issues: None`:**
```python
items = [{"id": "x", "path": "a.py", "line_range": [1,5], "issues": None, "status": "PASS",
           "checks": ["c1"], "evidence": ["e1"]}]
artifact_meta = {"allow_empty_array_fields": ["issues", "status"]}
norm_items, coercions = normalize_required_array_fields(items, artifact_meta)
```

**Output:**
```python
norm_items = [{"id": "x", "path": "a.py", "line_range": [1,5], "issues": [], "status": "PASS",
               "checks": ["c1"], "evidence": ["e1"]}]
coercions = [{"item_id": "x", "field": "issues", "from_type": "NoneType", "to_type": "list"}]
```
Note: `status` = `"PASS"` (a non-empty string) — not coerced because it's neither `None` nor `""`.
