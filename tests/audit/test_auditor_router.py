"""Tests for scripts/audit/auditor_router.py and route_schema.py."""
from __future__ import annotations

from pathlib import Path

import jsonschema
import pytest

from scripts.audit.auditor_router import (
    _CLINK_CONF_DIR,
    _DEFAULT_ROUTE_NAMES,
    default_routes,
    load_route_from_clink_config,
    probe_capability,
    select_route,
)
from scripts.audit.route_schema import FORBIDDEN_CLI_NAMES, AuditRoute

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "audit" / "audit_route.schema.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _always_found(cmd: str) -> str:
    return f"/usr/bin/{cmd}"


def _never_found(cmd: str) -> None:
    return None


# ---------------------------------------------------------------------------
# AuditRoute / route_schema
# ---------------------------------------------------------------------------

class TestAuditRoute:
    def test_valid_route_constructs(self) -> None:
        route = AuditRoute(cli_name="claude-audit", command="claude", priority=0)
        assert route.cli_name == "claude-audit"
        assert route.command == "claude"
        assert route.priority == 0
        assert route.role == "codereviewer"

    def test_forbidden_cli_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Forbidden auditor CLI"):
            AuditRoute(cli_name="codex", command="codex")

    def test_forbidden_cli_name_codex_audit_raises(self) -> None:
        with pytest.raises(ValueError, match="Forbidden auditor CLI"):
            AuditRoute(cli_name="codex-audit", command="codex")

    def test_empty_cli_name_raises(self) -> None:
        with pytest.raises(ValueError, match="cli_name must be non-empty"):
            AuditRoute(cli_name="", command="claude")

    def test_empty_command_raises(self) -> None:
        with pytest.raises(ValueError, match="command must be non-empty"):
            AuditRoute(cli_name="claude-audit", command="")

    def test_negative_priority_raises(self) -> None:
        with pytest.raises(ValueError, match="priority must be"):
            AuditRoute(cli_name="claude-audit", command="claude", priority=-1)

    def test_forbidden_cli_names_constant(self) -> None:
        assert "codex" in FORBIDDEN_CLI_NAMES
        assert "codex-audit" in FORBIDDEN_CLI_NAMES
        assert "claude-audit" not in FORBIDDEN_CLI_NAMES
        assert "gemini-audit" not in FORBIDDEN_CLI_NAMES


# ---------------------------------------------------------------------------
# load_route_from_clink_config
# ---------------------------------------------------------------------------

class TestLoadRouteFromClinkConfig:
    def test_load_claude_audit(self) -> None:
        path = _CLINK_CONF_DIR / "claude-audit.json"
        route = load_route_from_clink_config(path, priority=0)
        assert route.cli_name == "claude-audit"
        assert route.command == "claude"
        assert route.priority == 0
        assert "--model" in route.additional_args

    def test_load_gemini_audit(self) -> None:
        path = _CLINK_CONF_DIR / "gemini-audit.json"
        route = load_route_from_clink_config(path, priority=1)
        assert route.cli_name == "gemini-audit"
        assert route.command == "gemini"
        assert route.priority == 1

    def test_load_codex_config_raises(self) -> None:
        path = _CLINK_CONF_DIR / "codex.json"
        with pytest.raises(ValueError, match="Forbidden auditor CLI"):
            load_route_from_clink_config(path)

    def test_load_preserves_custom_role(self) -> None:
        path = _CLINK_CONF_DIR / "claude-audit.json"
        route = load_route_from_clink_config(path, role="codereviewer")
        assert route.role == "codereviewer"


# ---------------------------------------------------------------------------
# probe_capability
# ---------------------------------------------------------------------------

class TestProbeCapability:
    def test_returns_true_when_command_found(self) -> None:
        route = AuditRoute(cli_name="claude-audit", command="claude", priority=0)
        assert probe_capability(route, which_fn=_always_found) is True

    def test_returns_false_when_command_not_found(self) -> None:
        route = AuditRoute(cli_name="claude-audit", command="claude", priority=0)
        assert probe_capability(route, which_fn=_never_found) is False

    def test_gemini_route_probed_correctly(self) -> None:
        route = AuditRoute(cli_name="gemini-audit", command="gemini", priority=1)
        assert probe_capability(route, which_fn=_always_found) is True
        assert probe_capability(route, which_fn=_never_found) is False


