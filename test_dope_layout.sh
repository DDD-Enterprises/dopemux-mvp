#!/bin/bash
# Quick test of the DOPE layout implementation

set -e

echo "🚀 Testing DOPE Layout Implementation"
echo "======================================"
echo

# Run tests
echo "1️⃣  Running test suite..."
python3 -m pytest scripts/neon_dashboard/tests/ -v --tb=short || {
    echo "❌ Tests failed"
    exit 1
}

echo
echo "2️⃣  Checking CLI integration..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from dopemux.tmux.cli import _setup_dope_layout
print('✅ Dope layout function found in CLI')
"

echo
echo "3️⃣  Validating imports..."
python3 -c "
from scripts.neon_dashboard.core.app import NeonDashboardApp
from scripts.neon_dashboard.components.metrics_bar import main as metrics_main
from scripts.neon_dashboard.collectors.pm_collector import PMCollector
from scripts.neon_dashboard.collectors.impl_collector import ImplementationCollector
print('✅ All imports successful')
"

echo
echo "4️⃣  Checking dependencies..."
python3 -c "
import textual
import rich
import aiohttp
print(f'✅ textual {textual.__version__}')
print(f'✅ rich installed')
print(f'✅ aiohttp {aiohttp.__version__}')
"

echo
echo "✅ All checks passed!"
echo
echo "To launch the DOPE layout:"
echo "  dopemux tmux start --layout dope"
echo
echo "Keyboard shortcuts:"
echo "  M - Toggle between PM and Implementation modes"
echo "  ? - Show help"
echo "  Q - Quit"
