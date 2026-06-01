from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import CONTRACT_VERSION


CONFIG_RELATIVE_PATH = Path("config/pr_steward/policy.json")
SCHEMA_RELATIVE_PATH = Path("schemas/pr_steward/config.schema.json")
SCAFFOLD_RELATIVE_PATH = Path(
    "src/dopemux/templates/init/config/pr_steward/policy.json"
)

SUPPORTED_SCHEMA_KEYS = {
    "$id",
    "$schema",
    "additionalProperties",
    "description",
    "enum",
    "items",
    "minItems",
    "properties",
    "required",
    "title",
    "type",
}


@dataclass(frozen=True)
class DoctorResult:
    status: str
    reason_code: str
    workspace: str
    contract_version: str
    checks: dict[str, dict[str, str]]

    @property
    def ok(self) -> bool:
        return self.status == "PASS"

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason_code": self.reason_code,
            "workspace": self.workspace,
            "contract_version": self.contract_version,
            "checks": self.checks,
        }


def run_doctor(
    *,
    workspace: Path,
    schema_path: Path | None = None,
    scaffold_path: Path | None = None,
) -> DoctorResult:
    """Validate PR Steward config and scaffold skew without mutating files."""
    workspace = workspace.expanduser().resolve()
    config_path = workspace / CONFIG_RELATIVE_PATH
    schema_path = schema_path or _find_repo_file(SCHEMA_RELATIVE_PATH)
    scaffold_path = scaffold_path or _find_repo_file(SCAFFOLD_RELATIVE_PATH)

    checks: dict[str, dict[str, str]] = {}

    schema = _load_schema(schema_path)
    if isinstance(schema, str):
        checks["config_schema"] = {"status": "FAIL", "message": schema}
        return _blocked("UNKNOWN_SCHEMA", workspace, checks)

    unsupported = _find_unsupported_schema_keys(schema)
    if unsupported:
        checks["config_schema"] = {
            "status": "FAIL",
            "message": (
                "Unsupported schema keyword(s): "
                + ", ".join(sorted(unsupported))
                + ". Refusing to guess validation semantics."
            ),
        }
        return _blocked("UNKNOWN_SCHEMA", workspace, checks)

    config = _load_json_object(config_path)
    if isinstance(config, str):
        checks["config_schema"] = {"status": "FAIL", "message": config}
        return _blocked("CONFIG_INVALID", workspace, checks)

    errors = _validate_subset(config, schema)
    if errors:
        checks["config_schema"] = {
            "status": "FAIL",
            "message": "; ".join(errors),
        }
        return _blocked("CONFIG_INVALID", workspace, checks)

    checks["config_schema"] = {
        "status": "PASS",
        "message": f"{CONFIG_RELATIVE_PATH} validates against {SCHEMA_RELATIVE_PATH}.",
    }

    scaffold = _load_json_object(scaffold_path)
    if isinstance(scaffold, str):
        checks["scaffold_skew"] = {"status": "FAIL", "message": scaffold}
        return _blocked("SCAFFOLD_UNKNOWN", workspace, checks)

    if _canonical_json(config) != _canonical_json(scaffold):
        checks["scaffold_skew"] = {
            "status": "FAIL",
            "message": (
                f"{CONFIG_RELATIVE_PATH} differs from packaged scaffold policy; "
                "review local drift or rerun dopemux init in a controlled branch."
            ),
        }
        return _blocked("SCAFFOLD_SKEW", workspace, checks)

    checks["scaffold_skew"] = {
        "status": "PASS",
        "message": f"{CONFIG_RELATIVE_PATH} matches packaged scaffold policy.",
    }
    return DoctorResult(
        status="PASS",
        reason_code="PASS",
        workspace=str(workspace),
        contract_version=CONTRACT_VERSION,
        checks=checks,
    )


def format_result(result: DoctorResult, *, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result.to_payload(), indent=2, sort_keys=True)

    lines = [
        f"status={result.status}",
        f"reason_code={result.reason_code}",
        f"workspace={result.workspace}",
        f"contract_version={result.contract_version}",
    ]
    for name, check in result.checks.items():
        lines.append(f"{name}: {check['status']} - {check['message']}")
    if not result.ok:
        lines.append("TP-DMX-STEWARD-DOCTOR-303 is report-only; no files were changed.")
    return "\n".join(lines)


def _blocked(
    reason_code: str, workspace: Path, checks: dict[str, dict[str, str]]
) -> DoctorResult:
    return DoctorResult(
        status="BLOCKED",
        reason_code=reason_code,
        workspace=str(workspace),
        contract_version=CONTRACT_VERSION,
        checks=checks,
    )


def _find_repo_file(relative_path: Path) -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        path = candidate / relative_path
        if path.exists():
            return path
    return Path.cwd() / relative_path


def _load_schema(path: Path) -> dict[str, Any] | str:
    payload = _load_json_object(path)
    if isinstance(payload, str):
        return f"Unknown schema at {path}: {payload}"
    return payload


def _load_json_object(path: Path) -> dict[str, Any] | str:
    if not path.exists():
        return f"Missing JSON object file: {path}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in {path}: {exc.msg}"
    if not isinstance(payload, dict):
        return f"{path} must contain a JSON object"
    return payload


def _find_unsupported_schema_keys(schema: Any, *, in_properties: bool = False) -> set[str]:
    unsupported: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if not in_properties and key not in SUPPORTED_SCHEMA_KEYS:
                unsupported.add(key)
            unsupported.update(
                _find_unsupported_schema_keys(value, in_properties=(key == "properties"))
            )
    elif isinstance(schema, list):
        for item in schema:
            unsupported.update(_find_unsupported_schema_keys(item))
    return unsupported


def _validate_subset(payload: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type and not _matches_type(payload, expected_type):
        return [f"{path} must be {expected_type}"]

    enum = schema.get("enum")
    if enum is not None and payload not in enum:
        errors.append(f"{path} must be one of {enum}")

    if isinstance(payload, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in payload:
                errors.append(f"{path}.{key} is required")

        properties = schema.get("properties") or {}
        if schema.get("additionalProperties") is False:
            for key in payload:
                if key not in properties:
                    errors.append(f"{path}.{key} is not allowed")

        for key, subschema in properties.items():
            if key in payload and isinstance(subschema, dict):
                errors.extend(_validate_subset(payload[key], subschema, f"{path}.{key}"))

    if isinstance(payload, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(payload) < min_items:
            errors.append(f"{path} must contain at least {min_items} item(s)")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(payload):
                errors.extend(_validate_subset(item, item_schema, f"{path}[{index}]"))

    return errors


def _matches_type(payload: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(payload, dict)
    if expected_type == "array":
        return isinstance(payload, list)
    if expected_type == "string":
        return isinstance(payload, str)
    if expected_type == "boolean":
        return isinstance(payload, bool)
    if expected_type == "integer":
        return isinstance(payload, int) and not isinstance(payload, bool)
    return False


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
