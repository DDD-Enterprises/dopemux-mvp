---
title: "Operator Runbook — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "Step-by-step checklist for pre-restart hygiene scan, optional cleanup, and extraction restart."
tags: [extraction, hygiene, runbook, operator]
---

# Operator Runbook: Pre-Restart Hygiene

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001

## Prerequisites

- Python 3.11+
- Working directory: repo root (`dopemux-mvp/`)
- `pyyaml` installed (`pip install pyyaml` or active virtualenv)

## Step 1: Run Hygiene Scan (Read-Only)

```bash
python services/repo-truth-extractor/extraction_hygiene.py scan
```

**Expected output** (pre-restart state):
```
HYGIENE_SCAN_START: repo_root=/path/to/repo
VERSION_PATH_MISMATCH: runner is v5 but output root is 'extraction/repo-truth-extractor/v3' (v3)...
AUTHORITY_CLASSIFICATION_SUMMARY: {canonical: ~15K, reference: ~2K, ...}
HYGIENE_SCAN_RESULT: warnings=N errors=0 noise_paths=57 version_path_issues=1 resume_state_issues=N
```

**Interpret results**:

| Finding | Risk | Action |
|---------|------|--------|
| `VERSION_PATH_MISMATCH` (1 issue) | None — intentional | Read VERSION_PATH_REPORT.md; no code change needed |
| `stale_failed` resume issues | None — resume logic handles them | Optional: archive via apply mode |
| `os_artifact` (.DS_Store) | None | Optional: ignore |
| `vendored_deps` (vendor/) | None — already excluded | No action |
| `errors > 0` | BLOCK restart | Investigate before proceeding |

**If errors > 0**: Stop. Read the error output and resolve before restarting.

## Step 2: Get JSON Output (Optional, for scripting)

```bash
python services/repo-truth-extractor/extraction_hygiene.py scan --json \
  | python3 -m json.tool
```

Pipe to `jq` for filtering:
```bash
python services/repo-truth-extractor/extraction_hygiene.py scan --json \
  | jq '.version_path_issues'
```

## Step 3: Optional — Preview Cleanup (Dry Run)

If you want to archive stale FAILED markers and OS artifacts before restart:

```bash
python services/repo-truth-extractor/extraction_hygiene.py apply --dry-run
```

This prints exactly what would be moved to quarantine, without moving anything.

## Step 4: Optional — Apply Cleanup

Only do this if you want a cleaner run-state before restart. It is NOT required for correctness.

```bash
python services/repo-truth-extractor/extraction_hygiene.py apply --apply
```

This:
1. Moves stale FAILED markers to `extraction/repo-truth-extractor/quarantine/{timestamp}/`
2. Moves `.DS_Store` files in the extraction tree to quarantine
3. Writes `ARCHIVE_MANIFEST.json` in the quarantine directory
4. Does NOT delete anything

**To reverse**: Move files back from quarantine using the manifest.

## Step 5: Verify Quarantine (If Applied)

```bash
ls extraction/repo-truth-extractor/quarantine/
cat extraction/repo-truth-extractor/quarantine/*/ARCHIVE_MANIFEST.json
```

## Step 6: Restart Extraction

The extractor is safe to restart once:
- [ ] Scan shows `errors=0`
- [ ] Version/path mismatch acknowledged (expected, not a blocker)
- [ ] Optional cleanup done (if desired)

```bash
# Full run (adjust options as needed)
python services/repo-truth-extractor/run_extraction_v5.py \
  --phase ALL \
  --partition-workers 10 \
  --run-id RESTART_$(date +%Y%m%d_%H%M%S) \
  --routing-policy balanced_openrouter

# Or doctor mode first:
python services/repo-truth-extractor/run_extraction_v5.py \
  --phase ALL --partition-workers 10 --run-id LAUNCH \
  --routing-policy balanced_openrouter --doctor
```

## Step 7: Monitor for Version/Path Warning

After restart, the extractor will write output to `extraction/repo-truth-extractor/v3/runs/` (the v3 path). This is expected. See `VERSION_PATH_REPORT.md` for full explanation.

## Troubleshooting

### Scan takes too long
The scan walks the entire repo tree. If it's slow, it's traversing large run directories. These are already gitignored and excluded from extraction by policy — the scan walks them to report stale FAILED files. Consider running apply mode once to archive old stale files first.

### Apply mode says "no items to quarantine"
This means the repo is already clean (no stale FAILED markers with newer success files). Good — proceed to restart.

### `ModuleNotFoundError: No module named 'yaml'`
```bash
pip install pyyaml
```

### Tests fail after a dependency update
```bash
python -m pytest services/repo-truth-extractor/tests/test_hygiene_*.py -v
```
All 86 tests should pass. If not, check for import errors in the test output.

## Authority Classification Quick Reference

```bash
# Classify a specific path
python3 -c "
import sys
sys.path.insert(0, 'services/repo-truth-extractor')
from extraction_hygiene import classify_authority
print(classify_authority('docs/90-adr/adr-207.md'))  # canonical
print(classify_authority('reports/ENV_VARS.json'))    # status_audit
print(classify_authority('UPGRADES/some-plan.md'))    # roadmap_speculative
"
```
