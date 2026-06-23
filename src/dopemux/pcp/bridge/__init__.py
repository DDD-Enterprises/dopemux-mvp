"""dopemux.pcp.bridge — fail-closed live-write adapter.

Routes mutations through a registered canonical writer ONLY behind a satisfied,
unexpired, payload-bound LIVE_WRITE_READY gate. It is an ADAPTER, never a
canonical authority. No default production writer exists: a live write requires
an explicitly registered canonical_writer (resolved by the gate's
``canonical_writer`` name) AND a READY gate bound to the exact operation AND
``execute is True`` AND a first-time idempotency key.
"""

from dopemux.pcp.bridge.fastapi_bridge import (
    check_live_write_gate,
    create_bridge_app,
    create_bridge_router,
    route_mutation,
)

__all__ = [
    "check_live_write_gate",
    "route_mutation",
    "create_bridge_router",
    "create_bridge_app",
]
