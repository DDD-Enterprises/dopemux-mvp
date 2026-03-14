---
title: "Run-State Hygiene Report — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "Documents stale FAILED markers and resume-state hazards found across v3/v4 run directories."
tags: [extraction, resume, run-state, hygiene]
---

# Run-State Hygiene Report

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001  
**Generated**: 2026-03-14

## Summary

| Metric | Count |
|--------|-------|
| Resume-state issues found | 7,373 |
| Stale FAILED markers (have a newer success file) | 7,373 |
| Orphan FAILED markers (no success file) | 0 |
| v3 run directories | ~204 |
| v4 run directories | ~14 |

## What Are Stale FAILED Files?

The extractor writes `.FAILED.json` or `.FAILED.txt` sidecar files when a step fails. When a step is retried and succeeds, a success `.json` file is written alongside the `.FAILED.*` file. The resume logic in `compute_resume_decision()` (line 8108 of `run_extraction_v5.py`) compares:
- **Success file mtime** vs **FAILED file mtime**
- If success is newer → the FAILED is stale, step will be skipped on resume

**These stale FAILED files do NOT poison resume behavior** — the resume logic already handles them correctly. They are noise from completed runs, not active hazards.

## Hazard Assessment

| Issue Type | Count | Risk to Rerun | Recommended Action |
|-----------|-------|--------------|-------------------|
| `stale_failed` | 7,373 | **NONE** — resume logic ignores them | No action required before restart |
| `orphan_failed` | 0 | Would cause step re-execution | N/A |

## Representative Sample (first 10 stale files)

All from `v3/runs/real_proc_test_20260226_192237/A_repo_control_plane/raw/`:
```
A0__A_P0015.FAILED.txt    (stale — has newer success file)
A2__A_P0004.FAILED.json   (stale — has newer success file)
A2__A_P0018.FAILED.txt    (stale — has newer success file)
A3__A_P0017.FAILED.json   (stale — has newer success file)
A99__A_P0001.FAILED.txt   (stale — has newer success file)
A3__A_P0004.FAILED.txt    (stale — has newer success file)
A5__A_P0010.FAILED.json   (stale — has newer success file)
A1__A_P0009.FAILED.txt    (stale — has newer success file)
A4__A_P0003.FAILED.json   (stale — has newer success file)
A99__A_P0017.FAILED.json  (stale — has newer success file)
```

## Apply-Mode Quarantine

The stale FAILED files can be archived via `extraction_hygiene.py apply`:

```bash
# Preview what would be moved
python services/repo-truth-extractor/extraction_hygiene.py apply --dry-run

# Archive stale FAILED files (non-destructive: moves to quarantine/)
python services/repo-truth-extractor/extraction_hygiene.py apply --apply
```

This is **optional** before restart. The extractor handles stale FAILED files correctly. Quarantining them reduces scan noise and makes future hygiene reports cleaner.

## Resume Safety

The extractor's resume logic is safe to run with stale FAILED files present:
1. `compute_resume_decision()` checks success file mtime > FAILED file mtime
2. If true: step is skipped (already succeeded)
3. If false: step is recomputed (genuine failure, no valid success)

**No pre-cleanup is required for resume correctness.**
