"""Run artifacts for reproducibility and observability (manifest + report)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from chatx import __version__ as CHATX_VERSION


def _sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def write_manifest(
    *,
    out_dir: Path,
    db_path: Optional[Path],
    attachments_dir: Optional[Path] = None,
    schema_version: str = "1.0",
) -> Path:
    """Write manifest.json with inputs and their hashes.

    Returns the path to the manifest file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, Any] = {
        "version": CHATX_VERSION,
        "schema_version": schema_version,
        "inputs": {},
        "input_hashes": {},
    }
    if db_path:
        manifest["inputs"]["db_path"] = str(db_path)
        h = _sha256_file(db_path)
        if h:
            manifest["input_hashes"]["db_sha256"] = h
    if attachments_dir:
        manifest["inputs"]["attachments_dir"] = str(attachments_dir)

    path = out_dir / "manifest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path

