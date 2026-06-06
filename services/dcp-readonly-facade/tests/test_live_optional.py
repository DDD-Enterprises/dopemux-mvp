"""Optional live smoke tests against real local backends.

Skipped by default. Enable with DCP_FACADE_LIVE_TESTS=1 and point
DCP_FACADE_REGISTRY at a real registry whose first enabled project binds a
reachable ConPort profile. These tests make real loopback HTTP calls; they
never mutate anything (read-only tools only).
"""

from __future__ import annotations

import os

import pytest

_LIVE = os.getenv("DCP_FACADE_LIVE_TESTS") == "1"

pytestmark = pytest.mark.skipif(not _LIVE, reason="set DCP_FACADE_LIVE_TESTS=1 to run live tests")


def _registry():
    from dcp_facade.registry import load_registry

    return load_registry(os.getenv("DCP_FACADE_REGISTRY"))


def test_live_search_decisions_enveloped():
    from dcp_facade import envelope as E
    from dcp_facade import tools

    reg = _registry()
    enabled = reg.enabled_projects()
    if not enabled:
        pytest.skip("no enabled projects in the live registry")
    pid = enabled[0].project_id
    env = tools.search_decisions(reg, pid, limit=5)
    # Live backend may be up (OK) or down (PARTIAL/BLOCKED) — either way the
    # response must be a well-formed CANONICAL envelope, never fabricated data.
    assert set(env.keys()) == set(E.ENVELOPE_FIELDS)
    assert env["status"] in (E.OK, E.PARTIAL, E.BLOCKED)
    assert env["source_system"] == E.SOURCE_CONPORT
