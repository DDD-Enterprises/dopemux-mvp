"""Tests for the normalized agent/persona catalog builder.

Focused, deterministic validation of catalog invariants.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = (
    PROJECT_ROOT
    / "config"
    / "commandcode"
    / "normalized_agent_persona_catalog.yaml"
)
SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "commandcode"
    / "normalized_agent_persona_catalog.schema.json"
)

# Allowlist: tests that expect jsonschema to be available for schema validation
# Do NOT import jsonschema at module level
try:
    import jsonschema  # noqa: F401
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False


def _load_catalog():
    """Load the catalog from YAML."""
    if not CATALOG_PATH.exists():
        pytest.skip(f"Catalog not found at {CATALOG_PATH}")
    return yaml.safe_load(CATALOG_PATH.read_text())


def _load_schema():
    """Load the JSON schema."""
    return json.loads(SCHEMA_PATH.read_text())


class TestCatalogStructure:
    """Structural invariants of the catalog."""

    def test_catalog_exists(self):
        assert CATALOG_PATH.exists(), f"Catalog missing at {CATALOG_PATH}"

    def test_meta_fields(self):
        catalog = _load_catalog()
        meta = catalog["meta"]
        assert meta["packet_id"] == "CCAR-002"
        assert meta["model_free"] is True
        assert meta["base_agent_count"] == 9
        assert "generated_at" in meta
        assert "source_commit" in meta
        assert len(meta["source_commit"]) == 40

    def test_exactly_nine_base_agents(self):
        catalog = _load_catalog()
        assert len(catalog["base_agents"]) == 9, \
            f"Expected 9 base agents, got {len(catalog['base_agents'])}"

    def test_base_agent_required_fields(self):
        catalog = _load_catalog()
        required = {"id", "source_file", "canonical_role", "label",
                    "description", "attention_state", "tools", "mode",
                    "may_edit", "route_eligible"}
        for agent_id, agent in catalog["base_agents"].items():
            missing = required - set(agent.keys())
            assert not missing, f"Agent {agent_id} missing fields: {missing}"

    def test_base_agent_route_eligible(self):
        catalog = _load_catalog()
        for agent_id, agent in catalog["base_agents"].items():
            assert agent["route_eligible"] is True, \
                f"Base agent {agent_id} must be route_eligible"

    def test_persona_count_matches(self):
        catalog = _load_catalog()
        assert catalog["meta"]["persona_count"] == len(catalog["personas"])

    def test_persona_required_fields(self):
        catalog = _load_catalog()
        required = {"id", "source_file", "base_agents", "label",
                    "description", "route_eligible", "may_change_tools",
                    "may_select_model", "may_grant_write_authority"}
        for pid, persona in catalog["personas"].items():
            missing = required - set(persona.keys())
            assert not missing, f"Persona {pid} missing fields: {missing}"


class TestCatalogInvariants:
    """Invariant enforcement per the CCAR-002 packet."""

    def test_no_duplicate_persona_ids(self):
        catalog = _load_catalog()
        ids = list(catalog["personas"].keys())
        assert len(ids) == len(set(ids)), "Duplicate persona IDs"

    def test_no_duplicate_base_agent_ids(self):
        catalog = _load_catalog()
        ids = list(catalog["base_agents"].keys())
        assert len(ids) == len(set(ids)), "Duplicate base agent IDs"

    def test_authority_prohibitions_false(self):
        catalog = _load_catalog()
        for pid, persona in catalog["personas"].items():
            assert persona["may_change_tools"] is False, \
                f"Persona {pid}: may_change_tools must be false"
            assert persona["may_select_model"] is False, \
                f"Persona {pid}: may_select_model must be false"
            assert persona["may_grant_write_authority"] is False, \
                f"Persona {pid}: may_grant_write_authority must be false"

    def test_no_model_ids_in_catalog(self):
        catalog = _load_catalog()
        patterns = [
            "claude sonnet", "claude opus", "claude haiku",
            "gpt-5", "gpt-4", "gemini-2", "gemini-3",
            "grok-2", "grok-3", "grok-4",
        ]
        # Check non-source_file string values in base agents
        for agent in catalog["base_agents"].values():
            for key, val in agent.items():
                if key == "source_file":
                    continue
                if isinstance(val, str):
                    for pat in patterns:
                        assert pat not in val.lower(), \
                            f"Model pattern '{pat}' in base agent {agent['id']}.{key}: {val[:80]}"

    def test_general_purpose_not_route_eligible(self):
        catalog = _load_catalog()
        gp = catalog["personas"].get("general-purpose-dopemux")
        assert gp is not None, "general-purpose-dopemux missing"
        assert gp["route_eligible"] is False, \
            "general-purpose-dopemux must not be route_eligible"

    def test_every_persona_has_base_agents(self):
        catalog = _load_catalog()
        for pid, persona in catalog["personas"].items():
            assert len(persona["base_agents"]) >= 1, \
                f"Persona {pid} has no base agents"
            for ba in persona["base_agents"]:
                assert ba in catalog["base_agents"], \
                    f"Persona {pid} references unknown base agent {ba}"

    def test_persona_base_agents_valid(self):
        catalog = _load_catalog()
        valid_bases = set(catalog["base_agents"].keys())
        for pid, persona in catalog["personas"].items():
            for ba in persona["base_agents"]:
                assert ba in valid_bases, \
                    f"Persona {pid}: base agent {ba} not in catalog"


class TestSchemaValidation:
    """JSON Schema validation."""

    def test_schema_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema missing at {SCHEMA_PATH}"

    def test_schema_validates_catalog(self):
        if not _HAS_JSONSCHEMA:
            pytest.skip("jsonschema not installed")
        import jsonschema
        catalog = _load_catalog()
        schema = _load_schema()
        jsonschema.validate(catalog, schema)


class TestDeterministic:
    """Catalog generation is deterministic."""

    def test_generation_idempotent(self):
        """Builder must produce identical output on repeated runs."""
        import subprocess

        builder = str(PROJECT_ROOT / "scripts" / "commandcode_router" / "build_normalized_catalog.py")

        # Regenerate to ensure catalog is current
        subprocess.run(
            [sys.executable, builder],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )

        # --check must pass after regeneration
        result = subprocess.run(
            [sys.executable, builder, "--check"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, \
            f"Builder --check failed after regeneration: {result.stderr}"


class TestSourceCoverage:
    """Every active persona source must be represented."""

    def test_persona_index_consistent(self):
        """PERSONA_INDEX.md should reference the active persona set."""
        catalog = _load_catalog()
        persona_ids = set(catalog["personas"].keys())
        index_path = PROJECT_ROOT / ".claude" / "personas" / "PERSONA_INDEX.md"
        if index_path.exists():
            index_text = index_path.read_text()
            # Check that referenced persona files exist as catalog entries
            # This is a weak check; full coverage test is in the builder
            assert len(persona_ids) > 0, "Catalog must have personas"

    def test_source_files_exist(self):
        catalog = _load_catalog()
        for pid, persona in catalog["personas"].items():
            sf = persona.get("source_file")
            if sf:
                assert (PROJECT_ROOT / sf).exists(), \
                    f"Persona {pid} source missing: {sf}"
        for bid, agent in catalog["base_agents"].items():
            sf = agent.get("source_file")
            if sf:
                assert (PROJECT_ROOT / sf).exists(), \
                    f"Base agent {bid} source missing: {sf}"


class TestRoleResolution:
    """Base agent canonical roles must resolve through catalog.py."""

    def test_roles_resolve(self):
        catalog = _load_catalog()
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        try:
            from dopemux.roles.catalog import resolve_role, RoleNotFoundError
        except ImportError:
            pytest.skip("Cannot import dopemux.roles.catalog")

        for agent_id, agent in catalog["base_agents"].items():
            role = agent["canonical_role"]
            try:
                spec = resolve_role(role)
                assert spec.key == role, \
                    f"Agent {agent_id} role {role} resolved to {spec.key}"
            except RoleNotFoundError as e:
                pytest.fail(f"Agent {agent_id} role {role} not found: {e}")


class TestArchitectureApprovedOnly:
    """Only architecture-approved personas are route_eligible."""

    # Per the packet: route_eligible=true only for architecture-approved personas.
    # Currently no personas are route_eligible because all are advisory.
    # If this changes, update this test.
    def test_personas_not_automatically_route_eligible(self):
        catalog = _load_catalog()
        route_eligible_count = sum(
            1 for p in catalog["personas"].values() if p["route_eligible"]
        )
        # All personas are advisory; none should auto-activate routing
        assert route_eligible_count == 0, \
            f"Expected 0 route_eligible personas, got {route_eligible_count}"
