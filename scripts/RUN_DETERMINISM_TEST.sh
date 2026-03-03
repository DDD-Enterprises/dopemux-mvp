#!/bin/bash
# Phase 0C Determinism Test: Compare workers=1 vs workers=4
# This script runs the extraction twice with identical inputs but different worker counts
# and then compares the outputs to verify determinism.

set -e
set -u
set -o pipefail

echo "=== Phase 0C Determinism Test ==="
echo "Testing extraction determinism between workers=1 and workers=4"
echo ""

# Generate unique run IDs
RUN_ID_A="determinism_a_$(date +%Y%m%d_%H%M%S)"
RUN_ID_B="determinism_b_$(date +%Y%m%d_%H%M%S)"

echo "Run ID A (workers=1): $RUN_ID_A"
echo "Run ID B (workers=4): $RUN_ID_B"
echo ""

# Phase to test (start with A for repo control plane)
PHASE="A"

echo "Testing phase: $PHASE"
echo ""

# Run A: Single worker
echo "=== Running extraction with workers=1 ==="
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_A" \
  --phase "$PHASE" \
  --partition-workers 1 \
  --dry-run  # Add --dry-run for testing, remove for actual run

echo ""
echo "✅ Run A completed"
echo ""

# Run B: Multiple workers
echo "=== Running extraction with workers=4 ==="
python services/repo-truth-extractor/run_extraction_v3.py \
  --run-id "$RUN_ID_B" \
  --phase "$PHASE" \
  --partition-workers 4 \
  --dry-run  # Add --dry-run for testing, remove for actual run

echo ""
echo "✅ Run B completed"
echo ""

# Compare outputs
echo "=== Comparing outputs for determinism ==="
python services/repo-truth-extractor/tools/phase0_determinism_check.py \
  --out-a "extraction/repo-truth-extractor/v3/runs/${RUN_ID_A}/${PHASE}_repo_control_plane/raw" \
  --out-b "extraction/repo-truth-extractor/v3/runs/${RUN_ID_B}/${PHASE}_repo_control_plane/raw" \
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
echo "=== Test Summary ==="
echo "Run A (workers=1): $RUN_ID_A"
echo "Run B (workers=4): $RUN_ID_B"
echo "Phase: $PHASE"
echo "Comparison exit code: $COMPARISON_EXIT_CODE"
echo "Report: proof/PHASE0_DETERMINISM_REPORT.md"
