from __future__ import annotations

from typing import Dict


def poll_status(job: Dict[str, object]) -> str:
    # Placeholder poll adapter: in production this calls Gemini/Vertex job APIs.
    status = str(job.get("status") or "").lower()
    if status in {"submitted", "running"}:
        return "completed"
    return status or "unknown"
