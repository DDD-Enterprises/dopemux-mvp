"""Registry: validation, fail-closed defaults, file loading."""

from __future__ import annotations

import textwrap
from pathlib import Path

from dcp_facade import registry as REG


def _valid(project_id="p", enabled=True):
    return {
        "project_id": project_id,
        "workspace_path": "/abs/ws",
        "enabled": enabled,
        "identity": {"project": "proj", "owner": "owner"},
        "service_profiles": {"conport": {"workspace_id": "w"}},
    }


def test_parse_valid_project():
    reg = REG.parse_registry({"projects": [_valid()], "approved_roots": ["/abs"]})
    assert "p" in reg.projects
    p = reg.projects["p"]
    assert p.enabled is True
    assert p.identity_project == "proj"
    assert p.identity_owner == "owner"
    assert reg.approved_roots == ["/abs"]
    assert p.configured_capabilities()["conport"] is True
    assert p.configured_capabilities()["dope_memory"] is False


def test_enabled_defaults_false():
    raw = _valid()
    del raw["enabled"]
    reg = REG.parse_registry({"projects": [raw]})
    assert reg.projects["p"].enabled is False


def test_malformed_entries_dropped_failclosed():
    bad = [
        {"workspace_path": "/x", "identity": {"project": "a"}},          # no project_id
        {"project_id": "b", "identity": {"project": "a"}},                # no workspace_path
        {"project_id": "c", "workspace_path": "/x"},                      # no identity
        {"project_id": "d", "workspace_path": "/x", "identity": {}},      # no identity.project
        "not-a-mapping",
    ]
    reg = REG.parse_registry({"projects": bad})
    assert reg.projects == {}
    assert len(reg.warnings) >= len(bad)


def test_duplicate_project_id_dropped():
    reg = REG.parse_registry({"projects": [_valid("dup"), _valid("dup")]})
    assert list(reg.projects) == ["dup"]
    assert any("duplicate" in w for w in reg.warnings)


def test_enabled_projects_filter():
    reg = REG.parse_registry({"projects": [_valid("on", True), _valid("off", False)]})
    ids = {p.project_id for p in reg.enabled_projects()}
    assert ids == {"on"}


def test_load_missing_file_returns_empty(tmp_path: Path):
    reg = REG.load_registry(str(tmp_path / "nope.yaml"))
    assert reg.projects == {}
    assert any("not found" in w for w in reg.warnings)


def test_load_from_yaml_file(tmp_path: Path):
    f = tmp_path / "reg.yaml"
    f.write_text(
        textwrap.dedent(
            """
            approved_roots:
              - /abs
            projects:
              - project_id: p
                workspace_path: /abs/ws
                enabled: true
                identity:
                  project: proj
            """
        ),
        encoding="utf-8",
    )
    reg = REG.load_registry(str(f))
    assert "p" in reg.projects
    assert reg.projects["p"].identity_owner is None
