---
title: "Test Evidence — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "Exact test commands and results proving all 86 hygiene tests pass."
tags: [extraction, hygiene, tests, evidence]
---

# Test Evidence

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001  
**Result**: **86/86 tests pass**

## Test Command

```bash
cd /path/to/dopemux-mvp

python -m pytest \
  services/repo-truth-extractor/tests/test_hygiene_noise_detection.py \
  services/repo-truth-extractor/tests/test_hygiene_dry_run_safety.py \
  services/repo-truth-extractor/tests/test_hygiene_authority.py \
  services/repo-truth-extractor/tests/test_hygiene_version_path.py \
  services/repo-truth-extractor/tests/test_hygiene_resume_state.py \
  services/repo-truth-extractor/tests/test_hygiene_quarantine.py \
  services/repo-truth-extractor/tests/test_hygiene_nondestructive.py \
  -v --no-header
```

## Test Output (abbreviated)

```
collected 86 items

services/repo-truth-extractor/tests/test_hygiene_noise_detection.py .............  [15%]
services/repo-truth-extractor/tests/test_hygiene_dry_run_safety.py ......         [22%]
services/repo-truth-extractor/tests/test_hygiene_authority.py ...............      [74%]
services/repo-truth-extractor/tests/test_hygiene_version_path.py .....             [80%]
services/repo-truth-extractor/tests/test_hygiene_resume_state.py ......            [87%]
services/repo-truth-extractor/tests/test_hygiene_quarantine.py ......              [94%]
services/repo-truth-extractor/tests/test_hygiene_nondestructive.py .....          [100%]

============================== 86 passed in 0.19s ==============================
```

## Test Coverage by Requirement

| Test File | Requirement | Tests | Result |
|-----------|-------------|-------|--------|
| `test_hygiene_noise_detection.py` | T1: Noise-path detection | 13 | ✅ PASS |
| `test_hygiene_dry_run_safety.py` | T2: Dry-run makes no mutations | 6 | ✅ PASS |
| `test_hygiene_quarantine.py` | T3: Apply-mode quarantine + manifest | 6 | ✅ PASS |
| `test_hygiene_authority.py` | T4: Authority classification correctness | 45 | ✅ PASS |
| `test_hygiene_version_path.py` | T5: Version/path mismatch detection | 5 | ✅ PASS |
| `test_hygiene_resume_state.py` | T6: Resume-state hazard detection | 6 | ✅ PASS |
| `test_hygiene_nondestructive.py` | T7: Canonical source never mutated | 5 | ✅ PASS |

## Live Scan Evidence

Ran against the real repo on 2026-03-14:

```
HYGIENE_SCAN_START: repo_root=/path/to/dopemux-mvp
VERSION_PATH_MISMATCH: runner is v5 but output root is
  'extraction/repo-truth-extractor/v3' (v3).
  This is intentional for resume compatibility.
AUTHORITY_CLASSIFICATION_SUMMARY:
  {'canonical': 15328, 'reference': 1967, 'status_audit': 616,
   'roadmap_speculative': 622, 'generated': 157577}
HYGIENE_SCAN_RESULT: warnings=7431 errors=0 noise_paths=57
  version_path_issues=1 resume_state_issues=7373
```

Key findings verified:
- ✅ Version/path mismatch detected (v5 runner → v3 output path)
- ✅ 57 noise paths flagged (mostly `.DS_Store` and `vendor/`)
- ✅ 7,373 stale FAILED markers detected (all lower risk — have corresponding success files)
- ✅ No errors

## Note on `pytest.ini`

Root `pytest.ini` sets `norecursedirs = services` so these tests do NOT run with `pytest tests/` alone.
Always run them via explicit path:

```bash
python -m pytest services/repo-truth-extractor/tests/test_hygiene_*.py
```
