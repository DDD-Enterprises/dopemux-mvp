"""Parity guard: bundled PCP schemas must match the canonical repo-root copies.

The four import-time schema loaders in ``dopemux.pcp.*`` read their schema from
vendored package-data copies under ``src/dopemux/pcp/_schemas/`` so a built
wheel works without a repo root. Those copies MUST stay byte-identical to the
canonical schemas at ``schemas/project_control_plane/`` — otherwise a wheel
could ship a stale or contradictory contract while source-tree tests (which read
the canonical copies directly) stay green. This guard fails closed on any drift.

It also exercises the wheel-safe loader (:func:`dopemux.pcp._schemas.load_schema`)
to prove it resolves the bundled resource and returns the canonical content.
"""

from __future__ import annotations

import json
import pathlib

import pytest

# tests/project_control_plane/test_*.py -> 3 levels up = repo root
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_CANONICAL_DIR = _REPO_ROOT / "schemas" / "project_control_plane"
_BUNDLED_DIR = _REPO_ROOT / "src" / "dopemux" / "pcp" / "_schemas"

# Exactly the schemas loaded at import time by the dopemux.pcp.* modules:
#   exporter            -> project_evidence_export.schema.json
#   negative_cases      -> negative_case_result.schema.json,
#                          project_evidence_export.schema.json
#   pr_steward          -> merge_readiness.schema.json
#   bridge.fastapi_bridge -> live_write_ready.schema.json
_VENDORED_SCHEMAS = [
    "project_evidence_export.schema.json",
    "negative_case_result.schema.json",
    "merge_readiness.schema.json",
    "live_write_ready.schema.json",
]


@pytest.mark.parametrize("name", _VENDORED_SCHEMAS)
def test_bundled_schema_is_byte_identical_to_canonical(name: str) -> None:
    canonical = _CANONICAL_DIR / name
    bundled = _BUNDLED_DIR / name
    assert canonical.exists(), f"canonical schema missing: {canonical}"
    assert bundled.exists(), (
        f"bundled schema missing: {bundled} — the wheel-safe copy must exist "
        f"so an installed wheel can load it without a repo root."
    )
    assert bundled.read_bytes() == canonical.read_bytes(), (
        f"bundled schema {name} has drifted from canonical "
        f"{canonical.relative_to(_REPO_ROOT)} — re-copy it verbatim."
    )


@pytest.mark.parametrize("name", _VENDORED_SCHEMAS)
def test_load_schema_returns_canonical_content(name: str) -> None:
    from dopemux.pcp._schemas import load_schema

    loaded = load_schema(name)
    canonical = json.loads((_CANONICAL_DIR / name).read_text(encoding="utf-8"))
    assert loaded == canonical, (
        f"load_schema({name!r}) did not return the canonical parsed schema."
    )
