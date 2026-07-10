"""Registry v2: schema contract + fail-closed parse tests (TP-DCP-MCP-RO-0010).

Mirrors tests/test_registry.py's fail-closed style for the v2 shape
(target_id, 9-family allowlist, v1->v2 migration guard, deterministic
content-hash generation). No network/file-write primitives are exercised
here; fixtures are static YAML under tests/fixtures/registry_v2/.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import jsonschema
import pytest
import yaml

from dcp_facade import registry_v2 as REG2

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "registry_v2.schema.json"
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "registry_v2"


def _load_yaml(name: str):
    return yaml.safe_load((_FIXTURES / name).read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Module constants (family allowlist + static policy table)
# ---------------------------------------------------------------------------


def test_allowed_service_families_are_exactly_the_nine_adr_families():
    assert REG2.ALLOWED_SERVICE_FAMILIES == (
        "conport",
        "dope_memory",
        "to_compose_rest",
        "to_mcp_wrapper",
        "dope_context",
        "serena",
        "pal",
        "docker_mcp_gateway",
        "desktop_commander",
    )


def test_bare_task_orchestrator_not_in_allowlist():
    assert "task-orchestrator" not in REG2.ALLOWED_SERVICE_FAMILIES


def test_family_policy_table_covers_every_allowed_family():
    for family in REG2.ALLOWED_SERVICE_FAMILIES:
        assert family in REG2.FAMILY_POLICY_TABLE
        resolution_class, chatgpt_posture = REG2.FAMILY_POLICY_TABLE[family]
        assert isinstance(resolution_class, str) and resolution_class
        assert isinstance(chatgpt_posture, str) and chatgpt_posture


def test_family_policy_table_matches_adr_0009_posture_for_to_mcp_wrapper():
    # to_mcp_wrapper is explicitly blocked in ADR-0009 (host singleton, single active project).
    resolution_class, chatgpt_posture = REG2.FAMILY_POLICY_TABLE["to_mcp_wrapper"]
    assert resolution_class == "host_singleton_single_active_project"
    assert chatgpt_posture == "blocked"


def test_default_binding_mode_is_primary_checkout_only():
    assert REG2.DEFAULT_BINDING_MODE == "PRIMARY_CHECKOUT_ONLY"


# ---------------------------------------------------------------------------
# JSON Schema contract
# ---------------------------------------------------------------------------


def test_schema_is_draft7_and_self_valid():
    jsonschema.Draft7Validator.check_schema(_schema())


def test_schema_accepts_valid_fixture():
    jsonschema.Draft7Validator(_schema()).validate(_load_yaml("valid.yaml"))


def test_schema_accepts_disabled_target_fixture():
    jsonschema.Draft7Validator(_schema()).validate(_load_yaml("disabled_target.yaml"))


@pytest.mark.parametrize(
    "fixture_name",
    [
        "invalid_bare_task_orchestrator.yaml",
        "invalid_unknown_family.yaml",
        "invalid_missing_identity.yaml",
        "invalid_v1_project_id_doc.yaml",
    ],
)
def test_schema_rejects_structural_fixtures(fixture_name):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(_schema()).validate(_load_yaml(fixture_name))


# ---------------------------------------------------------------------------
# Fail-closed parsing — registry-level
# ---------------------------------------------------------------------------


def test_parse_valid_fixture_yields_enabled_target():
    reg = REG2.parse_registry_v2(_load_yaml("valid.yaml"))
    assert "dopemux-main" in reg.targets
    target = reg.targets["dopemux-main"]
    assert target.enabled is True
    assert target.binding_mode == "PRIMARY_CHECKOUT_ONLY"
    assert target.identity_project == "dopemux-mvp"
    assert target.identity_owner == "hu3mann"
    assert reg.approved_roots == ["/abs/approved/root"]
    assert target.service_policies["conport"].configured is True
    assert target.service_policies["pal"].configured is False


def test_bare_task_orchestrator_target_rejected_with_warning():
    reg = REG2.parse_registry_v2(_load_yaml("invalid_bare_task_orchestrator.yaml"))
    assert reg.targets == {}
    assert any("task-orchestrator" in w for w in reg.warnings)


def test_unknown_family_target_rejected_with_warning():
    reg = REG2.parse_registry_v2(_load_yaml("invalid_unknown_family.yaml"))
    assert reg.targets == {}
    assert any("unknown" in w.lower() and "family" in w.lower() for w in reg.warnings)


def test_missing_identity_target_rejected_with_warning():
    reg = REG2.parse_registry_v2(_load_yaml("invalid_missing_identity.yaml"))
    assert reg.targets == {}
    assert any("identity" in w.lower() for w in reg.warnings)


def test_duplicate_target_id_dropped():
    reg = REG2.parse_registry_v2(_load_yaml("invalid_duplicate_target_id.yaml"))
    assert list(reg.targets) == ["dup"]
    assert any("duplicate" in w.lower() for w in reg.warnings)


def test_disabled_target_parses_but_is_not_enabled():
    reg = REG2.parse_registry_v2(_load_yaml("disabled_target.yaml"))
    assert "dopemux-disabled" in reg.targets
    assert reg.targets["dopemux-disabled"].enabled is False
    assert reg.enabled_targets() == []


def test_enabled_defaults_false_when_omitted():
    doc = {
        "targets": [
            {
                "target_id": "p",
                "workspace_path": "/abs/ws",
                "identity": {"project": "proj"},
            }
        ]
    }
    reg = REG2.parse_registry_v2(doc)
    assert reg.targets["p"].enabled is False


def test_v1_project_id_doc_fails_closed_with_actionable_warning():
    reg = REG2.parse_registry_v2(_load_yaml("invalid_v1_project_id_doc.yaml"))
    assert reg.targets == {}
    assert any(
        ("v1" in w.lower() or "migrat" in w.lower()) and "target_id" in w
        for w in reg.warnings
    )


def test_v1_doc_is_not_silently_coerced_into_targets():
    # A v1 doc that ALSO happens to have "projects" but no "targets" key must
    # never be interpreted as an (accidentally empty) v2 doc with 0 targets
    # that silently "succeeds" — it must be flagged, not just quietly empty.
    reg = REG2.parse_registry_v2(_load_yaml("invalid_v1_project_id_doc.yaml"))
    assert len(reg.warnings) >= 1


def test_malformed_entries_dropped_failclosed():
    bad = [
        {"workspace_path": "/x", "identity": {"project": "a"}},  # no target_id
        {"target_id": "b", "identity": {"project": "a"}},  # no workspace_path
        {"target_id": "c", "workspace_path": "/x"},  # no identity
        {"target_id": "d", "workspace_path": "/x", "identity": {}},  # no identity.project
        {"target_id": "e", "workspace_path": "/x", "identity": {"project": "a"}, "enabled": "yes"},  # bad type
        {"target_id": "f", "workspace_path": "/x", "identity": {"project": "a"}, "binding_mode": "ANYTHING"},
        "not-a-mapping",
    ]
    reg = REG2.parse_registry_v2({"targets": bad})
    assert reg.targets == {}
    assert len(reg.warnings) >= len(bad)


def test_root_not_a_mapping_treated_as_empty():
    reg = REG2.parse_registry_v2(["not", "a", "mapping"])
    assert reg.targets == {}
    assert reg.warnings


def test_approved_roots_non_list_ignored_with_warning():
    reg = REG2.parse_registry_v2({"approved_roots": "not-a-list", "targets": []})
    assert reg.approved_roots == []
    assert any("approved_roots" in w for w in reg.warnings)


# ---------------------------------------------------------------------------
# Deterministic generation id
# ---------------------------------------------------------------------------


def test_generation_is_deterministic_content_hash():
    doc = _load_yaml("valid.yaml")
    reg1 = REG2.parse_registry_v2(doc)
    reg2 = REG2.parse_registry_v2(doc)
    assert reg1.generation == reg2.generation
    assert reg1.generation != ""

    doc2 = _load_yaml("disabled_target.yaml")
    reg3 = REG2.parse_registry_v2(doc2)
    assert reg3.generation != reg1.generation


def test_generation_has_no_timestamp_or_random_dependency():
    doc = _load_yaml("valid.yaml")
    reg_a = REG2.parse_registry_v2(doc)
    time.sleep(0.01)
    reg_b = REG2.parse_registry_v2(doc)
    assert reg_a.generation == reg_b.generation


# ---------------------------------------------------------------------------
# load_registry_v2 (file IO — read-only)
# ---------------------------------------------------------------------------


def test_load_missing_file_returns_empty(tmp_path: Path):
    reg = REG2.load_registry_v2(str(tmp_path / "nope.yaml"))
    assert reg.targets == {}
    assert any("not found" in w for w in reg.warnings)


def test_load_from_yaml_file(tmp_path: Path):
    f = tmp_path / "reg.yaml"
    f.write_text((_FIXTURES / "valid.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    reg = REG2.load_registry_v2(str(f))
    assert "dopemux-main" in reg.targets
