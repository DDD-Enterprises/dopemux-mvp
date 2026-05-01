#!/usr/bin/env python3
"""Static verifier for Dopemux runtime authority manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


ALLOWED_AUTHORITY_STATUSES = {
    "OBSERVED",
    "CONFLICTING",
    "UNKNOWN",
    "DERIVED",
    "TRANSPORT_ONLY",
    "SHIM_ONLY",
}

CANONICAL_ROLES = {
    "canonical_runtime",
    "canonical_store",
    "canonical_extraction_runner",
    "domain_authority",
    "runtime_entrypoint",
}

REQUIRED_ENTRY_FIELDS = {
    "system",
    "domain",
    "authority_status",
    "expected_paths",
    "expected_ports",
    "forbidden_authority_paths",
    "known_conflicts",
    "validation_mode",
    "notes",
}


def _dict_sort_value(item: Any, key: str) -> str:
    if isinstance(item, dict):
        return str(item.get(key, ""))
    return str(item)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _normalize_system(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object.")
    systems = payload.get("systems")
    if not isinstance(systems, list) or not systems:
        raise ValueError("Manifest must contain a non-empty systems list.")
    return payload


def _iter_selected_systems(
    manifest: dict[str, Any],
    requested_system: str | None,
) -> list[dict[str, Any]]:
    systems = list(manifest["systems"])
    systems.sort(key=lambda entry: str(entry.get("system", "")).casefold())
    if requested_system is None:
        return systems

    requested = _normalize_system(requested_system)
    selected = [
        entry
        for entry in systems
        if _normalize_system(str(entry.get("system", ""))) == requested
    ]
    if not selected:
        known = ", ".join(str(entry.get("system", "")) for entry in systems)
        raise KeyError(f"Unknown system {requested_system!r}. Known systems: {known}")
    return selected


def _as_list(value: Any, field_name: str, system: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{system}: {field_name} must be a list.")
    return value


def _validate_entry_shape(entry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    system = str(entry.get("system", "<unknown>"))
    missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
    if missing:
        failures.append(f"{system}: missing required fields {missing}")

    status = entry.get("authority_status")
    if status not in ALLOWED_AUTHORITY_STATUSES:
        failures.append(f"{system}: invalid authority_status {status!r}")

    for list_field in (
        "expected_paths",
        "expected_ports",
        "forbidden_authority_paths",
        "known_conflicts",
        "notes",
    ):
        try:
            _as_list(entry.get(list_field), list_field, system)
        except ValueError as exc:
            failures.append(str(exc))

    return failures


def _path_exists(repo_root: Path, raw_path: str) -> bool:
    return (repo_root / raw_path).exists()


def _read_text(repo_root: Path, raw_path: str) -> str:
    return (repo_root / raw_path).read_text(encoding="utf-8", errors="replace")


def _validate_expected_paths(
    repo_root: Path,
    entry: dict[str, Any],
    lines: list[str],
) -> list[str]:
    failures: list[str] = []
    system = entry["system"]
    expected_paths = _as_list(entry.get("expected_paths"), "expected_paths", system)
    for item in sorted(expected_paths, key=lambda path_item: _dict_sort_value(path_item, "path")):
        if not isinstance(item, dict):
            failures.append(f"{system}: expected_paths entries must be objects.")
            continue
        raw_path = str(item.get("path", ""))
        role = str(item.get("role", "unspecified"))
        required = bool(item.get("required", True))
        exists = bool(raw_path) and _path_exists(repo_root, raw_path)
        state = "OK" if exists else "MISSING"
        requirement = "required" if required else "optional"
        lines.append(f"PATH {state} {system} {requirement} {role} {raw_path}")
        if required and not exists:
            failures.append(f"{system}: missing required expected path {raw_path}")
    return failures


def _validate_forbidden_paths(
    repo_root: Path,
    entry: dict[str, Any],
    lines: list[str],
) -> list[str]:
    failures: list[str] = []
    system = entry["system"]
    forbidden_paths = _as_list(
        entry.get("forbidden_authority_paths"),
        "forbidden_authority_paths",
        system,
    )
    expected_paths = _as_list(entry.get("expected_paths"), "expected_paths", system)
    canonical_expected_paths = {
        str(item.get("path", ""))
        for item in expected_paths
        if isinstance(item, dict) and str(item.get("role", "")) in CANONICAL_ROLES
    }

    for item in sorted(forbidden_paths, key=lambda path_item: _dict_sort_value(path_item, "path")):
        if not isinstance(item, dict):
            failures.append(f"{system}: forbidden_authority_paths entries must be objects.")
            continue
        raw_path = str(item.get("path", ""))
        forbidden_domain = str(item.get("forbidden_domain", "unspecified"))
        exists = bool(raw_path) and _path_exists(repo_root, raw_path)
        state = "PRESENT" if exists else "ABSENT"
        lines.append(f"FORBIDDEN {state} {system} {forbidden_domain} {raw_path}")
        if raw_path in canonical_expected_paths:
            failures.append(
                f"{system}: forbidden authority path is also listed with canonical role: {raw_path}"
            )
    return failures


def _validate_conflict_markers(
    repo_root: Path,
    entry: dict[str, Any],
    lines: list[str],
) -> list[str]:
    failures: list[str] = []
    system = entry["system"]
    conflicts = _as_list(entry.get("known_conflicts"), "known_conflicts", system)
    for conflict in sorted(conflicts, key=lambda item: _dict_sort_value(item, "id")):
        if not isinstance(conflict, dict):
            failures.append(f"{system}: known_conflicts entries must be objects.")
            continue
        conflict_id = str(conflict.get("id", "unnamed_conflict"))
        markers = conflict.get("markers", [])
        if not isinstance(markers, list):
            failures.append(f"{system}: conflict {conflict_id} markers must be a list.")
            continue
        marker_failures = 0
        for marker in sorted(markers, key=lambda item: _dict_sort_value(item, "path")):
            if not isinstance(marker, dict):
                failures.append(
                    f"{system}: conflict {conflict_id} marker entries must be objects."
                )
                marker_failures += 1
                continue
            raw_path = str(marker.get("path", ""))
            expected_text = str(marker.get("contains", ""))
            if not raw_path or not _path_exists(repo_root, raw_path):
                marker_failures += 1
                failures.append(
                    f"{system}: conflict {conflict_id} marker path missing: {raw_path}"
                )
                continue
            content = _read_text(repo_root, raw_path)
            if expected_text not in content:
                marker_failures += 1
                failures.append(
                    f"{system}: conflict {conflict_id} marker not found in {raw_path}"
                )
        state = "OBSERVED" if marker_failures == 0 else "MISSING_MARKER"
        lines.append(f"CONFLICT {state} {system} {conflict_id}")
    return failures


def _report_ports(entry: dict[str, Any], lines: list[str]) -> None:
    system = entry["system"]
    expected_ports = _as_list(entry.get("expected_ports"), "expected_ports", system)
    for port_info in sorted(
        expected_ports,
        key=lambda item: (
            int(item.get("port", -1)) if isinstance(item, dict) else -1,
            str(item.get("role", "")) if isinstance(item, dict) else str(item),
        ),
    ):
        if not isinstance(port_info, dict):
            lines.append(f"PORT INVALID {system}")
            continue
        port = port_info.get("port")
        status = str(port_info.get("status", "unspecified"))
        role = str(port_info.get("role", "unspecified"))
        lines.append(f"PORT {status.upper()} {system} {port} {role}")


def run_static_check(
    manifest: dict[str, Any],
    *,
    requested_system: str | None,
    repo_root: Path,
) -> tuple[int, list[str]]:
    lines: list[str] = []
    failures: list[str] = []

    selected = _iter_selected_systems(manifest, requested_system)
    lines.append(
        f"RUNTIME_AUTHORITY_STATIC_CHECK schema={manifest.get('schema_version')} systems={len(selected)}"
    )

    for entry in selected:
        shape_failures = _validate_entry_shape(entry)
        failures.extend(shape_failures)
        if shape_failures:
            continue

        system = str(entry["system"])
        lines.append(
            "SYSTEM "
            f"{system} status={entry['authority_status']} "
            f"domain={entry['domain']} validation={entry['validation_mode']}"
        )
        failures.extend(_validate_expected_paths(repo_root, entry, lines))
        failures.extend(_validate_forbidden_paths(repo_root, entry, lines))
        _report_ports(entry, lines)
        failures.extend(_validate_conflict_markers(repo_root, entry, lines))

    if failures:
        for failure in sorted(failures):
            lines.append(f"FAIL {failure}")
        lines.append(f"SUMMARY status=failed failures={len(failures)}")
        return 1, lines

    lines.append("SUMMARY status=passed failures=0")
    return 0, lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Dopemux runtime authority manifest without network or Docker."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to config/runtime_authority_manifest.json.",
    )
    parser.add_argument(
        "--system",
        help="Optional system filter. Matching is case-insensitive and ignores punctuation.",
    )
    parser.add_argument(
        "--check",
        choices=["static"],
        default="static",
        help="Check mode. Only static mode is supported.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        manifest_path = args.manifest
        if not manifest_path.is_absolute():
            manifest_path = _repo_root() / manifest_path
        manifest = _load_manifest(manifest_path)
        exit_code, lines = run_static_check(
            manifest,
            requested_system=args.system,
            repo_root=_repo_root(),
        )
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    for line in lines:
        print(line)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
