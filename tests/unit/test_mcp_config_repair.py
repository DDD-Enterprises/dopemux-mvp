"""Unit tests for MCP config repair (TP-DMX-MCP-RUNTIME-003)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from dopemux.mcp import config_repair as cr
from dopemux.mcp import mcp_json as mj


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport", "dope-memory", "task-orchestrator"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
                "requires_env": ["DOPEMUX_WORKSPACE_ID"],
                "management_model": "compose-service",
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
                "management_model": "compose-service",
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "per-repo",
                "transport": "http",
                "url_template": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
                "management_model": "wrapper-singleton",
            },
            "pal": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3003/mcp",
            },
        },
    }


def _render(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"type": spec.get("transport", "http")}
    if "url_template" in spec or "url" in spec:
        entry["url"] = spec.get("url_template") or spec.get("url")
    env_keys = list(spec.get("requires_env") or [])
    if env_keys:
        entry["env"] = {k: f"${{{k}:-}}" for k in env_keys}
    return entry


def _alloc(worktree: str, names: List[str], catalog: Dict[str, Any], *, project_root: str | None = None):
    # Deterministic fake ports for tests
    out = {}
    for name in names:
        spec = catalog["servers"][name]
        if spec.get("port_var"):
            base = int(spec.get("default_port_base") or 3000)
            out[spec["port_var"]] = base + 10
        for extra in spec.get("extra_port_vars") or []:
            out[extra["var"]] = int(extra["base"]) + 10
    return out


def _exports(worktree: str, project_root: str) -> Dict[str, str]:
    return {
        "DOPEMUX_WORKSPACE_ID": worktree,
        "DOPEMUX_WORKSPACE_ROOT": worktree,
        "DOPEMUX_PROJECT_ROOT": project_root,
        "TASK_ORCHESTRATOR_PROJECT_ROOT": project_root,
        "DOPEMUX_INSTANCE_ID": "abcd",
        "DOPE_MEMORY_WORKSPACE_ID": Path(worktree).name,
        "DOPE_MEMORY_INSTANCE_ID": "abcd",
        "WORKSPACE_ID": worktree,
    }


def _plan(repo: Path, **kwargs):
    return cr.plan_repair(
        repo,
        _catalog(),
        dry_run=kwargs.pop("dry_run", True),
        allocate_ports_fn=_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
        global_claude_path=repo / "no-global-claude.json",
        **kwargs,
    )


def test_dry_run_writes_nothing(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    mcp = {
        "mcpServers": {
            "dope-memory": {"type": "sse", "url": "http://localhost:3060/mcp"},
            "custom-svc": {"type": "http", "url": "http://localhost:9999/mcp"},
        }
    }
    mcp_path = repo / ".mcp.json"
    mcp_path.write_text(json.dumps(mcp, indent=2) + "\n")
    before = mcp_path.read_text()

    plan = _plan(repo, dry_run=True)
    assert plan.status == "PLANNED"
    assert plan.dry_run is True
    assert mcp_path.read_text() == before
    assert not (repo / ".envrc.dopemux-mcp").exists()
    assert not (repo / ".claude" / "WORKTREE_MCP_SETUP.md").exists()


def test_apply_repairs_transport_and_preserves_custom(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    mcp = {
        "mcpServers": {
            "conport": {
                "type": "sse",
                "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
            },
            "dope-memory": {"type": "sse", "url": "http://localhost:3060/mcp"},
            "task-orchestrator": {"type": "sse", "url": "http://localhost:7890/mcp"},
            "custom-svc": {"type": "http", "url": "http://localhost:9999/mcp"},
        }
    }
    (repo / ".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n")

    plan = _plan(repo, dry_run=True)
    assert any(c.get("service") == "dope-memory" and c.get("reason") == "TRANSPORT_MISMATCH" for c in plan.planned_changes)
    assert any(c.get("service") == "task-orchestrator" for c in plan.planned_changes)
    assert any(p.get("service") == "custom-svc" for p in plan.preserved_entries)

    plan.dry_run = False
    applied = cr.apply_repair(plan)
    assert applied.status == "APPLIED"

    data = json.loads((repo / ".mcp.json").read_text())
    assert data["mcpServers"]["dope-memory"]["type"] == "http"
    assert data["mcpServers"]["task-orchestrator"]["type"] == "http"
    assert data["mcpServers"]["conport"]["type"] == "sse"
    assert data["mcpServers"]["custom-svc"]["url"] == "http://localhost:9999/mcp"
    assert (repo / ".envrc.dopemux-mcp").is_file()
    assert (repo / ".claude" / "WORKTREE_MCP_SETUP.md").is_file()


def test_noop_when_already_valid(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    servers = {}
    for name in ("conport", "dope-memory", "task-orchestrator"):
        servers[name] = _render(name, _catalog()["servers"][name])
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n")

    # Write matching envrc
    env_map = _exports(str(repo), str(repo))
    env_map.update({k: str(v) for k, v in _alloc(str(repo), list(servers), _catalog(), project_root=str(repo)).items()})
    lines = [f"export {k}={v}" for k, v in env_map.items()]
    (repo / ".envrc.dopemux-mcp").write_text("\n".join(lines) + "\n")

    # Pre-write matching agent bootstrap
    from dopemux.mcp.agent_bootstrap import apply_agent_bootstrap, plan_agent_bootstrap

    ap = plan_agent_bootstrap(repo)
    apply_agent_bootstrap(ap)

    plan = _plan(repo, dry_run=True)
    assert plan.status == "NOOP"
    assert plan.planned_changes == []


def test_missing_mcp_json_creates(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    plan = _plan(repo, dry_run=False)
    plan.dry_run = False
    applied = cr.apply_repair(plan)
    assert applied.status == "APPLIED"
    data = json.loads((repo / ".mcp.json").read_text())
    assert "conport" in data["mcpServers"]
    assert "dope-memory" in data["mcpServers"]


def test_malformed_mcp_json_blocks(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".mcp.json").write_text("{not-json\n")
    plan = _plan(repo)
    assert plan.status == "BLOCKED"
    assert any(b.get("code") == "MCP_JSON_PARSE_ERROR" for b in plan.blocking_findings)


def test_non_localhost_url_not_modified(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    mcp = {
        "mcpServers": {
            "dope-memory": {
                "type": "sse",
                "url": "https://remote.example.com/mcp",
            }
        }
    }
    (repo / ".mcp.json").write_text(json.dumps(mcp) + "\n")
    plan = _plan(repo, dry_run=False)
    plan.dry_run = False
    cr.apply_repair(plan)
    data = json.loads((repo / ".mcp.json").read_text())
    assert data["mcpServers"]["dope-memory"]["url"] == "https://remote.example.com/mcp"
    # type may still be repaired
    assert data["mcpServers"]["dope-memory"]["type"] == "http"


def test_secret_like_envrc_blocks_apply(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"conport": _render("conport", _catalog()["servers"]["conport"])}}) + "\n"
    )
    (repo / ".envrc.dopemux-mcp").write_text(
        "export DOPEMUX_WORKSPACE_ID=/x\nexport OPENAI_API_KEY=sk-secret\n"
    )
    plan = _plan(repo, dry_run=True)
    assert plan.status == "BLOCKED"
    assert any(b.get("code") == "ENVRC_SECRET_LIKE_UNCERTAIN" for b in plan.blocking_findings)
    assert any(w.get("code") == "ENVRC_SECRET_LIKE_VALUE_REDACTED" for w in plan.warnings)
    # dry-run must not write
    assert "sk-secret" not in plan.to_json()


def test_no_global_mutation(tmp_path: Path, monkeypatch):
    repo = tmp_path / "proj"
    repo.mkdir()
    global_path = tmp_path / "fake-claude.json"
    global_path.write_text(json.dumps({"mcpServers": {"conport": {"type": "sse"}}}) + "\n")
    before = global_path.read_text()

    plan = _plan(repo)
    # force global path via plan_repair kw
    plan = cr.plan_repair(
        repo,
        _catalog(),
        dry_run=False,
        allocate_ports_fn=_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
        global_claude_path=global_path,
    )
    plan.dry_run = False
    cr.apply_repair(plan)
    assert global_path.read_text() == before
    assert any(w.get("code") == "GLOBAL_CONFIG_NOT_MODIFIED" for w in plan.warnings)


def test_port_limitation_warnings(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    plan = _plan(repo)
    codes = {w.get("code") for w in plan.warnings}
    assert "PORT_HASH_BUCKET_COLLISION_RISK" in codes
    assert "PORT_REBIND_MISSING" in codes


def test_plan_does_not_persist_leases_until_apply(tmp_path: Path):
    """Planning must not write leases even when dry_run=False (apply path)."""
    repo = tmp_path / "proj"
    repo.mkdir()
    calls: list[dict] = []

    def tracking_alloc(
        worktree: str,
        names: List[str],
        catalog: Dict[str, Any],
        *,
        project_root: str | None = None,
        persist: bool = True,
        dry_run: bool = False,
        existing_envrc: Dict[str, str] | None = None,
        source: str = "",
        **_kwargs: Any,
    ):
        calls.append({"persist": persist, "dry_run": dry_run, "source": source})
        return _alloc(worktree, names, catalog, project_root=project_root)

    plan = cr.plan_repair(
        repo,
        _catalog(),
        dry_run=False,  # simulate --apply planning
        allocate_ports_fn=tracking_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
        global_claude_path=repo / "no-global.json",
    )
    assert plan.status in {"PLANNED", "NOOP"}
    # Plan-time allocation must never persist
    assert calls, "allocator should have been invoked during plan"
    assert all(c["persist"] is False or c["dry_run"] is True for c in calls)

    plan.dry_run = False
    plan_calls_before_apply = len(calls)
    applied = cr.apply_repair(plan)
    assert applied.status == "APPLIED"
    # Apply should re-invoke allocator with persist enabled
    post = calls[plan_calls_before_apply:]
    assert post, "allocator should re-run on apply for lease persistence"
    assert any(c["persist"] is True and c["dry_run"] is False for c in post)


def test_is_catalog_owned():
    cat = _catalog()
    assert mj.is_catalog_owned("conport", cat) is True
    assert mj.is_catalog_owned("pal", cat) is False
    assert mj.is_catalog_owned("custom", cat) is False


def test_json_schema_shape(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    plan = _plan(repo)
    d = plan.to_dict()
    assert d["schema_version"] == "1.0"
    assert d["operation"] == "repair-config"
    assert "project_identity" in d
    assert "planned_changes" in d
    assert "next_actions" in d
    assert "dopemux mcp start" in d["next_actions"]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (None, True),
        ("", True),
        ("http://localhost:3005/sse", True),
        ("http://127.0.0.1:7890/mcp", True),
        ("https://remote.example/sse", False),
        ("http://user:secret@localhost:3005/sse", False),
        # A template is repairable only in the exact shape dopemux renders. The
        # variable's value is unknown at repair time (PORT=3005@remote.example
        # expands to host remote.example), so a generic or unknown port variable
        # never proves the endpoint local.
        ("http://localhost:${PORT:-3005}/sse", False),
        ("http://localhost:${CONPORT_PORT:-3005}/sse", False),
        ("http://127.0.0.1:${PORT}/mcp", False),
        # A host/userinfo placeholder is operator-selected whatever its default.
        ("http://${CONPORT_HOST:-localhost}:3005/sse", False),
        ("http://${HOST:-127.0.0.1}:3005/sse", False),
        ("http://${USER:-x}@localhost:3005/sse", False),
        ("http://[${HOST:-::1}]:3005/sse", False),
        ("http://local${SUFFIX:-host}:3005/sse", False),
        ("https://remote.example:${REMOTE_PORT:-443}/sse", False),
        ("http://user:${PASSWORD}@localhost:3005/sse", False),
        ("http://${HOST}:3005/sse", False),
        ("${CONPORT_URL}", False),
        ("http://${REMOTE_HOST:-remote.example}:3005/sse", False),
        ("http://${USER_INFO:-me@}localhost:3005/sse", False),
        ("http://localhost:${PORT-3005}/sse", False),
        ("http://${HOST-localhost}:3005/sse", False),
        ("http://localhost:${A${B}}/sse", False),
        ("http://localhost:${UNCLOSED/sse", False),
        # A delimiter inside a host/userinfo placeholder default must not end
        # the authority.
        ("http://${HOST:-localhost/path}/sse", False),
        ("http://${HOST:-localhost?x}/sse", False),
        ("http://${HOST:-localhost#x}/sse", False),
        ("http://${HOST:-user@localhost}:3005/sse", False),
        ("http://${HOST:-localhost:3005}/sse", False),
        ("http://${U:-a/b}@localhost:3005/sse", False),
        ("${BASE:-http://localhost:3005}/sse", False),
        # A placeholder supplying the scheme or the base fails closed; a later
        # literal ``://`` in the path or query is never the authority.
        ("${BASE:-http://localhost:3005}/sse?next=http://remote.example", False),
        ("${SCHEME:-http}://localhost:3005/sse", False),
        ("http${X:-}://localhost:3005/sse", False),
        ("http:${X:-}//localhost:3005/sse", False),
        ("http://localhost:3005/sse?next=http://remote.example", True),
        # Generic port variables: an unknown value, so not provably ours (cycle 4).
        ("http://localhost:${PORT:-3005}/sse?u=ws://x", False),
        ("http://localhost:${PORT:-3005}/${P:-a/b}", False),
        # No dopemux port variable at all: operator-authored.
        ("http://localhost:3005/sse?x=${Q:-a/b}", False),
        # Every URL the catalog itself renders must stay repairable.
        ("http://localhost:${CONPORT_MCP_PORT:-3005}/sse", True),
        ("http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp", True),
        ("http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp", True),
        ("http://localhost:${CONPORT_MCP_PORT}/sse", True),
        ("https://127.0.0.1:${DOPE_MEMORY_PORT:-3020}/mcp", True),
        ("http://localhost:${CONPORT_MCP_PORT:-3005}/sse?x=1", True),
        # Anything else shaped like a dopemux template is operator-authored.
        ("http://localhost:${CONPORT_MCP_PORT:-abc}/sse", False),
        ("http://localhost:${CONPORT_MCP_PORT:-3005}/${P:-x}", False),
        ("http://localhost:${CONPORT_MCP_PORT:-3005}${X:-}/sse", False),
        ("http://remote.example:${CONPORT_MCP_PORT:-3005}/sse", False),
        ("http://user@localhost:${CONPORT_MCP_PORT:-3005}/sse", False),
        ("http://localhost:${CONPORT_MCP_PORT:-3005}@remote.example/sse", False),
    ],
)
def test_url_is_repairable_templated_and_literal(url: Any, expected: bool) -> None:
    assert mj._url_is_repairable(url) is expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:3005/sse", False),
        ("http://${HOST:-localhost}:3005/sse", True),
        ("http://${HOST:-localhost/path}/sse", True),
        ("http://${HOST:-localhost?x}/sse", True),
        ("http://${HOST:-localhost#x}/sse", True),
        ("http://${HOST:-user@localhost}:3005/sse", True),
        ("http://${HOST:-localhost:3005}/sse", True),
        ("http://${U:-a/b}@localhost:3005/sse", True),
        ("${BASE:-http://localhost:3005}/sse", True),
        ("${BASE:-http://localhost:3005}/sse?next=http://remote.example", True),
        ("${SCHEME:-http}://localhost:3005/sse", True),
        ("http${X:-}://localhost:3005/sse", True),
        ("http:${X:-}//localhost:3005/sse", True),
        ("http://localhost:3005/sse?next=http://remote.example", False),
        ("http://localhost:${PORT:-3005}/sse?u=ws://x", False),
        ("http://localhost:${PORT:-3005}/${P:-a/b}", False),
        ("http://localhost:3005/sse?x=${Q:-a/b}", False),
        ("http://[${HOST:-::1}]:3005/sse", True),
    ],
)
def test_placeholder_in_userinfo_or_host_masks_before_splitting(
    url: str, expected: bool
) -> None:
    assert mj._placeholder_in_userinfo_or_host(url) is expected


def test_catalog_port_vars_from_default_catalog() -> None:
    from dopemux.mcp import fleet_catalog

    repo_root = Path(__file__).resolve().parents[2]
    catalog = fleet_catalog.load_root_catalog(repo_root)
    assert mj._catalog_port_vars(catalog) >= {
        "CONPORT_MCP_PORT",
        "DOPE_MEMORY_PORT",
        "TASK_ORCHESTRATOR_HTTP_PORT",
    }


def test_catalog_port_vars_reads_names_only_from_url_values() -> None:
    catalog = {
        "servers": {
            "a": {"url_template": "http://localhost:${A_PORT:-1}/x", "port_var": "B"},
            "b": {"url": "http://localhost:${C_PORT}/y"},
            "c": {"transport": "sse"},
        }
    }
    assert mj._catalog_port_vars(catalog) == {"A_PORT", "C_PORT"}


def test_self_rendered_template_rejects_generic_port_variable() -> None:
    url = "http://localhost:${PORT:-3005}/sse"
    assert mj._self_rendered_template(url, mj._DOPEMUX_PORT_VARS) is False
    assert mj._self_rendered_template(url, frozenset({"PORT"})) is True
    ours = "http://localhost:${CONPORT_MCP_PORT:-3005}/sse"
    assert mj._self_rendered_template(ours, mj._DOPEMUX_PORT_VARS) is True


def _launcher_catalog() -> Dict[str, Any]:
    catalog = _catalog()
    catalog["servers"]["conport"]["client"] = "launcher"
    return catalog


def _launcher_entry(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "stdio", "command": "dopemux", "args": ["mcp", "launch", name]}


def test_planner_preserves_generic_port_template_and_repairs_dopemux_template() -> None:
    catalog = _launcher_catalog()
    operator = {"type": "sse", "url": "http://localhost:${PORT:-3005}/sse"}
    merged, planned, preserved = mj.plan_mcp_json_repairs(
        {"conport": operator},
        catalog,
        mcp_json_path="x/.mcp.json",
        include_defaults=False,
        render_fn=_launcher_entry,
    )
    assert merged["conport"] == operator
    assert planned == []
    assert preserved == [
        {
            "path": "x/.mcp.json",
            "service": "conport",
            "reason": (
                "operator URL preserved "
                "(not a literal local URL and not a dopemux-rendered template)"
            ),
        }
    ]

    rendered = {
        "type": "sse",
        "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
    }
    merged, planned, preserved = mj.plan_mcp_json_repairs(
        {"conport": rendered},
        catalog,
        mcp_json_path="x/.mcp.json",
        include_defaults=False,
        render_fn=_launcher_entry,
    )
    assert merged["conport"]["type"] == "stdio"
    assert "url" not in merged["conport"]
    assert [c["service"] for c in planned] == ["conport"]
    assert preserved == []


def test_templated_remote_launcher_url_is_preserved_not_replaced(tmp_path: Path):
    repo = tmp_path / "proj"
    repo.mkdir()
    remote = "https://remote.example:${REMOTE_PORT:-443}/sse"
    mcp = {"mcpServers": {"conport": {"type": "sse", "url": remote}}}
    (repo / ".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n")

    plan = _plan(repo, dry_run=True)

    assert not any(
        c.get("service") == "conport" and c.get("reason") == "URL_MISMATCH"
        for c in plan.planned_changes
    )
    reason = (
        "operator URL preserved "
        "(not a literal local URL and not a dopemux-rendered template)"
    )
    assert any(
        p.get("service") == "conport" and p.get("reason") == reason
        for p in plan.preserved_entries
    )
