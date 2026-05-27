"""Deterministic, secret-safe evidence bundle builder for audit packets.

Produces a self-contained bundle directory with:
  manifest.json      — sorted file inventory + metadata
  request.json       — raw file contents (included files only)
  checksums.sha256   — sha256:<hex>  <path> lines (sorted)
  redactions.json    — records of files redacted or excluded
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Secret patterns (fail-closed: reject unless allow_redact=True)
# ---------------------------------------------------------------------------
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token_ghp", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("github_token_gho", re.compile(r"gho_[A-Za-z0-9]{36}")),
    ("github_token_ghs", re.compile(r"ghs_[A-Za-z0-9]{36}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{36,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("private_key_header", re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----")),
    (
        "generic_secret",
        re.compile(
            r'(?i)(?:api_key|api_secret|token|secret|password|bearer)\s*[=:]\s*["\']?([A-Za-z0-9+/\-_]{16,})',
        ),
    ),
]


def _scan_for_secrets(content: str) -> str | None:
    """Return the first secret kind found in *content*, or None if clean."""
    for kind, pattern in _SECRET_PATTERNS:
        if pattern.search(content):
            return kind
    return None


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

def _check_path_safe(source: Path, allowed_root: Path) -> None:
    """Raise ValueError if *source* escapes *allowed_root* or is a symlink."""
    if source.is_symlink():
        raise ValueError(f"symlinks rejected: {source}")
    try:
        resolved = source.resolve()
        resolved.relative_to(allowed_root.resolve())
    except ValueError:
        raise ValueError(f"path escape rejected: {source} not under {allowed_root}")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FileRecord:
    path: str            # relative to source_root, forward-slash separated
    sha256: str          # hex digest, or "" if excluded/redacted before hashing
    size_bytes: int      # 0 if excluded/redacted before reading
    kind: str            # "included" | "redacted" | "excluded"
    redaction_reason: str | None = None
    exclusion_reason: str | None = None


@dataclass
class BundleResult:
    bundle_path: Path
    manifest_path: Path
    checksums_path: Path
    request_path: Path
    redactions_path: Path
    files: list[FileRecord] = field(default_factory=list)
    rejected: list[FileRecord] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_bundle(
    sources: Sequence[Path],
    dest: Path,
    *,
    allowed_root: Path,
    tp_id: str | None = None,
    bundle_id: str | None = None,
    created_at: str | None = None,
    allow_redact: bool = False,
) -> BundleResult:
    """Build a deterministic evidence bundle at *dest*.

    Args:
        sources:      Files to include (must all be under allowed_root).
        dest:         Destination directory (must not already exist).
        allowed_root: Root under which all sources must reside.
        tp_id:        TP identifier embedded in manifest (e.g. TP-DMX-AUDIT-BUNDLE-001).
        bundle_id:    Unique bundle ID; defaults to tp_id or ISO timestamp.
        created_at:   ISO-8601 timestamp; defaults to now (UTC). Caller-supplied
                      value enables reproducible tests.
        allow_redact: When True, files containing secrets are redacted rather than
                      rejected. Default is False (fail-closed).

    Raises:
        FileExistsError: if *dest* already exists.
        ValueError:      on path escape, symlink, or secret (when allow_redact=False).
    """
    if dest.exists():
        raise FileExistsError(f"bundle destination already exists: {dest}")

    dest.mkdir(parents=True)

    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()

    if bundle_id is None:
        bundle_id = tp_id or created_at

    # relative source_root — do NOT embed resolved host paths
    source_root_str = str(allowed_root)

    included: list[FileRecord] = []
    rejected_list: list[FileRecord] = []
    request_contents: dict[str, str] = {}

    for source in sources:
        rel = _process_source(
            source,
            allowed_root=allowed_root,
            allow_redact=allow_redact,
            included=included,
            rejected_list=rejected_list,
            request_contents=request_contents,
        )
        _ = rel  # used inside helper

    # Sort for determinism
    included.sort(key=lambda r: r.path)
    rejected_list.sort(key=lambda r: r.path)

    # Write request.json
    request_path = dest / "request.json"
    request_path.write_text(
        json.dumps(request_contents, sort_keys=True, indent=2), encoding="utf-8"
    )

    # Write checksums.sha256
    checksums_path = dest / "checksums.sha256"
    checksum_lines = [
        f"sha256:{r.sha256}  {r.path}"
        for r in included
        if r.kind == "included" and r.sha256
    ]
    checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    # Write redactions.json
    redactions_path = dest / "redactions.json"
    redaction_records = [r for r in included if r.kind == "redacted"] + rejected_list
    redactions_path.write_text(
        json.dumps(
            [asdict(r) for r in redaction_records], sort_keys=True, indent=2
        ),
        encoding="utf-8",
    )

    # Write manifest.json
    manifest_path = dest / "manifest.json"
    manifest = {
        "schema_version": "1.0.0",
        "bundle_id": bundle_id,
        "tp_id": tp_id,
        "created_at": created_at,
        "source_root": source_root_str,
        "files": [asdict(r) for r in included],
        "rejected": [asdict(r) for r in rejected_list],
        "redactions_path": "redactions.json",
        "checksums_path": "checksums.sha256",
        "request_path": "request.json",
    }
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8"
    )

    return BundleResult(
        bundle_path=dest,
        manifest_path=manifest_path,
        checksums_path=checksums_path,
        request_path=request_path,
        redactions_path=redactions_path,
        files=included,
        rejected=rejected_list,
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _process_source(
    source: Path,
    *,
    allowed_root: Path,
    allow_redact: bool,
    included: list[FileRecord],
    rejected_list: list[FileRecord],
    request_contents: dict[str, str],
) -> str:
    """Process a single source path; mutates included/rejected_list/request_contents."""
    # Compute relative path for manifest (forward slashes, no host path)
    try:
        rel_path = source.resolve().relative_to(allowed_root.resolve())
        rel_str = rel_path.as_posix()
    except ValueError:
        # Path escape caught before hashing
        rejected_list.append(
            FileRecord(
                path=str(source),
                sha256="",
                size_bytes=0,
                kind="excluded",
                exclusion_reason="path_escape",
            )
        )
        return str(source)

    # Safety checks
    try:
        _check_path_safe(source, allowed_root)
    except ValueError as exc:
        reason = "symlink" if "symlink" in str(exc) else "path_escape"
        rejected_list.append(
            FileRecord(
                path=rel_str,
                sha256="",
                size_bytes=0,
                kind="excluded",
                exclusion_reason=reason,
            )
        )
        return rel_str

    # Missing file
    if not source.exists():
        rejected_list.append(
            FileRecord(
                path=rel_str,
                sha256="",
                size_bytes=0,
                kind="excluded",
                exclusion_reason="file_not_found",
            )
        )
        return rel_str

    raw = source.read_bytes()
    digest = _sha256(raw)
    size = len(raw)

    # Secret scan
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        # Binary files: include as-is (no text secret scan possible)
        included.append(
            FileRecord(path=rel_str, sha256=digest, size_bytes=size, kind="included")
        )
        request_contents[rel_str] = f"<binary file: {size} bytes>"
        return rel_str

    secret_kind = _scan_for_secrets(text)
    if secret_kind:
        if allow_redact:
            included.append(
                FileRecord(
                    path=rel_str,
                    sha256="",
                    size_bytes=0,
                    kind="redacted",
                    redaction_reason=f"secret_pattern:{secret_kind}",
                )
            )
            request_contents[rel_str] = f"<redacted: secret_pattern:{secret_kind}>"
        else:
            rejected_list.append(
                FileRecord(
                    path=rel_str,
                    sha256="",
                    size_bytes=0,
                    kind="excluded",
                    exclusion_reason=f"secret_pattern:{secret_kind}",
                )
            )
        return rel_str

    included.append(
        FileRecord(path=rel_str, sha256=digest, size_bytes=size, kind="included")
    )
    request_contents[rel_str] = text
    return rel_str


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build-evidence-bundle",
        description="Build a deterministic, secret-safe evidence bundle.",
    )
    parser.add_argument("sources", nargs="+", type=Path, help="Source files to bundle")
    parser.add_argument("--dest", required=True, type=Path, help="Output bundle directory")
    parser.add_argument(
        "--allowed-root",
        required=True,
        type=Path,
        help="All sources must reside under this root",
    )
    parser.add_argument("--tp-id", default=None, help="TP identifier")
    parser.add_argument("--bundle-id", default=None, help="Bundle ID (default: tp-id or timestamp)")
    parser.add_argument("--created-at", default=None, help="ISO-8601 timestamp for reproducibility")
    parser.add_argument(
        "--allow-redact",
        action="store_true",
        default=False,
        help="Redact files containing secrets instead of rejecting (default: reject)",
    )

    args = parser.parse_args(argv)

    try:
        result = build_bundle(
            sources=args.sources,
            dest=args.dest,
            allowed_root=args.allowed_root,
            tp_id=args.tp_id,
            bundle_id=args.bundle_id,
            created_at=args.created_at,
            allow_redact=args.allow_redact,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rejected_count = len(result.rejected)
    redacted_count = sum(1 for r in result.files if r.kind == "redacted")
    included_count = sum(1 for r in result.files if r.kind == "included")

    print(f"bundle: {result.bundle_path}")
    print(f"  included: {included_count}  redacted: {redacted_count}  rejected: {rejected_count}")
    if rejected_count:
        for r in result.rejected:
            print(f"  REJECTED {r.path}: {r.exclusion_reason}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(_cli())
