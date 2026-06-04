"""Regression tests for DiscoveryGate provenance-aware failure policy.

Context (PR #725 review): the TP-2 commit claimed to make non-mandatory
(env_var / global_fallback) server failures ALWAYS emit a WARNING, and to
escalate them to a hard BLOCK under ``strict_optional`` / DOPEMUX_MCP_GATE_STRICT.
The ``__init__`` wiring landed but the ``run()``-side enforcement was lost in a
salvage, so the behaviour was never delivered. The shipped
``test_discovery_gate`` only prints (no assertions), so it passed vacuously and
did not catch the regression.

These tests assert the contract directly by injecting controlled resolver +
discovery results, so they fail closed against the regressed code and stay green
once the ``run()`` logic is restored.
"""

import pytest

from dopemux.mcp.gate import DiscoveryGate


def _make_gate(tmp_path, *, servers, provenance, discovery_servers, strict_optional=None):
    """Build a DiscoveryGate with the resolver + discovery layers stubbed.

    ``servers``/``provenance`` mimic InstanceResolver.resolve(); ``discovery_servers``
    mimics ToolDiscoveryClient.discover()["servers"]. This keeps the test
    deterministic and offline while exercising the real run() logic.
    """
    gate = DiscoveryGate(tmp_path, run_id="test", strict_optional=strict_optional)

    def fake_resolve(profile_name="default"):
        return {"servers": servers, "provenance": provenance, "transports": {}}

    async def fake_discover(resolved_servers):
        return {
            "servers": discovery_servers,
            "reachable": all(s.get("reachable") for s in discovery_servers),
        }

    gate.resolver.resolve = fake_resolve
    gate.discovery.discover = fake_discover
    return gate


@pytest.mark.asyncio
async def test_nonmandatory_unreachable_warns_but_passes(tmp_path):
    """An env_var (non-mandatory) server that is unreachable must WARN, not block."""
    gate = _make_gate(
        tmp_path,
        servers={"opt": {"required_tool_globs": []}},
        provenance={"opt": "env_var"},
        discovery_servers=[
            {"name": "opt", "reachable": False, "status": "unreachable", "tools": []}
        ],
    )
    passed = await gate.run()
    assert passed is True
    assert gate.report["status"] == "PASS"
    assert any("opt" in w for w in gate.report["warnings"]), gate.report["warnings"]


@pytest.mark.asyncio
async def test_nonmandatory_unreachable_blocks_under_strict(tmp_path):
    """Under strict_optional, the same non-mandatory failure escalates to BLOCK."""
    gate = _make_gate(
        tmp_path,
        servers={"opt": {"required_tool_globs": []}},
        provenance={"opt": "env_var"},
        discovery_servers=[
            {"name": "opt", "reachable": False, "status": "unreachable", "tools": []}
        ],
        strict_optional=True,
    )
    passed = await gate.run()
    assert passed is False
    assert gate.report["status"] == "BLOCK"
    assert any("opt" in w for w in gate.report["warnings"]), gate.report["warnings"]


@pytest.mark.asyncio
async def test_mandatory_unreachable_always_blocks(tmp_path):
    """A repo_profile (mandatory) server that is unreachable must always BLOCK."""
    gate = _make_gate(
        tmp_path,
        servers={"repo": {"required_tool_globs": []}},
        provenance={"repo": "repo_profile"},
        discovery_servers=[
            {"name": "repo", "reachable": False, "status": "unreachable", "tools": []}
        ],
    )
    passed = await gate.run()
    assert passed is False
    assert gate.report["status"] == "BLOCK"


@pytest.mark.asyncio
async def test_nonmandatory_missing_glob_warns_passes_then_strict_blocks(tmp_path):
    """A reachable non-mandatory server missing a required glob warns (PASS), and
    BLOCKs under strict_optional. Exercises the missing-globs branch of run()."""
    servers = {"opt": {"required_tool_globs": ["needed_*"]}}
    provenance = {"opt": "env_var"}
    discovery_servers = [
        {"name": "opt", "reachable": True, "status": "ok", "tools": ["other_tool"]}
    ]

    gate = _make_gate(
        tmp_path,
        servers=servers,
        provenance=provenance,
        discovery_servers=discovery_servers,
    )
    passed = await gate.run()
    assert passed is True
    assert gate.report["status"] == "PASS"
    assert "opt" in gate.report["missing_required_tools"]
    assert any("opt" in w for w in gate.report["warnings"]), gate.report["warnings"]

    gate_strict = _make_gate(
        tmp_path,
        servers=servers,
        provenance=provenance,
        discovery_servers=discovery_servers,
        strict_optional=True,
    )
    passed_strict = await gate_strict.run()
    assert passed_strict is False
    assert gate_strict.report["status"] == "BLOCK"


@pytest.mark.asyncio
async def test_mandatory_reachable_with_all_globs_passes(tmp_path):
    """Control: a mandatory server that is reachable with all globs satisfied PASSES
    with no warnings."""
    gate = _make_gate(
        tmp_path,
        servers={"repo": {"required_tool_globs": ["conport_*"]}},
        provenance={"repo": "repo_profile"},
        discovery_servers=[
            {
                "name": "repo",
                "reachable": True,
                "status": "ok",
                "tools": ["conport_decisions_add", "conport_graph_query"],
            }
        ],
    )
    passed = await gate.run()
    assert passed is True
    assert gate.report["status"] == "PASS"
    assert gate.report["warnings"] == []
