#!/bin/bash
#
# Basic installer tests (platform detection, Python checks, dependencies)
# Does NOT require Docker - tests core functionality only
#

set -e

echo "🧪 Running basic installer tests..."
echo ""

# Test 1: Script Syntax Check
echo "Test 1: Script Syntax Check"
echo "==========================="
if bash -n install.sh; then
    echo "✅ install.sh syntax valid"
else
    echo "❌ install.sh has syntax errors"
    exit 1
fi
echo ""

# Test 2: Help Output
echo "Test 2: Help Output"
echo "==================="
if ./install.sh --help >/dev/null 2>&1; then
    echo "✅ Help flag works"
else
    echo "❌ Help flag failed"
fi
echo ""

# Test 3: Python Check
echo "Test 3: Python Version"
echo "======================"
if python3 --version; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✅ Python found: $PY_VERSION"
    
    MIN_VERSION="3.10"
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        echo "✅ Python version >= $MIN_VERSION"
    else
        echo "⚠️  Python < $MIN_VERSION (installer requires 3.10+)"
    fi
else
    echo "❌ Python not found"
fi
echo ""

# Test 4: Git Check
echo "Test 4: Git Check"
echo "================="
if command -v git >/dev/null 2>&1; then
    GIT_VERSION=$(git --version)
    echo "✅ Git found: $GIT_VERSION"
else
    echo "❌ Git not found"
fi
echo ""

# Test 5: Docker Check (optional)
echo "Test 5: Docker Check"
echo "===================="
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version 2>/dev/null || echo "found but not running")
    echo "✅ Docker found: $DOCKER_VERSION"
else
    echo "⚠️  Docker not found (optional for testing)"
fi
echo ""

echo "📊 Test Summary"
echo "==============="
echo "Basic tests complete! ✅"
echo ""
echo "Note: Full installation tests require:"
echo "  - Docker (for service deployment)"
echo "  - Platform-specific package managers"
echo "  - Root/sudo access (for system packages)"

