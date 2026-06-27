"""dopemux.pcp.dcp_extension_export — DCP-aware enrichment of the generic PCP export.

``dopemux.pcp.exporter.export_evidence`` is deliberately project-agnostic and emits
``proof_manifest = {state: ABSENT, freshness: UNKNOWN}`` for every repository. This
module is the DCP EXTENSION seam: when the target repo carries the DCP extension
(its ``schemas/dcp_extension/extension_manifest.dcp.json`` manifest), it resolves the
declared proof-family mapping (the manifest's ``capabilities.proof_status_mappings``
→ ``proof_status_map.dcp.json`` → ``proof_pointers``) and enriches the export's
``proof_manifest`` from the actual repo state — keeping the result valid against
``schemas/project_control_plane/project_evidence_export.schema.json``.

The generic exporter is NOT modified — this seam wraps it. When no DCP extension is
detected the generic export is returned unchanged (project-agnostic contract intact).

Scope (increment 1): resolves PRESENCE of the declared proof roots. SHA-based
freshness (CURRENT/STALE) is deferred — proof-bundle formats are heterogeneous and
have no canonical schema yet, so ``freshness`` stays ``UNKNOWN`` rather than guessed.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
from typing import Any

from dopemux.pcp.exporter import _git, export_evidence

_DCP_MANIFEST_REL = "schemas/dcp_extension/extension_manifest.dcp.json"


def _load_json(path: pathlib.Path) -> dict[str, Any] | None:
    """Read a JSON object from *path*; None on missing/unreadable/invalid JSON."""
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _repo_root(repo_path: str | os.PathLike) -> pathlib.Path | None:
    """Resolve the git top-level for *repo_path* (mirrors export_evidence); None if not a repo."""
    try:
        top = _git(
            ["rev-parse", "--show-toplevel"],
            cwd=str(pathlib.Path(repo_path).resolve()),
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return pathlib.Path(top)


def _proof_pointers(root: pathlib.Path) -> list[dict[str, Any]]:
    """Proof pointers declared by the DCP manifest's ``proof_status_mappings`` artifacts."""
    manifest = _load_json(root / _DCP_MANIFEST_REL) or {}
    mappings = (manifest.get("capabilities") or {}).get("proof_status_mappings") or []
    pointers: list[dict[str, Any]] = []
    for rel in mappings:
        if not isinstance(rel, str):
            continue
        artifact = _load_json(root / rel)
        if artifact:
            for ptr in artifact.get("proof_pointers") or []:
                if isinstance(ptr, dict):
                    pointers.append(ptr)
    return pointers


_HEAD_SHA_FIELDS = ("head", "head_sha", "git_sha", "commit_sha", "commit", "sha")
_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


def _proof_freshness(proof_path: pathlib.Path, head_sha: str) -> str:
    """Freshness of a proof artifact relative to the current repo head.

    CURRENT when the artifact records the current head SHA, STALE when it records a
    different one, UNKNOWN when it is not JSON or carries no recognizable head-SHA
    field. Proof-bundle formats are heterogeneous; this reads only a recognized field
    (dopemux ``PROOF.json`` uses ``head``) and never guesses freshness otherwise.
    """
    data = _load_json(proof_path)
    if not data:
        return "UNKNOWN"
    current = head_sha.strip().lower()
    for field in _HEAD_SHA_FIELDS:
        recorded = data.get(field)
        if isinstance(recorded, str) and _SHA_RE.match(recorded.strip().lower()):
            recorded = recorded.strip().lower()
            if recorded == current or current.startswith(recorded) or recorded.startswith(current):
                return "CURRENT"
            return "STALE"
    return "UNKNOWN"


def export_evidence_with_dcp(repo_path: str | os.PathLike = ".") -> dict:
    """Generic PCP export enriched with DCP proof-family data when the repo is a DCP project.

    Returns the unmodified generic export when no DCP extension manifest is present.
    The returned dict still validates against
    ``schemas/project_control_plane/project_evidence_export.schema.json``.
    """
    result = export_evidence(repo_path)
    root = _repo_root(repo_path)
    if root is None or not (root / _DCP_MANIFEST_REL).is_file():
        return result

    pointers = _proof_pointers(root)
    present = [
        p
        for p in pointers
        if isinstance(p.get("path"), str) and p["path"] and (root / p["path"]).is_file()
    ]

    if present:
        proof_path = present[0]["path"]
        freshness = _proof_freshness(root / proof_path, result["repo_state"]["head_sha"])
        result["proof_manifest"] = {
            "state": "PRESENT",
            "path": proof_path,
            "freshness": freshness,
        }
        reason = (
            f"DCP proof-family mapping resolved: {len(present)}/{len(pointers)} declared "
            f"proof root(s) present; freshness={freshness} (from recorded head SHA)."
        )
    else:
        result["proof_manifest"] = {"state": "ABSENT", "path": None, "freshness": "UNKNOWN"}
        reason = "DCP proof-family mapping resolved: no declared proof root present in repo."

    # proof_manifest is now DCP-assessed, not generically unknowable. Update the reason
    # in place; result stays UNKNOWN because freshness remains unresolved (increment 1).
    for entry in result.get("unknowns", []):
        if isinstance(entry, dict) and entry.get("field") == "proof_manifest":
            entry["reason"] = reason
    return result
