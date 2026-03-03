import asyncio
import sys
from pathlib import Path

# Add the service directory to path to allow direct imports
service_dir = Path(__file__).resolve().parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

try:
    from main import mcp
except ImportError:
    from services.adhd_engine.main import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
