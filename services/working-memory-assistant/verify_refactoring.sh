#!/bin/bash
# Verify Phase 2 refactoring is complete

echo "🔍 Dope-Memory Phase 2 Refactoring Verification"
echo "================================================"
echo ""

# Check imports
echo "✓ Checking imports..."
python3 -c "from dope_memory_main import DopeMemoryMCPServer; from reflection.reflection import ReflectionGenerator; from trajectory.manager import TrajectoryManager" && echo "  ✅ All modules import successfully" || exit 1

# Check no duplicate SQL
echo ""
echo "✓ Checking for duplicate reflection SQL..."
if grep -q "INSERT INTO reflection_cards" dope_memory_main.py; then
    echo "  ❌ Found duplicate reflection SQL in dope_memory_main.py"
    exit 1
else
    echo "  ✅ No duplicate reflection SQL found"
fi

# Check no _update_trajectory_state
echo ""
echo "✓ Checking for removed _update_trajectory_state..."
if grep -q "def _update_trajectory_state" dope_memory_main.py; then
    echo "  ❌ Found _update_trajectory_state method that should be removed"
    exit 1
else
    echo "  ✅ _update_trajectory_state method removed"
fi

# Run tests
echo ""
echo "✓ Running Phase 2 tests..."
python3 -m pytest tests/test_phase2_reflection_trajectory.py -q --no-cov
if [ $? -eq 0 ]; then
    echo "  ✅ All Phase 2 tests pass"
else
    echo "  ❌ Phase 2 tests failed"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Phase 2 refactoring verification PASSED"
echo "================================================"
