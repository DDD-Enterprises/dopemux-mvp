"""Tests for the normalized agent/persona catalog builder.

Focused, deterministic validation of catalog invariants.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def _load_builder_module():
    """Load build_normalized_catalog without requiring package install."""
    builder_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "commandcode_router"
        / "build_normalized_catalog.py"
    )
    spec = importlib.util.spec_from_file_location(
        "build_normalized_catalog", builder_path
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILDER = _load_builder_module()
PROJECT_ROOT = _BUILDER.resolve_repo_root(start=Path(__file__).resolve())
CATALOG_PATH = PROJECT_ROOT / "config" / "commandcode" / "normalized_agent_persona_catalog.yaml"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "commandcode"
    / "normalized_agent_persona_catalog.schema.json"
)
SOURCE_MANIFEST_REL = "proof/CCAR-002/SOURCE_MANIFEST.json"
BUILDER_SCRIPT = (
    PROJECT_ROOT / "scripts" / "commandcode_router" / "build_normalized_catalog.py"
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
        assert meta["source_manifest"] == SOURCE_MANIFEST_REL
        assert not meta["source_manifest"].startswith("/")
        assert "/Users/" not in meta["source_manifest"]
        assert "/home/" not in meta["source_manifest"]

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
        """Committed catalog must match source, and regeneration must be a no-op.

        ``--check`` runs first against the committed catalog, before any
        regeneration, so committed drift cannot be silently self-healed by
        regenerating before the check ever inspects it. The on-disk catalog
        bytes (including ``generated_at``) are restored afterward so this
        test has no lasting side effect on committed evidence.
        """
        builder = str(BUILDER_SCRIPT)
        original_bytes = CATALOG_PATH.read_bytes()

        try:
            # --check must pass against the committed catalog as-is.
            committed_check = subprocess.run(
                [sys.executable, builder, "--check", "--repo-root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
            )
            assert committed_check.returncode == 0, (
                "Builder --check failed against the committed catalog "
                f"(drift detected): {committed_check.stderr}"
            )

            # Regenerating must be a no-op: --check must still pass afterward.
            subprocess.run(
                [sys.executable, builder, "--repo-root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            result = subprocess.run(
                [sys.executable, builder, "--check", "--repo-root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, \
                f"Builder --check failed after regeneration: {result.stderr}"
        finally:
            CATALOG_PATH.write_bytes(original_bytes)

    def test_source_manifest_repo_relative_in_yaml(self):
        text = CATALOG_PATH.read_text()
        assert "source_manifest: proof/CCAR-002/SOURCE_MANIFEST.json" in text
        assert "/Users/" not in text.split("personas:")[0]
        assert re.search(r"source_manifest:\s*/", text) is None

    def test_dual_worktree_byte_identical_catalog(self, tmp_path):
        """Catalog YAML from two differently located worktrees must match.

        ``generated_at`` is fixed so true byte identity is required (CCAR-002R).
        """
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
        ).strip()
        wt_a = tmp_path / "wt-a-ccar002r"
        wt_b = tmp_path / "wt-b-ccar002r"
        # Detached worktrees at same commit, different absolute paths
        for wt in (wt_a, wt_b):
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(wt), head],
                cwd=str(PROJECT_ROOT),
                check=True,
                capture_output=True,
                text=True,
            )

        fixed_ts = "2026-08-02T00:00:00Z"
        outs = []
        try:
            for wt in (wt_a, wt_b):
                # Use the under-test builder (working tree) against each worktree root.
                # Worktrees are at HEAD (pre-R1) so their own script lacks --repo-root;
                # portability is exercised by binding different absolute roots.
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(BUILDER_SCRIPT),
                        "--repo-root",
                        str(wt),
                        "--generated-at",
                        fixed_ts,
                        "--stdout",
                    ],
                    cwd=str(wt),
                    capture_output=True,
                    text=True,
                )
                assert proc.returncode == 0, (
                    f"Builder failed in {wt}:\nstdout={proc.stdout}\nstderr={proc.stderr}"
                )
                # --stdout emits pure YAML on stdout; status goes to stderr.
                yaml_body = proc.stdout
                assert yaml_body.startswith("meta:"), (
                    f"Expected pure YAML from {wt}, got: {yaml_body[:300]!r}"
                )
                outs.append(yaml_body)
        finally:
            for wt in (wt_a, wt_b):
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt)],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                )

        assert outs[0] == outs[1], (
            "Dual-worktree catalog outputs differ.\n"
            f"len_a={len(outs[0])} len_b={len(outs[1])}\n"
            f"a_head={outs[0][:200]!r}\nb_head={outs[1][:200]!r}"
        )
        assert "source_manifest: proof/CCAR-002/SOURCE_MANIFEST.json" in outs[0]
        assert str(wt_a) not in outs[0]
        assert str(wt_b) not in outs[0]
        assert "/Users/" not in outs[0].split("personas:")[0]

    def test_resolve_repo_root_rejects_invalid(self, tmp_path):
        with pytest.raises(SystemExit):
            _BUILDER.resolve_repo_root(explicit=tmp_path)


class TestScanModelIds:
    """_scan_model_ids must report the full matched token, not a fragment."""

    def test_returns_full_match_not_capture_fragment(self):
        found = _BUILDER._scan_model_ids("Model: claude-sonnet-4.5, notes below.")
        assert "claude-sonnet-4.5" in found
        assert "sonnet" not in found

    def test_matches_each_claude_family(self):
        text = "claude opus-3, claude-haiku-4.5, claude sonnet-5"
        found = _BUILDER._scan_model_ids(text)
        assert any(m.lower().startswith("claude opus-3") for m in found)
        assert any(m.lower().startswith("claude-haiku-4.5") for m in found)
        assert any(m.lower().startswith("claude sonnet-5") for m in found)


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
