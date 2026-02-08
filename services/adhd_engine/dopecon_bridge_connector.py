"""Optional Dopecon bridge connector shim for ADHD engine."""

from typing import Any, Dict


async def emit_state_update(event_type: str, payload: Dict[str, Any]) -> bool:
    """
    Emit ADHD state updates to bridge integrations.

    This shim is intentionally no-op safe to avoid hard runtime dependency.
    """
    return True
