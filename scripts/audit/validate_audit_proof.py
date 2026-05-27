#!/usr/bin/env python3
"""CLI validator for PROOF.json embedded_audit objects.

Validates the ``embedded_audit`` sub-object inside one or more PROOF.json
files against ``schemas/proof/embedded_audit.schema.json`` using
jsonschema Draft7Validator.

Exit codes:
  0 — all validated bundles PASS
  1 — one or more bundles FAIL schema validation
  2 — usage error (bad arguments, missing schema)

Usage examples::

    # Validate a single bundle
    python scripts/audit/validate_audit_proof.py proof/TP-DMX-PR-FIXTURES-011/PROOF.json

    # Validate multiple bundles
    python scripts/audit/validate_audit_proof.py proof/TP-*/PROOF.json

    # Scan all PROOF.json files under proof/
    python scripts/audit/validate_audit_proof.py --all proof/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
    import jsonschema.exceptions
except ImportError:  # pragma: no cover
    print("ERROR: jsonschema is not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = _REPO_ROOT / "schemas" / "proof" / "embedded_audit.schema.json"


# ---------------------------------------------------------------------------
# Core validation helpers
# ---------------------------------------------------------------------------


def load_schema(schema_path: Path) -> dict:
    """Load and return the JSON Schema dict."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Schema file is not valid JSON: {exc}") from exc


def collect_proof_paths(paths: list[str], scan_root: str | None) -> list[Path]:
    """Return deduplicated, sorted list of PROOF.json paths to validate."""
    collected: list[Path] = []

    if scan_root is not None:
        root = Path(scan_root)
        if not root.is_dir():
            raise ValueError(f"--all argument must be a directory, got: {scan_root}")
        collected.extend(sorted(root.rglob("PROOF.json")))

    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"PROOF.json not found: {path}")
        collected.append(path)

    # Deduplicate while preserving deterministic order.
    seen: dict[Path, None] = {}
    for p in collected:
        seen[p.resolve()] = None
    return sorted(seen.keys())


def _rel_path(proof_path: Path) -> Path:
    """Return path relative to repo root when possible, else absolute."""
    try:
        return proof_path.relative_to(_REPO_ROOT)
    except ValueError:
        return proof_path


def validate_proof_file(
    proof_path: Path, schema: dict, validator_cls: type
) -> tuple[str, list[str]]:
    """Validate a single PROOF.json file.

    Returns ``(status, errors)`` where *status* is ``"PASS"`` or ``"FAIL"``
    and *errors* is a (possibly empty) list of human-readable error strings.
    """
    try:
        data = json.loads(proof_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "FAIL", [f"JSON parse error: {exc}"]

    if "embedded_audit" not in data:
        return "FAIL", ["missing top-level field: embedded_audit"]

    embedded = data["embedded_audit"]
    if not isinstance(embedded, dict):
        return "FAIL", [f"embedded_audit: expected object, got {type(embedded).__name__}"]

    validator = validator_cls(schema)
    raw_errors = sorted(
        validator.iter_errors(embedded),
        key=lambda e: ".".join(map(str, e.path)),
    )
    if raw_errors:
        return "FAIL", [
            f"{'.'.join(map(str, e.path)) or '(root)'}: {e.message}"
            for e in raw_errors
        ]
    return "PASS", []


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate PROOF.json embedded_audit objects against the schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "proof_files",
        nargs="*",
        metavar="PROOF.json",
        help="One or more PROOF.json file paths to validate.",
    )
    parser.add_argument(
        "--all",
        dest="scan_root",
        metavar="DIR",
        default=None,
        help="Recursively scan DIR for PROOF.json files and validate all of them.",
    )
    parser.add_argument(
        "--schema",
        dest="schema_path",
        metavar="PATH",
        default=str(DEFAULT_SCHEMA_PATH),
        help=(
            "Path to embedded_audit.schema.json. "
            f"Default: {DEFAULT_SCHEMA_PATH}"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file PASS output; only print failures and the summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: C901 (acceptable complexity)
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.proof_files and args.scan_root is None:
        parser.print_help()
        return 2

    # Load schema
    schema_path = Path(args.schema_path)
    try:
        schema = load_schema(schema_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Validate schema is internally consistent
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        print(f"ERROR: invalid schema: {exc.message}", file=sys.stderr)
        return 2
    validator_cls = jsonschema.Draft7Validator

    # Collect paths
    try:
        proof_paths = collect_proof_paths(args.proof_files, args.scan_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not proof_paths:
        print("No PROOF.json files found.", file=sys.stderr)
        return 2

    # Validate each file
    pass_count = 0
    fail_count = 0

    for proof_path in proof_paths:
        status, errors = validate_proof_file(proof_path, schema, validator_cls)
        rel = _rel_path(proof_path)

        if status == "PASS":
            pass_count += 1
            if not args.quiet:
                print(f"PASS  {rel}")
        else:
            fail_count += 1
            print(f"FAIL  {rel}")
            for err in errors:
                print(f"      - {err}")

    # Summary line
    total = pass_count + fail_count
    if fail_count == 0:
        print(f"\nResult: {pass_count}/{total} PASS")
        return 0
    else:
        print(f"\nResult: {pass_count}/{total} PASS, {fail_count}/{total} FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
