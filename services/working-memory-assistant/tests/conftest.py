"""
Pytest configuration for working-memory-assistant tests.

Ensures service directory is in sys.path for proper imports.
"""

import sys
from pathlib import Path

# Add service directory to sys.path
service_dir = Path(__file__).parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))
