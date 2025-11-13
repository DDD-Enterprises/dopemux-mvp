#!/bin/bash
# Run all multi-workspace tests

echo "=================================="
echo "Multi-Workspace Test Suite"
echo "=================================="
echo ""

# Shared utilities
echo "1. Testing shared utilities..."
python3 -m pytest services/shared/test_workspace_utils.py -v --tb=short 2>&1 | tail -5

# dope-context
echo ""
echo "2. Testing dope-context..."
PYTHONPATH="$(pwd)/services/dope-context" python3 -m pytest \
  services/dope-context/tests/test_mcp_server.py -k multi -v --tb=short 2>&1 | tail -5

# serena
echo ""
echo "3. Testing serena..."
python3 -m pytest services/serena/tests/test_multi_workspace.py -v --tb=short 2>&1 | tail -5

# orchestrator
echo ""
echo "4. Testing orchestrator..."
python3 -m pytest services/orchestrator/tests/test_workspace_support.py -v --tb=short --override-ini="addopts=" 2>&1 | tail -5

echo ""
echo "=================================="
echo "Test Summary"
echo "=================================="
echo "All multi-workspace tests complete"
