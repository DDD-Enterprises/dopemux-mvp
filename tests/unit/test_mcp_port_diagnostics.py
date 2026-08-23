"""Unit tests for dopemux.mcp.port_diagnostics."""

from __future__ import annotations

from dopemux.mcp import port_diagnostics as pd


def _catalog():
    return {
        "version": 1,
        "servers": {
            "pal": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3003/mcp",
            },
            "gpt-researcher": {
                "scope": "singleton",
                "transport": "stdio",
                "reserved_port": 3009,
            },
            "dope-context": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3010/mcp",
            },
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
            },
            "alpha": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "ALPHA_PORT",
                "default_port_base": 5000,
            },
            "beta": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "BETA_PORT",
                "default_port_base": 5000,
            },
        },
    }


def test_allocator_name_and_offset():
    path = "/Users/hue/code/dNh_CRM"
    offset = pd.offset_for_path(path)
    assert 0 <= offset < 100
    assert pd.ALLOCATOR_NAME == "sha1_abs_path_mod_100"
    assert pd.port_for_base(path, 3005) == 3005 + offset


def test_no_collision_when_bases_spaced():
    catalog = _catalog()
    report = pd.diagnose_ports(
        "/tmp/wt-safe-unique-path-zzzz",
        ["conport", "dope-memory", "task-orchestrator"],
        catalog,
        has_lease_registry=False,
        has_live_rebind=False,
    )
    reserved = [c for c in report.collisions if c.kind == "reserved"]
    # May or may not collide depending on path hash — check structure
    assert report.allocator == "sha1_abs_path_mod_100"
    assert report.bucket_count == 100
    codes = {f["code"] for f in report.findings}
    assert "PORT_HASH_BUCKET_COLLISION_RISK" in codes
    assert "PORT_REBIND_MISSING" in codes


def test_reserved_singleton_collision_for_dnh_hash_path():
    """dNh_CRM path is known to map ConPort into reserved singleton ports under pure hash."""
    catalog = _catalog()
    path = "/Users/hue/code/dNh_CRM"
    formula = pd.formula_ports_only(path, ["conport", "dope-memory"], catalog)
    # Document formula ports
    report = pd.diagnose_ports(
        path,
        ["conport", "dope-memory"],
        catalog,
        configured_ports=None,  # pure formula
    )
    reserved_findings = [f for f in report.findings if f["code"] == "PORT_RESERVED_COLLISION"]
    # Pure hash for dNh should hit 3009 and/or 3010 based on investigation notes
    offset = pd.offset_for_path(path)
    assert formula["CONPORT_MCP_PORT"] == 3005 + offset
    if formula["CONPORT_MCP_PORT"] in (3009, 3010) or formula.get("CONPORT_HTTP_PORT") in (3009, 3010):
        assert reserved_findings, "expected reserved collision for dNh pure-hash ports"
    else:
        # Still validate detection works with forced collision
        forced = pd.diagnose_ports(
            path,
            ["conport"],
            catalog,
            configured_ports={"CONPORT_MCP_PORT": 3009},
        )
        assert any(f["code"] == "PORT_RESERVED_COLLISION" for f in forced.findings)


def test_formula_reserved_is_warn_when_configured_safe():
    catalog = _catalog()
    path = "/Users/hue/code/dNh_CRM"
    formula = pd.formula_ports_only(path, ["conport", "dope-memory"], catalog)
    configured = {
        "CONPORT_HTTP_PORT": 3040,
        "CONPORT_MCP_PORT": 3041,
        "CONPORT_INFO_PORT": 4040,
        "DOPE_MEMORY_PORT": 3024,
    }
    report = pd.diagnose_ports(
        path,
        ["conport", "dope-memory"],
        catalog,
        configured_ports=configured,
    )
    reserved = [f for f in report.findings if f["code"] == "PORT_RESERVED_COLLISION"]
    formula_hits = [f for f in reserved if "source=formula" in f["evidence"]]
    formula_hits_reserved = any(
        formula.get(var) in (3009, 3010)
        for var in ("CONPORT_MCP_PORT", "CONPORT_HTTP_PORT")
    )
    assert formula_hits_reserved, (
        f"dNh_CRM hash no longer hits reserved singletons: {formula}"
    )
    assert formula_hits, "expected formula reserved collision for dNh_CRM hash"
    assert all(f["severity"] == "WARN" for f in formula_hits)
    assert all("neutralized=configured" in f["evidence"] for f in formula_hits)
    assert all(
        f["severity"] != "FAIL" or "source=configured" in f["evidence"]
        for f in reserved
    )


def test_configured_reserved_collision_still_fail():
    catalog = _catalog()
    report = pd.diagnose_ports(
        "/tmp/wt-safe-unique-path-zzzz",
        ["conport"],
        catalog,
        configured_ports={"CONPORT_MCP_PORT": 3010, "CONPORT_HTTP_PORT": 3040},
    )
    configured_hits = [
        f
        for f in report.findings
        if f["code"] == "PORT_RESERVED_COLLISION" and "source=configured" in f["evidence"]
    ]
    assert configured_hits
    assert all(f["severity"] == "FAIL" for f in configured_hits)


def test_intra_config_collision():
    catalog = _catalog()
    report = pd.diagnose_ports(
        "/tmp/wt",
        ["conport"],
        catalog,
        configured_ports={"CONPORT_MCP_PORT": 3100, "CONPORT_HTTP_PORT": 3100},
    )
    assert any(f["code"] == "PORT_INTRA_CONFIG_COLLISION" for f in report.findings)
    assert any(c.kind == "intra_config" for c in report.collisions)


def test_cross_service_collision():
    catalog = _catalog()
    report = pd.diagnose_ports(
        "/tmp/same-base-collision-path",
        ["alpha", "beta"],
        catalog,
    )
    codes = {f["code"] for f in report.findings}
    assert "PORT_CROSS_SERVICE_COLLISION" in codes or "PORT_INTRA_CONFIG_COLLISION" in codes


def test_bucket_risk_and_rebind_missing_warnings():
    catalog = _catalog()
    report = pd.diagnose_ports(
        "/tmp/wt",
        ["conport"],
        catalog,
        has_lease_registry=False,
        has_live_rebind=False,
    )
    codes = {f["code"] for f in report.findings}
    assert "PORT_HASH_BUCKET_COLLISION_RISK" in codes
    assert "PORT_REBIND_MISSING" in codes
    risk = next(f for f in report.findings if f["code"] == "PORT_HASH_BUCKET_COLLISION_RISK")
    assert "100 offset buckets" in risk["message"]


def test_ports_listening_check_ownership_unknown():
    findings = pd.ports_listening_check(
        {"CONPORT_MCP_PORT": 3041},
        is_free_fn=lambda port: False,  # not free => listening
    )
    codes = {f["code"] for f in findings}
    assert "PORT_LISTENING" in codes
    assert "PORT_OWNERSHIP_UNKNOWN" in codes
    # Listening must not be treated as ownership PASS
    assert all(f["severity"] != "PASS" for f in findings)


def test_ports_not_listening():
    findings = pd.ports_listening_check(
        {"CONPORT_MCP_PORT": 3041},
        is_free_fn=lambda port: True,
    )
    assert any(f["code"] == "PORT_NOT_LISTENING" for f in findings)
