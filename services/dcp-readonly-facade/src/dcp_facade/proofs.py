"""Proof-bundle reads (containment + symlink safe, bounded).

Proof bundles live at ``<workspace>/proof/<BUNDLE_ID>/``. All reads are
confined to the resolved workspace's ``proof/`` directory: the ``bundle_id`` is
validated as a single path segment, the target is canonicalized (``resolve()``)
and re-checked with ``relative_to`` against the canonical proof root, and each
file is canonicalized and re-checked before being **opened by its resolved
path** (so a check/use TOCTOU swap cannot redirect the read). Reads are bounded
to ``_MAX_FILE_BYTES`` at I/O time, and directory scans are bounded before
sorting. This module performs no writes.

Filtering uses a **literal substring** (``packet_filter``), not a regex — an
untrusted caller must never be able to supply a pattern that triggers
catastrophic backtracking (ReDoS).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

PROOF_DIRNAME = "proof"
MAX_BUNDLES = 20
_SCAN_LIMIT = MAX_BUNDLES * 5  # cap directory entries scanned before sort (DoS guard)
_MAX_FILE_BYTES = 256 * 1024
_BUNDLE_FILES = ("PROOF.json", "COMMAND_LOG.md", "AUDIT.md")


def _proof_root(workspace: Path) -> Path:
    return workspace / PROOF_DIRNAME


def _safe_bundle_id(bundle_id: object) -> bool:
    """A bundle id must be a single path segment, no separators/traversal."""
    if not isinstance(bundle_id, str) or not bundle_id:
        return False
    if "/" in bundle_id or "\\" in bundle_id:
        return False
    if bundle_id.startswith(".") or ".." in bundle_id:
        return False
    return True


def list_bundles(
    workspace: Path,
    packet_filter: Optional[str] = None,
    cap: int = MAX_BUNDLES,
    scan_limit: int = _SCAN_LIMIT,
) -> tuple[list[dict], bool]:
    """List proof bundles, filtered by a literal substring of the bundle id.

    Returns ``(bundles, truncated)``. The directory scan is bounded to
    ``scan_limit`` entries before sorting (guards against a workspace with an
    enormous ``proof/`` directory).
    """
    root = _proof_root(workspace)
    if not root.is_dir():
        return [], False

    names: list[str] = []
    truncated = False
    try:
        for entry in root.iterdir():
            try:
                if not entry.is_dir():
                    continue
            except OSError:
                continue
            names.append(entry.name)
            if len(names) >= scan_limit:
                truncated = True
                break
    except OSError:
        return [], False

    names.sort()
    if packet_filter:
        flt = str(packet_filter)
        names = [n for n in names if flt in n]
    if len(names) > cap:
        truncated = True
        names = names[:cap]

    out: list[dict] = []
    for name in names:
        bdir = root / name
        try:
            files = sorted(f.name for f in bdir.iterdir() if f.is_file())
        except OSError:
            files = []
        out.append({"bundle_id": name, "files": files})
    return out, truncated


def fetch_bundle(
    workspace: Path,
    bundle_id: object,
    current_head: Optional[str] = None,
) -> tuple[Optional[dict], Optional[str], list[str]]:
    """Fetch one bundle's known files. Returns (data, block_reason, warnings).

    Containment is enforced on the resolved bundle dir and on each resolved
    file; files are opened by their resolved path with a bounded read.
    """
    if not _safe_bundle_id(bundle_id):
        return None, "invalid bundle_id", []

    try:
        root = _proof_root(workspace).resolve()
    except (OSError, RuntimeError):
        return None, "proof root could not be resolved", []
    try:
        target = (root / str(bundle_id)).resolve()
    except (OSError, RuntimeError):
        return None, "bundle path could not be resolved", []
    try:
        target.relative_to(root)
    except ValueError:
        return None, "bundle path escapes proof root", []
    if not target.is_dir():
        return None, "bundle not found", []

    warnings: list[str] = []
    contents: dict[str, str] = {}
    for fname in _BUNDLE_FILES:
        f = target / fname
        if not f.is_file():
            continue
        try:
            resolved_f = f.resolve()
            resolved_f.relative_to(root)  # reject symlinked files pointing outside
        except (ValueError, OSError, RuntimeError):
            warnings.append(f"{fname} skipped (escapes proof root)")
            continue
        # Bounded read of the RESOLVED path (avoids unbounded read + TOCTOU swap).
        try:
            with resolved_f.open("rb") as fh:
                raw = fh.read(_MAX_FILE_BYTES + 1)
        except OSError:
            warnings.append(f"{fname} unreadable")
            continue
        if len(raw) > _MAX_FILE_BYTES:
            raw = raw[:_MAX_FILE_BYTES]
            warnings.append(f"{fname} truncated")
        contents[fname] = raw.decode("utf-8", errors="replace")

    bundle_head: Optional[str] = None
    pj = contents.get("PROOF.json")
    if pj:
        try:
            meta = json.loads(pj)
            bundle_head = meta.get("head_sha") or meta.get("commit_sha")
        except (ValueError, AttributeError):
            bundle_head = None

    stale: Optional[bool] = None
    if current_head and bundle_head:
        stale = bundle_head != current_head
        if stale:
            warnings.append("stale proof bundle (head_sha mismatch)")

    data = {
        "bundle_id": str(bundle_id),
        "files": sorted(contents.keys()),
        "contents": contents,
        "bundle_head_sha": bundle_head,
        "stale": stale,
    }
    return data, None, warnings
