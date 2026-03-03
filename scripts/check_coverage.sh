#!/bin/bash
# Scoped coverage check for Dopemux
# Enforces >= 80% coverage only on active/new modules

# Modules to check
MODULES="dopemux.mcp.provision,dopemux.mcp.instance_overlay"

echo "Running scoped coverage for: $MODULES"

export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest tests/mcp -q \
    --cov=dopemux.mcp.provision \
    --cov=dopemux.mcp.instance_overlay \
    --cov-report=term-missing \
    --cov-fail-under=80

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ Scoped coverage PASS"
else
    echo "❌ Scoped coverage FAIL"
    exit $RESULT
fi
