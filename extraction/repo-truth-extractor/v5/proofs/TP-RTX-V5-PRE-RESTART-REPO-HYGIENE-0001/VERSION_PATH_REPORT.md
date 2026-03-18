---
title: "Version/Path Consistency Report — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "Documents the known v5-runner/v3-output-path mismatch and safe handling decision."
tags: [extraction, version, path-mismatch]
---

# Version/Path Consistency Report

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001  
**Severity**: WARN (not ERROR — intentional for resume compatibility)

## Finding

The active runner is `run_extraction_v5.py` but its output root constant is `V3_EXTRACTION_ROOT`:

```python
# services/repo-truth-extractor/run_extraction_v5.py, lines 280-283
V3_EXTRACTION_ROOT = Path("extraction/repo-truth-extractor/v3")
V3_RUNS_ROOT = V3_EXTRACTION_ROOT / "runs"
V3_LATEST_RUN_FILE = V3_EXTRACTION_ROOT / "latest_run_id.txt"
V3_DOCTOR_ROOT = V3_EXTRACTION_ROOT / "doctor"
```

This means:
- The runner is **v5** in name and functionality
- The output path is **v3** by constant inheritance
- There is **no** `extraction/repo-truth-extractor/v5/` directory for run outputs

## Scanner Detection

```
VERSION_PATH_MISMATCH: runner is v5 but output root is
'extraction/repo-truth-extractor/v3' (v3).
This is intentional for resume compatibility.
To migrate to a v5 output path, create a separate task packet.
```

## Root Cause

The v5 runner was developed by extending the v4/v3 runner. The `V3_EXTRACTION_ROOT` constant was inherited to preserve resume compatibility with existing 204+ v3 runs. Renaming it to `V5_EXTRACTION_ROOT` would break:
1. `compute_resume_decision()` logic referencing `V3_RUNS_ROOT`
2. All existing run directory lookups
3. `V3_LATEST_RUN_FILE` — the file tracking the most recent run ID

## Decision

**Do NOT change `V3_EXTRACTION_ROOT` in this packet.**

The TP specifies "implement only the minimal safe correction or explicit warning needed." The safe action is:
- Detect the mismatch via preflight check ✅
- Document the rationale ✅
- Warn operators before restart ✅

If output path migration to `v5/` is desired, create a separate task packet focused on:
1. Verifying all resume references
2. Migrating or symlinking existing runs
3. Running a full test pass against the new path

## Hygiene Policy Reference

See `config/extraction_hygiene/hygiene_policy.yaml` → `version_path_wiring`:
```yaml
version_path_wiring:
  runner: services/repo-truth-extractor/run_extraction_v5.py
  output_root: extraction/repo-truth-extractor/v3
  mismatch: intentional
  severity: warn
  rationale: >
    V3_EXTRACTION_ROOT is an inherited constant for resume compatibility.
    Changing it requires a dedicated migration task packet.
```

## Operator Action

Before restarting extraction, acknowledge this warning. No code change is required.
Run the preflight check to confirm:

```bash
python services/repo-truth-extractor/extraction_hygiene.py scan
# Expected: VERSION_PATH_MISMATCH warning (1 issue, severity=warn)
```
