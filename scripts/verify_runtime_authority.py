#!/usr/bin/env python3
"""Deterministic static verifier for Dopemux runtime authority pointers."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SYSTEM_KEYS = {"system", "expected_paths", "authority_status", "validation_mode"}
ERROR = "error"
WARNING = "warning"
INFO = "info"


def _finding(
    *,
    severity: str,
    code: str,
    system: str,
    message: str,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "code": code,
        "message": message,
        "severity": severity,
        "system": system,
    }
    if path is not None:
        finding["path"] = path
    if details:
        finding["details"] = details
    return finding


def _sort_findings(findings: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_order = {ERROR: 0, WARNING: 1, INFO: 2}
    return sorted(
        findings,
        key=lambda item: (
            severity_order.get(str(item.get("severity")), 99),
            str(item.get("system", "")),
            str(item.get("code", "")),
            str(item.get("path", "")),
            str(item.get("message", "")),
        ),
    )


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a JSON object")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML is present in repo test envs
        raise RuntimeError("PyYAML is required for static registry and compose checks") from exc

    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _path_text(repo_root: Path, rel_path: str) -> str:
    return (repo_root / rel_path).read_text(encoding="utf-8", errors="replace")


def _path_exists(repo_root: Path, rel_path: str) -> bool:
    return (repo_root / rel_path).exists()


def _entry_path(entry: str | dict[str, Any]) -> str:
    if isinstance(entry, str):
        return entry
    return str(entry.get("path", ""))


def _entry_required(entry: str | dict[str, Any], *, system_status: str, validation_mode: str) -> bool:
    if system_status == "unknown" or validation_mode == "advisory":
        return False
    if isinstance(entry, str):
        return True
    return bool(entry.get("required", True))


def _registry_services(repo_root: Path) -> dict[str, dict[str, Any]]:
    payload = _load_yaml(repo_root / "services" / "registry.yaml")
    services = payload.get("services", [])
    if not isinstance(services, list):
        return {}
    return {
        str(item.get("name")): item
        for item in services
        if isinstance(item, dict) and item.get("name")
    }


def _compose_services(repo_root: Path) -> dict[str, dict[str, Any]]:
    payload = _load_yaml(repo_root / "compose.yml")
    services = payload.get("services", {})
    if not isinstance(services, dict):
        return {}
    return {
        str(name): cfg
        for name, cfg in services.items()
        if isinstance(cfg, dict)
    }


def _defaulted_port(value: str) -> int | None:
    text = value.strip()
    match = re.fullmatch(r"\$\{[^:}]+:-(\d+)\}", text)
    if match:
        return int(match.group(1))
    if text.isdigit():
        return int(text)
    return None


def _compose_ports(compose_cfg: dict[str, Any]) -> set[tuple[int | None, int | None]]:
    ports = compose_cfg.get("ports", [])
    resolved: set[tuple[int | None, int | None]] = set()
    if not isinstance(ports, list):
        return resolved

    for item in ports:
        if isinstance(item, str):
            match = re.fullmatch(r"(?P<host>\$\{[^}]+\}|\d+):(?P<container>\d+)", item.strip())
            if match:
                resolved.add((_defaulted_port(match.group("host")), _defaulted_port(match.group("container"))))
        elif isinstance(item, dict):
            published = item.get("published")
            target = item.get("target")
            resolved.add(
                (
                    int(published) if isinstance(published, int) else _defaulted_port(str(published)),
                    int(target) if isinstance(target, int) else _defaulted_port(str(target)),
                )
            )
    return resolved


def _check_repo_identity(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    identity = manifest.get("repo_identity", {})
    if not isinstance(identity, dict):
        return []

    findings: list[dict[str, Any]] = []
    marker = str(identity.get("repo_marker") or "")
    if marker and not _path_exists(repo_root, marker):
        findings.append(
            _finding(
                severity=ERROR,
                code="repo_marker_missing",
                system="repo",
                path=marker,
                message=f"Required repo marker is missing: {marker}",
            )
        )

    if identity.get("require_identity_match"):
        hint = str(identity.get("origin_hint") or "").strip()
        if hint:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            origin = result.stdout.strip()
            if result.returncode != 0:
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="origin_unreadable",
                        system="repo",
                        message=(result.stderr or "Could not read origin remote").strip(),
                    )
                )
            elif hint not in origin:
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="origin_mismatch",
                        system="repo",
                        message=f"Origin remote does not contain required hint {hint!r}",
                        details={"origin": origin},
                    )
                )
    return findings


def _check_system_entries(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    systems = manifest.get("systems", [])
    if not isinstance(systems, list):
        return [
            _finding(
                severity=ERROR,
                code="manifest_systems_invalid",
                system="manifest",
                message="Manifest field 'systems' must be a list.",
            )
        ]

    for system_entry in sorted(systems, key=lambda item: str(item.get("system", "")) if isinstance(item, dict) else ""):
        if not isinstance(system_entry, dict):
            findings.append(
                _finding(
                    severity=ERROR,
                    code="manifest_system_invalid",
                    system="manifest",
                    message="Each system entry must be a JSON object.",
                )
            )
            continue

        system = str(system_entry.get("system") or "UNKNOWN")
        missing_keys = REQUIRED_SYSTEM_KEYS - set(system_entry)
        if missing_keys:
            findings.append(
                _finding(
                    severity=ERROR,
                    code="manifest_required_key_missing",
                    system=system,
                    message=f"System entry is missing required keys: {', '.join(sorted(missing_keys))}",
                )
            )

        status = str(system_entry.get("authority_status", "unknown"))
        validation_mode = str(system_entry.get("validation_mode", "advisory"))
        if status == "expected_conflict":
            findings.append(
                _finding(
                    severity=WARNING,
                    code="expected_authority_conflict",
                    system=system,
                    message="Manifest marks this runtime authority surface as an expected conflict.",
                )
            )
        if status == "unknown":
            findings.append(
                _finding(
                    severity=INFO,
                    code="unknown_authority_not_asserted",
                    system=system,
                    message="Manifest marks authority unknown; required-path assertions are advisory only.",
                )
            )

        expected_paths = system_entry.get("expected_paths", [])
        if not isinstance(expected_paths, list):
            findings.append(
                _finding(
                    severity=ERROR,
                    code="expected_paths_invalid",
                    system=system,
                    message="expected_paths must be a list.",
                )
            )
            continue

        for path_entry in sorted(expected_paths, key=_entry_path):
            rel_path = _entry_path(path_entry)
            if not rel_path:
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="expected_path_blank",
                        system=system,
                        message="Expected path entry is blank.",
                    )
                )
                continue
            if not _path_exists(repo_root, rel_path):
                required = _entry_required(path_entry, system_status=status, validation_mode=validation_mode)
                findings.append(
                    _finding(
                        severity=ERROR if required else WARNING,
                        code="expected_path_missing",
                        system=system,
                        path=rel_path,
                        message=f"Expected runtime authority path is missing: {rel_path}",
                    )
                )

        findings.extend(_check_wrapper_mappings(system_entry.get("wrapper_mappings", []), repo_root, default_system=system))

    return findings


def _check_ports(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    registry = _registry_services(repo_root)
    compose = _compose_services(repo_root)

    systems = manifest.get("systems", [])
    if not isinstance(systems, list):
        return findings

    for system_entry in sorted(systems, key=lambda item: str(item.get("system", "")) if isinstance(item, dict) else ""):
        if not isinstance(system_entry, dict):
            continue
        system = str(system_entry.get("system") or "UNKNOWN")
        expected_ports = system_entry.get("expected_ports", [])
        if not isinstance(expected_ports, list):
            findings.append(
                _finding(
                    severity=ERROR,
                    code="expected_ports_invalid",
                    system=system,
                    message="expected_ports must be a list.",
                )
            )
            continue

        for port_entry in sorted(expected_ports, key=lambda item: str(item.get("registry_service", "")) if isinstance(item, dict) else ""):
            if not isinstance(port_entry, dict):
                continue
            registry_name = str(port_entry.get("registry_service") or "")
            compose_name = str(port_entry.get("compose_service") or registry_name)
            expected_host = int(port_entry["host_port"])
            expected_container = int(port_entry["container_port"])

            registry_entry = registry.get(registry_name)
            if registry_entry is None:
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="registry_service_missing",
                        system=system,
                        message=f"Registry service is missing: {registry_name}",
                    )
                )
            else:
                actual_host = registry_entry.get("port")
                actual_container = registry_entry.get("container_port", actual_host)
                if actual_host != expected_host or actual_container != expected_container:
                    findings.append(
                        _finding(
                            severity=ERROR,
                            code="registry_port_mismatch",
                            system=system,
                            message=f"Registry port mismatch for {registry_name}",
                            details={
                                "actual_container_port": actual_container,
                                "actual_host_port": actual_host,
                                "expected_container_port": expected_container,
                                "expected_host_port": expected_host,
                            },
                        )
                    )

            compose_entry = compose.get(compose_name)
            if compose_entry is None:
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="compose_service_missing",
                        system=system,
                        message=f"Compose service is missing: {compose_name}",
                    )
                )
                continue
            compose_ports = _compose_ports(compose_entry)
            if (expected_host, expected_container) not in compose_ports:
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="compose_port_mismatch",
                        system=system,
                        message=f"Compose port mapping mismatch for {compose_name}",
                        details={
                            "actual_mappings": sorted([list(item) for item in compose_ports]),
                            "expected_mapping": [expected_host, expected_container],
                        },
                    )
                )

    return findings


def _check_wrapper_mappings(
    mappings: Any,
    repo_root: Path,
    *,
    default_system: str = "manifest",
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not mappings:
        return findings
    if not isinstance(mappings, list):
        return [
            _finding(
                severity=ERROR,
                code="wrapper_mappings_invalid",
                system=default_system,
                message="wrapper_mappings must be a list.",
            )
        ]

    for mapping in sorted(mappings, key=lambda item: str(item.get("path", "")) if isinstance(item, dict) else ""):
        if not isinstance(mapping, dict):
            continue
        system = str(mapping.get("system") or default_system)
        rel_path = str(mapping.get("path") or "")
        expected_conflict = bool(mapping.get("expected_conflict", False))
        if not rel_path:
            findings.append(
                _finding(
                    severity=ERROR,
                    code="wrapper_path_blank",
                    system=system,
                    message="Wrapper mapping path is blank.",
                )
            )
            continue
        if not _path_exists(repo_root, rel_path):
            findings.append(
                _finding(
                    severity=ERROR if not expected_conflict else WARNING,
                    code="wrapper_path_missing",
                    system=system,
                    path=rel_path,
                    message=f"Wrapper mapping file is missing: {rel_path}",
                )
            )
            continue

        text = _path_text(repo_root, rel_path)
        for expected in sorted(mapping.get("expected_contains", [])):
            if expected not in text:
                findings.append(
                    _finding(
                        severity=ERROR if not expected_conflict else WARNING,
                        code="wrapper_expected_target_missing",
                        system=system,
                        path=rel_path,
                        message=f"Wrapper file does not contain expected target text: {expected}",
                    )
                )
            elif expected_conflict:
                findings.append(
                    _finding(
                        severity=WARNING,
                        code="expected_wrapper_conflict_observed",
                        system=system,
                        path=rel_path,
                        message=f"Expected wrapper conflict remains present: {expected}",
                    )
                )

        for forbidden in sorted(mapping.get("forbidden_contains", [])):
            if forbidden in text:
                findings.append(
                    _finding(
                        severity=ERROR if not expected_conflict else WARNING,
                        code="wrapper_forbidden_target_present",
                        system=system,
                        path=rel_path,
                        message=f"Wrapper file contains forbidden target text: {forbidden}",
                    )
                )

    return findings


def _check_forbidden_legacy_targets(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    targets = manifest.get("forbidden_legacy_targets", [])
    if not isinstance(targets, list):
        return [
            _finding(
                severity=ERROR,
                code="forbidden_legacy_targets_invalid",
                system="manifest",
                message="forbidden_legacy_targets must be a list.",
            )
        ]

    for target in sorted(targets, key=lambda item: str(item.get("target", "")) if isinstance(item, dict) else ""):
        if not isinstance(target, dict):
            continue
        system = str(target.get("system") or "manifest")
        needle = str(target.get("target") or "")
        expected_conflict = bool(target.get("expected_conflict", False))
        paths = target.get("paths", [])
        if not isinstance(paths, list) or any(not isinstance(rel_path, str) for rel_path in paths):
            findings.append(
                _finding(
                    severity=ERROR,
                    code="forbidden_target_paths_invalid",
                    system=system,
                    message="forbidden_legacy_targets[*].paths must be a list of strings.",
                    details={"target": needle} if needle else None,
                )
            )
            continue
        for rel_path in sorted(paths):
            if not _path_exists(repo_root, rel_path):
                findings.append(
                    _finding(
                        severity=ERROR,
                        code="forbidden_target_scan_path_missing",
                        system=system,
                        path=rel_path,
                        message=f"Cannot scan missing forbidden-target path: {rel_path}",
                    )
                )
                continue
            if needle and needle in _path_text(repo_root, rel_path):
                findings.append(
                    _finding(
                        severity=WARNING if expected_conflict else ERROR,
                        code="forbidden_legacy_target_present",
                        system=system,
                        path=rel_path,
                        message=f"Forbidden legacy target is referenced: {needle}",
                    )
                )
    return findings


def _check_known_conflicts(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    conflicts = manifest.get("known_conflicts", [])
    if not isinstance(conflicts, list):
        return [
            _finding(
                severity=ERROR,
                code="known_conflicts_invalid",
                system="manifest",
                message="known_conflicts must be a list.",
            )
        ]

    for conflict in sorted(conflicts, key=lambda item: (str(item.get("system", "")), str(item.get("type", ""))) if isinstance(item, dict) else ("", "")):
        if not isinstance(conflict, dict):
            continue
        system = str(conflict.get("system") or "UNKNOWN")
        conflict_type = str(conflict.get("type") or "conflict")
        observed_paths: list[str] = []
        missing_paths: list[str] = []
        for evidence in conflict.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            rel_path = str(evidence.get("path") or "")
            if not rel_path:
                continue
            if not _path_exists(repo_root, rel_path):
                missing_paths.append(rel_path)
                continue
            text = _path_text(repo_root, rel_path)
            patterns = [str(pattern) for pattern in evidence.get("patterns", [])]
            if all(pattern in text for pattern in patterns):
                observed_paths.append(rel_path)

        if observed_paths:
            findings.append(
                _finding(
                    severity=WARNING,
                    code=f"expected_{conflict_type}",
                    system=system,
                    message=str(conflict.get("observed") or "Expected conflict remains present."),
                    details={
                        "expected": conflict.get("expected"),
                        "observed_paths": sorted(observed_paths),
                    },
                )
            )
        elif missing_paths:
            findings.append(
                _finding(
                    severity=WARNING,
                    code=f"expected_{conflict_type}_evidence_missing",
                    system=system,
                    message="Expected-conflict evidence path is missing.",
                    details={"missing_paths": sorted(missing_paths)},
                )
            )
        else:
            findings.append(
                _finding(
                    severity=INFO,
                    code=f"expected_{conflict_type}_not_observed",
                    system=system,
                    message="Expected conflict was not observed in the declared evidence paths.",
                )
            )
    return findings


def verify_manifest(manifest: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Run deterministic static checks and return a machine-readable report."""
    findings: list[dict[str, Any]] = []
    findings.extend(_check_repo_identity(manifest, repo_root))
    findings.extend(_check_system_entries(manifest, repo_root))
    findings.extend(_check_wrapper_mappings(manifest.get("wrapper_mappings", []), repo_root))
    findings.extend(_check_forbidden_legacy_targets(manifest, repo_root))
    findings.extend(_check_ports(manifest, repo_root))
    findings.extend(_check_known_conflicts(manifest, repo_root))

    sorted_findings = _sort_findings(findings)
    summary = {
        "errors": sum(1 for finding in sorted_findings if finding["severity"] == ERROR),
        "infos": sum(1 for finding in sorted_findings if finding["severity"] == INFO),
        "warnings": sum(1 for finding in sorted_findings if finding["severity"] == WARNING),
    }
    return {
        "check": "static",
        "findings": sorted_findings,
        "ok": summary["errors"] == 0,
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify Dopemux runtime authority manifest.")
    parser.add_argument(
        "--manifest",
        default="config/runtime_authority_manifest.json",
        help="Path to runtime authority manifest JSON.",
    )
    parser.add_argument(
        "--check",
        choices=("static",),
        default="static",
        help="Verification mode. Static mode performs no network calls and no mutations.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = REPO_ROOT / manifest_path

    try:
        manifest = _read_json(manifest_path)
        report = verify_manifest(manifest, REPO_ROOT)
    except Exception as exc:
        report = {
            "check": args.check,
            "findings": [
                _finding(
                    severity=ERROR,
                    code="verifier_exception",
                    system="verifier",
                    message=str(exc),
                )
            ],
            "ok": False,
            "summary": {"errors": 1, "infos": 0, "warnings": 0},
        }

    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
