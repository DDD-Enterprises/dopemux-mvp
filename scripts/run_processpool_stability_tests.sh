#!/bin/bash
# ProcessPool Stability Regression Tests
# Run this in CI on every push/PR to prevent regression of TP-EXTR-001C-PROCESSPOOL-STABILIZE-0002

echo "Running ProcessPool stability regression tests..."
cd /Users/hue/code/dopemux-mvp

# Run the regression test suite
python -m pytest tests/unit/test_run_extraction_v3_processpool_stability.py --no-cov -q

if [ $? -eq 0 ]; then
    echo "✅ All ProcessPool stability tests passed"
    exit 0
else
    echo "❌ ProcessPool stability tests failed"
    exit 1
fi