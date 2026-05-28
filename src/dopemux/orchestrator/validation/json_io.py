"""Read-only JSON loading for validators."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .report import ValidationIssue, issue


def load_json_object(
    path: str | Path,
) -> Tuple[Dict[str, Any] | None, List[ValidationIssue]]:
    resolved = Path(path)
    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [
            issue(
                "INPUT_READ_ERROR",
                f"Unable to read JSON file: {exc}",
            )
        ]

    try:
        payload = json.loads(text)
    except JSONDecodeError as exc:
        return None, [
            issue(
                "JSON_PARSE_ERROR",
                f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
        ]

    if not isinstance(payload, dict):
        return None, [
            issue(
                "JSON_OBJECT_REQUIRED",
                "Validation input must be a JSON object.",
            )
        ]
    return payload, []
