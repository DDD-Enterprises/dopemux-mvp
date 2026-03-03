---
id: DETERMINISM_COMMANDS
title: Determinism Commands
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Determinism Commands (reference) for dopemux documentation and developer
  workflows.
---
# Phase 0C Determinism Test - Exact Commands

## Current Extraction Command Template

Based on the actual `run_extraction_v3.py` script, here are the exact commands to run for determinism testing:

## Run A (workers=1)

```bash
RUN_ID_A="determinism_a_$(date +%Y%m%d_%H%M%S)"
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_A" \
  --phase A \
  --partition-workers 1
```

## Run B (workers=4)

```bash
RUN_ID_B="determinism_b_$(date +%Y%m%d_%H%M%S)"
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_B" \
  --phase A \
  --partition-workers 4
```

## Compare Outputs

```bash
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a "extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/A_repo_control_plane/raw" \
  --out-b "extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/A_repo_control_plane/raw" \
  --report proof/PHASE0_DETERMINISM_REPORT.md
```

## Complete One-Liner

```bash
# Run A
RUN_ID_A="determinism_a_$(date +%Y%m%d_%H%M%S)" && python services/repo-truth-extractor/run_extraction_v3.py --run-id "$RUN_ID_A" --phase A --partition-workers 1

# Run B
RUN_ID_B="determinism_b_$(date +%Y%m%d_%H%M%S)" && python services/repo-truth-extractor/run_extraction_v3.py --run-id "$RUN_ID_B" --phase A --partition-workers 4

# Compare
python services/repo-truth-extractor/tools/phase0_determinism_check.py --out-a "extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/A_repo_control_plane/raw" --out-b "extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/A_repo_control_plane/raw" --report proof/PHASE0_DETERMINISM_REPORT.md
```

## Notes

1. **Phase Selection**: Testing phase `A` (repo control plane) first as it's foundational
2. **Worker Counts**: Comparing 1 worker (sequential) vs 4 workers (concurrent)
3. **Output Directories**: The script outputs to `extraction/repo-truth-extractor/v3/runs/{RUN_ID}/{PHASE}_*/raw/`
4. **Determinism Check**: The comparison script normalizes JSON and compares SHA256 hashes

## Expected Behavior

- If deterministic: Exit code 0, report shows "DETERMINISM PASSED"
- If non-deterministic: Exit code 2, report shows specific file mismatches

## Additional Arguments

For more comprehensive testing, you may want to add:
- `--dry-run` for testing without actual API calls
- Specific phase configurations as needed
- Additional flags based on your specific requirements

The core difference between Run A and Run B is **only** the `--partition-workers` value, ensuring all other inputs are identical.
