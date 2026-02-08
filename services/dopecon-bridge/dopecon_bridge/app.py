"""DopeconBridge unified application entrypoint.

This module intentionally delegates to the legacy `main.py` FastAPI app so all
execution paths (`python main.py` and `python -m dopecon_bridge.app`) run the
same runtime implementation.
"""

from __future__ import annotations

import uvicorn

from main import app as _legacy_app
from main import HOST, MCP_INTEGRATION_PORT, LOG_LEVEL


# Public ASGI app object for uvicorn imports.
app = _legacy_app


def run() -> None:
    """Run the unified DopeconBridge ASGI app."""
    uvicorn.run(
        "main:app",
        host=HOST,
        port=MCP_INTEGRATION_PORT,
        reload=False,
        log_level=LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run()
