"""Task Packet validation against the canonical repo schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .json_io import load_json_object
from .report import ValidationIssue, ValidationReport, issue, path_text, sort_issues


DEFAULT_PACKET_SCHEMA_PATH = Path(
    "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
)


def default_packet_schema_path() -> Path:
    cwd_candidate = Path.cwd() / DEFAULT_PACKET_SCHEMA_PATH
    if cwd_candidate.exists():
        return DEFAULT_PACKET_SCHEMA_PATH

    repo_candidate = Path(__file__).resolve().parents[4] / DEFAULT_PACKET_SCHEMA_PATH
    if repo_candidate.exists():
        return repo_candidate
    return DEFAULT_PACKET_SCHEMA_PATH


def _json_pointer(parts: Any) -> str:
    values = [str(part) for part in parts]
    return "/" + "/".join(values) if values else ""


def _schema_issues(
    packet: Dict[str, Any],
    schema: Dict[str, Any],
) -> List[ValidationIssue]:
    try:
        from jsonschema import Draft7Validator
        from jsonschema.exceptions import SchemaError
    except ModuleNotFoundError:
        return [
            issue(
                "JSONSCHEMA_UNAVAILABLE",
                "jsonschema is not importable; packet validation cannot run.",
            )
        ]

    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:
        return [
            issue(
                "PACKET_SCHEMA_INVALID",
                f"Packet schema is invalid: {exc.message}",
                path=_json_pointer(exc.absolute_schema_path),
            )
        ]

    validator = Draft7Validator(schema)
    return [
        issue(
            "PACKET_SCHEMA_VIOLATION",
            error.message,
            path=_json_pointer(error.absolute_path),
        )
        for error in validator.iter_errors(packet)
    ]


def validate_packet_file(
    packet_path: str | Path,
    *,
    schema_path: str | Path | None = None,
) -> ValidationReport:
    packet = Path(packet_path)
    schema = Path(schema_path) if schema_path is not None else default_packet_schema_path()
    schema_path_text = path_text(schema)

    if not schema.exists():
        errors = [
            issue(
                "REQUIRES_REPO_INSPECTION",
                f"Packet schema path is missing: {schema_path_text}",
            )
        ]
        return ValidationReport(
            kind="task_packet",
            path=path_text(packet),
            authority="dopetask-canonical-spec",
            status="UNKNOWN",
            valid=False,
            errors=errors,
            details={
                "schema_path": schema_path_text,
                "authority_boundary": "read_only_schema_validation_only",
            },
            exit_code=2,
        )

    packet_payload, packet_errors = load_json_object(packet)
    schema_payload, schema_errors = load_json_object(schema)
    errors: List[ValidationIssue] = [*packet_errors, *schema_errors]
    if packet_payload is not None and schema_payload is not None:
        errors.extend(_schema_issues(packet_payload, schema_payload))

    sorted_errors = sort_issues(errors)
    status = "PASS" if not sorted_errors else "FAIL"
    return ValidationReport(
        kind="task_packet",
        path=path_text(packet),
        authority="dopetask-canonical-spec",
        status=status,
        valid=status == "PASS",
        errors=sorted_errors,
        details={
            "schema_path": schema_path_text,
            "authority_boundary": "read_only_schema_validation_only",
        },
        exit_code=0 if status == "PASS" else 2,
    )
