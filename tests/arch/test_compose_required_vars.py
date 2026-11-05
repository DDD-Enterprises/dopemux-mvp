"""Drift gate: every compose.yml ``${VAR:?...}`` guard must be covered.

``dopemux mcp`` runs ``docker compose -f compose.yml ...`` with the environment
built by ``env_with_compose_interpolation()``. Compose interpolates the WHOLE
file, so one unset ``:?`` variable fails every service. A new ``:?`` guard must
either be supplied by the wrapper or be listed as always set by the shell.
"""

from __future__ import annotations

import re
from pathlib import Path

from dopemux.mcp import docker_runtime as dr

REPO_ROOT = Path(__file__).parent.parent.parent
COMPOSE_PATH = REPO_ROOT / "compose.yml"

REQUIRED_VAR_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*):\?")

# Variables every login shell exports; the wrapper need not supply them.
ALWAYS_SET = {"HOME"}

# Snapshot of the required set at the time the wrapper was extended. A new
# guard surfaces here first and must be consciously covered.
EXPECTED_REQUIRED = {"HOST_CODE_PARENT_DIR", "DOPECON_BRIDGE_TOKEN", "HOME"}


def _required_vars() -> set[str]:
    return set(
        REQUIRED_VAR_RE.findall(COMPOSE_PATH.read_text(encoding="utf-8"))
    )


def test_compose_required_set_is_known():
    assert _required_vars() == EXPECTED_REQUIRED


def test_every_required_compose_var_is_covered_by_wrapper():
    wrapper_keys = set(dr.env_with_compose_interpolation({}))
    uncovered = _required_vars() - wrapper_keys - ALWAYS_SET
    assert not uncovered, (
        "compose.yml requires variables that env_with_compose_interpolation() "
        f"does not supply: {sorted(uncovered)}"
    )