# ---------------------------------------------------------------------------
# select_route
# ---------------------------------------------------------------------------

class TestSelectRoute:
    def _routes(self) -> list[AuditRoute]:
        return [
            AuditRoute(cli_name="claude-audit", command="claude", priority=0),
            AuditRoute(cli_name="gemini-audit", command="gemini", priority=1),
        ]

    def test_returns_primary_when_both_available(self) -> None:
        route = select_route(self._routes(), which_fn=_always_found)
        assert route is not None
        assert route.cli_name == "claude-audit"

    def test_falls_back_to_secondary_when_primary_unavailable(self) -> None:
        def which_fn(cmd: str):
            return None if cmd == "claude" else f"/usr/bin/{cmd}"

        route = select_route(self._routes(), which_fn=which_fn)
        assert route is not None
        assert route.cli_name == "gemini-audit"

    def test_returns_none_when_all_unavailable(self) -> None:
        route = select_route(self._routes(), which_fn=_never_found)
        assert route is None

    def test_empty_routes_returns_none(self) -> None:
        assert select_route([], which_fn=_always_found) is None

    def test_unsorted_input_still_returns_highest_priority(self) -> None:
        routes = [
            AuditRoute(cli_name="gemini-audit", command="gemini", priority=1),
            AuditRoute(cli_name="claude-audit", command="claude", priority=0),
        ]
        route = select_route(routes, which_fn=_always_found)
        assert route is not None
        assert route.cli_name == "claude-audit"


# ---------------------------------------------------------------------------
# default_routes
# ---------------------------------------------------------------------------

class TestDefaultRoutes:
    def test_returns_two_routes(self) -> None:
        routes = default_routes()
        assert len(routes) == 2

    def test_claude_audit_has_priority_zero(self) -> None:
        routes = default_routes()
        assert routes[0].cli_name == "claude-audit"
        assert routes[0].priority == 0

    def test_gemini_audit_has_priority_one(self) -> None:
        routes = default_routes()
        assert routes[1].cli_name == "gemini-audit"
        assert routes[1].priority == 1

    def test_no_codex_in_default_routes(self) -> None:
        routes = default_routes()
        for route in routes:
            assert route.cli_name not in FORBIDDEN_CLI_NAMES

    def test_all_routes_valid_against_schema(self) -> None:
        import json

        schema = json.loads(SCHEMA_PATH.read_text())
        routes = default_routes()
        for route in routes:
            doc = {
                "cli_name": route.cli_name,
                "command": route.command,
                "priority": route.priority,
                "additional_args": route.additional_args,
                "env": route.env,
                "role": route.role,
            }
            jsonschema.validate(doc, schema)

    def test_missing_conf_dir_returns_empty(self, tmp_path: Path) -> None:
        routes = default_routes(conf_dir=tmp_path / "nonexistent")
        assert routes == []

    def test_partial_conf_dir_returns_available_routes(self, tmp_path: Path) -> None:
        import json

        (tmp_path / "claude-audit.json").write_text(
            json.dumps(
                {
                    "name": "claude-audit",
                    "runner": "claude",
                    "command": "claude",
                    "additional_args": [],
                    "env": {},
                    "roles": {"codereviewer": {"prompt_path": "x", "role_args": []}},
                }
            )
        )
        routes = default_routes(conf_dir=tmp_path)
        assert len(routes) == 1
        assert routes[0].cli_name == "claude-audit"

    def test_load_route_raises_when_role_not_in_config(self, tmp_path: Path) -> None:
        import json

        cfg = tmp_path / "claude-audit.json"
        cfg.write_text(
            json.dumps(
                {
                    "name": "claude-audit",
                    "command": "claude",
                    "additional_args": [],
                    "env": {},
                    "roles": {},
                }
            )
        )
        with pytest.raises(KeyError, match="codereviewer"):
            load_route_from_clink_config(cfg, role="codereviewer")
