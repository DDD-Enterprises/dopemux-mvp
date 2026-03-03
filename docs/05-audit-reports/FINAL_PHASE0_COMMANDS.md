# 🎯 Phase 0 Gate Commands - Ready to Execute

## ✅ Gate 0B: Serialization - COMPLETE

**Status**: ✅ **PASS** - All 1054 partitions are pickle-safe

**Command already executed**:
```bash
python services/repo-truth-extractor/tools/phase0_serialize_partitions.py \
  --out proof/PHASE0_SERIALIZATION_REPORT.md
```

**Result**: Exit code 0, 1054/1054 partitions pickle-safe

## 🚀 Gate 0C: Determinism - READY TO RUN

### Exact Commands to Execute

#### 1. Run A (workers=1)
```bash
RUN_ID_A="determinism_a_$(date +%Y%m%d_%H%M%S)"
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_A" \
  --phase A \
  --partition-workers 1
```

#### 2. Run B (workers=4)
```bash
RUN_ID_B="determinism_b_$(date +%Y%m%d_%H%M%S)"
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_B" \
  --phase A \
  --partition-workers 4
```

#### 3. Compare Outputs
```bash
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a "extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/A_repo_control_plane/raw" \
  --out-b "extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/A_repo_control_plane/raw" \
  --report proof/PHASE0_DETERMINISM_REPORT.md
```

### Complete Copy-Paste Script

```bash
#!/bin/bash
set -e

echo "=== Phase 0C Determinism Test ==="

# Generate unique run IDs
RUN_ID_A="determinism_a_$(date +%Y%m%d_%H%M%S)"
RUN_ID_B="determinism_b_$(date +%Y%m%d_%H%M%S)"

echo "Run A (workers=1): $RUN_ID_A"
echo "Run B (workers=4): $RUN_ID_B"
echo ""

# Run A: Single worker
echo "Running extraction with workers=1..."
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_A" \
  --phase A \
  --partition-workers 1

echo "✅ Run A completed"
echo ""

# Run B: Multiple workers
echo "Running extraction with workers=4..."
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_B" \
  --phase A \
  --partition-workers 4

echo "✅ Run B completed"
echo ""

# Compare outputs
echo "Comparing outputs for determinism..."
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a "extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/A_repo_control_plane/raw" \
  --out-b "extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/A_repo_control_plane/raw" \
  --report proof/PHASE0_DETERMINISM_REPORT.md

COMPARISON_EXIT_CODE=$?

echo ""
if [ $COMPARISON_EXIT_CODE -eq 0 ]; then
    echo "🎉 DETERMINISM PASSED: Outputs are identical"
else
    echo "❌ DETERMINISM FAILED: Outputs differ (exit code: $COMPARISON_EXIT_CODE)"
    echo "Check proof/PHASE0_DETERMINISM_REPORT.md for details"
fi

echo ""
echo "Report: proof/PHASE0_DETERMINISM_REPORT.md"
```

## 📋 What These Commands Do

1. **Run A**: Executes extraction with 1 worker (sequential)
2. **Run B**: Executes extraction with 4 workers (concurrent)  
3. **Compare**: Uses SHA256 hashing to verify outputs are identical

## 🎯 Expected Outcomes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | ✅ **DETERMINISM PASSED** | Proceed to next phase |
| 2 | ❌ **DETERMINISM FAILED** | Analyze report, fix non-deterministic sources |
| 1 | ⚠️ **SCRIPT ERROR** | Check error output |

## 🔍 What to Look For

- **Timestamps**: If outputs include timestamps, they'll cause mismatches
- **Randomness**: Any random IDs or nonces will break determinism
- **File Ordering**: JSON key ordering is already normalized by the script
- **Worker-Specific Artifacts**: Ensure no worker-specific data is written to outputs

## 📁 Files Created

- `proof/PHASE0_DETERMINISM_REPORT.md` - Detailed comparison report
- Extraction outputs in `extraction/repo-truth-extractor/v3/runs/{RUN_ID}/`

## 🚀 Next Steps After Running

1. **If PASS (exit 0)**: Commit the report and proceed to next phase
2. **If FAIL (exit 2)**: 
   - Analyze `proof/PHASE0_DETERMINISM_REPORT.md`
   - Identify sources of non-determinism
   - Fix issues (remove timestamps, randomness, etc.)
   - Re-run the test

**You're now ready to execute Gate 0C!** 🎉