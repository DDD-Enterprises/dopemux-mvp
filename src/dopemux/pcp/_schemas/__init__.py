"""Bundled Project Control Plane JSON schemas (wheel-safe loader).

The canonical schemas live at the repo root under
``schemas/project_control_plane/``. These vendored copies travel *inside* the
installed package so the four PCP modules that load a schema **at import time**
— :mod:`dopemux.pcp.exporter`, :mod:`dopemux.pcp.negative_cases`,
:mod:`dopemux.pcp.pr_steward`, and :mod:`dopemux.pcp.bridge.fastapi_bridge` —
import cleanly both from the source tree (``src/`` on ``sys.path``) and from an
installed wheel, where no repo root exists.

Parity with the canonical schemas is enforced by
``tests/project_control_plane/test_schema_bundle_parity.py``: every vendored
copy must be byte-identical to its canonical source, so a built wheel can never
ship a stale or contradictory contract.

This module carries no Project-Control-Plane logic of its own — it is purely a
schema-file location/bundling shim.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

__all__ = ["load_schema"]


def load_schema(filename: str) -> dict[str, Any]:
    """Return the parsed JSON schema *filename* from this bundled package.

    Resolves the resource via :func:`importlib.resources.files` so the lookup
    works identically from the source tree and from an installed wheel — no
    repo-root-relative path is computed and no current working directory is
    assumed.

    Parameters
    ----------
    filename:
        The schema file name, e.g. ``"merge_readiness.schema.json"``.

    Returns
    -------
    dict
        The parsed JSON schema.

    Raises
    ------
    FileNotFoundError
        If *filename* is not bundled in this package.
    """
    resource = resources.files(__name__).joinpath(filename)
    with resource.open("r", encoding="utf-8") as fh:
        return json.load(fh)
