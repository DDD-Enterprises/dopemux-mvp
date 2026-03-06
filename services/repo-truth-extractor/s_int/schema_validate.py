from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_schema(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_type(value: Any, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return True


def _validate(payload: Any, schema: Dict[str, Any], path: str, errors: List[str]) -> None:
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _is_type(payload, expected_type):
        errors.append(f"{path}: expected {expected_type}, got {type(payload).__name__}")
        return

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and payload not in enum_values:
        errors.append(f"{path}: expected one of {enum_values}, got {payload!r}")

    if isinstance(payload, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in payload:
                    errors.append(f"{path}: missing required key {key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in payload and isinstance(child_schema, dict):
                    _validate(payload[key], child_schema, f"{path}.{key}", errors)
        if schema.get("additionalProperties") is False and isinstance(properties, dict):
            allowed = set(properties.keys())
            for key in payload.keys():
                if key not in allowed:
                    errors.append(f"{path}: additional property {key} is not allowed")
    elif isinstance(payload, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(payload):
                _validate(item, item_schema, f"{path}[{index}]", errors)


def validate_payload(payload: Any, schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    _validate(payload, schema, "$", errors)
    return errors


def validate_payload_or_raise(payload: Any, schema: Dict[str, Any], *, label: str) -> None:
    errors = validate_payload(payload, schema)
    if errors:
        joined = "; ".join(errors[:10])
        raise ValueError(f"{label} failed schema validation: {joined}")
