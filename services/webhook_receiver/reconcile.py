from __future__ import annotations

from typing import Any, Dict, Optional


def extract_run_mapping(payload: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract run metadata (run_id, phase, step_id, partition_id, attempt, provider_ref) from OpenAI webhook payload structure."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    return {
        "run_id": _as_text(metadata.get("run_id")),
        "phase": _as_text(metadata.get("phase")),
        "step_id": _as_text(metadata.get("step_id")),
        "partition_id": _as_text(metadata.get("partition_id")),
        "attempt": _as_text(metadata.get("attempt")),
        "provider_ref": _as_text(data.get("id")),
    }


def _as_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    token = str(value).strip()
    return token if token else None
