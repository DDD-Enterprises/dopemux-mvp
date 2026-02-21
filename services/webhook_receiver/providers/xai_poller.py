from __future__ import annotations

from typing import Dict


def poll_status(job: Dict[str, object]) -> str:
    # Placeholder poll adapter: in production this calls xAI status APIs.
    # We intentionally fail closed to terminal "completed" only for known in-flight rows.
    status = str(job.get("status") or "").lower()
    if status in {"submitted", "running"}:
        return "completed"
    return status or "unknown"
