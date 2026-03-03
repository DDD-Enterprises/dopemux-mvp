---
id: PHASE0_DETERMINISM_IMPLEMENTATION
title: Phase0 Determinism Implementation
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Phase0 Determinism Implementation (reference) for dopemux documentation and
  developer workflows.
---
# Phase 0C Determinism - Implementation Guide

## Objective
Prove extraction outputs are deterministic across workers=1 vs workers=N runs.

## Implementation Status

### ✅ Files Created
1. **`services/repo-truth-extractor/tools/phase0_determinism_check.py`**
   - Main determinism comparison script
   - Compares JSON outputs using SHA256 hashing
   - Handles missing files and content mismatches
   - Generates comprehensive markdown reports

2. **`proof/PLAN.txt`** (updated)
   - Implementation plan for Phase 0C

### 📋 Script Capabilities

#### Features Implemented
- **JSON Normalization**: Sorts keys and uses consistent separators for deterministic comparison
- **SHA256 Hashing**: Robust content comparison
- **Comprehensive Comparison**: Detects missing files and content differences
- **Flexible File Matching**: Supports glob patterns for inclusion/exclusion
- **Detailed Reporting**: Markdown reports with tables and summaries
- **Proper Exit Codes**: 0 for success, 2 for mismatches, 1 for errors

#### Command Line Interface
```bash
# Basic usage
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a <directory_a> \
  --out-b <directory_b> \
  --report proof/PHASE0_DETERMINISM_REPORT.md

# With custom patterns
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a proof/phase0_out_a \
  --out-b proof/phase0_out_b \
  --include-glob "*.json" \
  --ignore-glob "*_timestamp*" \
  --report proof/PHASE0_DETERMINISM_REPORT.md
```

### 🔧 Usage with Current Extraction System

The current `run_extraction_v3.py` script uses a fixed directory structure based on `V3_RUNS_ROOT` and `run_id`. To test determinism:

#### Step 1: Run with workers=1
```bash
# Create run directory for workers=1
RUN_ID_A="determinism_test_a_$(date +%Y%m%d_%H%M%S)"
python services/repo-truth-extractor/run_extraction_v3.py \
  --partition-workers 1 \
  --phase A \
  # ... other required arguments
  # This will output to extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/A_repo_control_plane/
```

#### Step 2: Run with workers=N
```bash
# Create run directory for workers=N
RUN_ID_B="determinism_test_b_$(date +%Y%m%d_%H%M%S)"
python services/repo-truth-extractor/run_extraction_v3.py \
  --partition-workers 4 \
  --phase A \
  # ... same arguments as above
  # This will output to extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/A_repo_control_plane/
```

#### Step 3: Compare outputs
```bash
# Compare the raw output directories
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a "extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/A_repo_control_plane/raw" \
  --out-b "extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/A_repo_control_plane/raw" \
  --report proof/PHASE0_DETERMINISM_REPORT.md
```

### 🎯 Test Results (Verification)

The script has been tested with:
- ✅ **Identical files**: Correctly reports "DETERMINISM PASSED" with exit code 0
- ✅ **Different content**: Correctly detects mismatches with exit code 2
- ✅ **Missing files**: Properly reports files missing in either directory
- ✅ **JSON normalization**: Handles different key ordering and formatting
- ✅ **Error handling**: Graceful handling of unreadable files

### 📁 Report Format

The generated report includes:
- **Metadata**: Timestamp, Python version, directory paths
- **Summary Statistics**: File counts, match/mismatch counts
- **Status Indication**: Clear PASS/FAIL indication
- **Missing Files**: Lists of files missing in each directory
- **Hash Mismatches**: Detailed table with paths and hash values
- **Top Mismatches**: First 50 mismatches for readability

### 🚀 Next Steps

To complete the determinism verification:

1. **Run extraction twice** with identical inputs but different worker counts
2. **Compare outputs** using the determinism check script
3. **Analyze report** to identify any non-deterministic behavior
4. **Fix issues** if mismatches are found (timestamps, randomness, etc.)
5. **Commit results** with the determinism report

### 🔍 Expected Output Structure

The extraction system creates these directories per phase:
```
extraction/repo-truth-extractor/v3/runs/${RUN_ID}/${PHASE}_*/
  ├── inputs/
  ├── raw/          # ← Compare these for determinism
  ├── norm/
  └── qa/
```

Focus on the `raw/` directories for initial determinism testing, as they contain the direct extraction outputs.

### ⚠️ Known Considerations

1. **Timestamps**: If outputs include timestamps, they will cause mismatches
2. **Randomness**: Any random IDs or nonces will break determinism
3. **File Ordering**: JSON key ordering is normalized by the script
4. **Floating Point**: JSON serialization handles floats consistently

### ✅ Acceptance Criteria Met

- ✅ Script exists and handles directory comparison
- ✅ JSON normalization implemented (sort_keys, consistent separators)
- ✅ SHA256 hashing for content comparison
- ✅ Proper exit codes (0 for success, 2 for mismatches)
- ✅ Comprehensive reporting with mismatch details
- ✅ Tested with both matching and differing content

**Ready for actual extraction runs to verify determinism.**
