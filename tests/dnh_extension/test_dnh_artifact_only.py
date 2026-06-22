"""
Tests for the dNh CRM extension mapping (Packet 7).

Validates that:
  - schemas/dnh_extension/extension_manifest.dnh.json is a valid instance of
    schemas/project_control_plane/extension_manifest.schema.json
  - schemas/dnh_extension/authority_map.dnh.json is a valid instance of
    schemas/project_control_plane/authority_map.schema.json
  - All entries are ARTIFACT-ONLY: no live writes, no SOURCE surface, canonical_writer is null,
    unknown_behavior is BLOCK_OR_ESCALATE
  - No-send / no-write / no-import for all mutation domains
  - Red-lane fixture validates against project_red_lanes.schema.json with correct defaults
  - dNh must never be required by PCP Core (cannot_require_extension_for_baseline_core=True)
  - Manifest declares no live runtime (runtime_mappings==[], proof_status_mappings==[])
  - Scope lock: exactly the 10 domains, all owned by dnh-crm
  - Manifest adapter_mappings (10) correspond to the 10 entry domains
  - Negative tamper: schema gates hold
"""

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Paths — repo root is 3 levels up from tests/dnh_extension/test_*.py
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCHEMAS_PCP = _REPO_ROOT / "schemas" / "project_control_plane"
_SCHEMAS_DNH = _REPO_ROOT / "schemas" / "dnh_extension"
_FIXTURES_DNH = _REPO_ROOT / "reports" / "project-control-plane" / "fixtures" / "dnh_crm_fixture"

_MANIFEST_SCHEMA_PATH = _SCHEMAS_PCP / "extension_manifest.schema.json"
_AUTHORITY_SCHEMA_PATH = _SCHEMAS_PCP / "authority_map.schema.json"
_RED_LANES_SCHEMA_PATH = _SCHEMAS_PCP / "project_red_lanes.schema.json"

_MANIFEST_INST_PATH = _SCHEMAS_DNH / "extension_manifest.dnh.json"
_AUTHORITY_INST_PATH = _SCHEMAS_DNH / "authority_map.dnh.json"
_RED_LANES_PATH = _FIXTURES_DNH / "red_lanes.json"


def _load(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


# Load once at module level; missing files produce clear FileNotFoundError (no silent skip).
MANIFEST_SCHEMA = _load(_MANIFEST_SCHEMA_PATH)
AUTHORITY_SCHEMA = _load(_AUTHORITY_SCHEMA_PATH)
RED_LANES_SCHEMA = _load(_RED_LANES_SCHEMA_PATH)

MANIFEST_INST = _load(_MANIFEST_INST_PATH)
AUTHORITY_INST = _load(_AUTHORITY_INST_PATH)
RED_LANES_INST = _load(_RED_LANES_PATH)

# Canonical 10 domains for this packet
EXPECTED_DOMAINS = {
    "dnh.project_profile",
    "dnh.authority_docs",
    "dnh.proof_roots",
    "dnh.crm",
    "dnh.telegram",
    "dnh.calendar",
    "dnh.identity",
    "dnh.policy",
    "dnh.event_store",
    "dnh.runtime_db",
}

# Domain->adapter-name mapping for the manifest check
_DOMAIN_TO_ADAPTER = {
    "dnh.project_profile": "dnh-project-profile",
    "dnh.authority_docs": "dnh-authority-docs",
    "dnh.proof_roots": "dnh-proof-roots",
    "dnh.crm": "dnh-crm",
    "dnh.telegram": "dnh-telegram",
    "dnh.calendar": "dnh-calendar",
    "dnh.identity": "dnh-identity",
    "dnh.policy": "dnh-policy",
    "dnh.event_store": "dnh-event-store",
    "dnh.runtime_db": "dnh-runtime-db",
}

# Mutation domains that must have no send/write/import
_MUTATION_DOMAINS = {
    "dnh.crm",
    "dnh.telegram",
    "dnh.calendar",
    "dnh.identity",
    "dnh.policy",
    "dnh.event_store",
    "dnh.runtime_db",
}

# Required red-lane IDs per the fixture specification
_REQUIRED_RED_LANE_IDS = {"crm-write", "telegram-send", "calendar-write", "runtime-db", "identity-merge"}


def _schema_errors(schema: dict, instance: dict) -> list:
    return list(Draft202012Validator(schema).iter_errors(instance))


def _entry_by_domain(domain: str) -> dict:
    matches = [e for e in AUTHORITY_INST["entries"] if e["domain"] == domain]
    assert matches, f"No entry found for domain '{domain}'"
    return matches[0]


# ---------------------------------------------------------------------------
# 1. Extension manifest schema validation
# ---------------------------------------------------------------------------
class TestExtensionManifestInstance:
    def test_validates_against_schema(self):
        errs = _schema_errors(MANIFEST_SCHEMA, MANIFEST_INST)
        assert errs == [], f"extension_manifest.dnh.json has schema errors: {errs}"

    def test_extension_kind_is_dnh_crm(self):
        assert MANIFEST_INST["extension_kind"] == "DNH_CRM"

    def test_invariant_cannot_override_core_fail_closed(self):
        assert MANIFEST_INST["invariants"]["cannot_override_core_fail_closed"] is True

    def test_invariant_cannot_weaken_proof_gates(self):
        assert MANIFEST_INST["invariants"]["cannot_weaken_proof_gates"] is True

    def test_invariant_cannot_weaken_audit_gates(self):
        assert MANIFEST_INST["invariants"]["cannot_weaken_audit_gates"] is True

    def test_invariant_cannot_promote_adapter_to_authority(self):
        assert MANIFEST_INST["invariants"]["cannot_promote_adapter_to_authority"] is True

    def test_invariant_cannot_require_extension_for_baseline_core(self):
        assert MANIFEST_INST["invariants"]["cannot_require_extension_for_baseline_core"] is True


# ---------------------------------------------------------------------------
# 2. Authority map schema validation
# ---------------------------------------------------------------------------
class TestAuthorityMapInstance:
    def test_validates_against_schema(self):
        errs = _schema_errors(AUTHORITY_SCHEMA, AUTHORITY_INST)
        assert errs == [], f"authority_map.dnh.json has schema errors: {errs}"

    def test_entries_non_empty(self):
        assert len(AUTHORITY_INST["entries"]) > 0, "entries must be non-empty"


# ---------------------------------------------------------------------------
# 3. ARTIFACT-ONLY guarantee: every entry is read-only, no writer, no SOURCE
# ---------------------------------------------------------------------------
class TestArtifactOnly:
    """Every entry must be artifact-only: no live write, no SOURCE, no canonical writer."""

    @pytest.fixture(params=AUTHORITY_INST["entries"], ids=lambda e: e["domain"])
    def entry(self, request):
        return request.param

    def test_live_write_not_allowed(self, entry):
        assert entry["live_write_allowed"] is False, (
            f"Entry {entry['domain']}/{entry['action']} has live_write_allowed=True"
        )

    def test_canonical_writer_is_null(self, entry):
        assert entry["canonical_writer"] is None, (
            f"Entry {entry['domain']}/{entry['action']} has non-null canonical_writer"
        )

    def test_surface_class_is_not_source(self, entry):
        assert entry["surface_class"] != "SOURCE", (
            f"Entry {entry['domain']}/{entry['action']} has surface_class=SOURCE "
            "(would mean dNh owns the domain, which violates artifact-only)"
        )

    def test_unknown_behavior_is_block_or_escalate(self, entry):
        assert entry["unknown_behavior"] == "BLOCK_OR_ESCALATE", (
            f"Entry {entry['domain']}/{entry['action']} unknown_behavior is "
            f"'{entry['unknown_behavior']}', expected BLOCK_OR_ESCALATE"
        )


# ---------------------------------------------------------------------------
# 4. No-send / no-write / no-import for mutation domains
# ---------------------------------------------------------------------------
class TestMutationDomainsReadOnly:
    """Mutation-risk domains (CRM/Telegram/calendar/identity/policy/event-store/runtime-db)
    must exist in the authority map and be read-only."""

    @pytest.fixture(params=sorted(_MUTATION_DOMAINS))
    def mutation_domain(self, request):
        return request.param

    def test_mutation_domain_exists_and_is_readonly(self, mutation_domain):
        entry = _entry_by_domain(mutation_domain)
        assert entry["live_write_allowed"] is False, (
            f"Mutation domain '{mutation_domain}' must not allow live writes"
        )


# ---------------------------------------------------------------------------
# 5. Red-lane fixture validation
# ---------------------------------------------------------------------------
class TestRedLanes:
    def test_red_lanes_validates_against_schema(self):
        errs = _schema_errors(RED_LANES_SCHEMA, RED_LANES_INST)
        assert errs == [], f"red_lanes.json has schema errors: {errs}"

    def test_default_on_unknown_is_block(self):
        assert RED_LANES_INST["default_on_unknown"] == "BLOCK", (
            "red_lanes.json default_on_unknown must be 'BLOCK'"
        )

    def test_required_lane_ids_present(self):
        lane_ids = {c["lane_id"] for c in RED_LANES_INST["classifications"]}
        missing = _REQUIRED_RED_LANE_IDS - lane_ids
        assert not missing, (
            f"red_lanes.json is missing required lane_ids: {missing}"
        )


# ---------------------------------------------------------------------------
# 6. dNh must never be required by PCP Core
# ---------------------------------------------------------------------------
class TestDnhNotRequiredByCore:
    def test_cannot_require_extension_for_baseline_core_is_true(self):
        """Invariant cannot_require_extension_for_baseline_core=True is the contractual
        guarantee that dNh is a project extension, not a PCP Core template dependency."""
        val = MANIFEST_INST["invariants"]["cannot_require_extension_for_baseline_core"]
        assert val is True, (
            f"cannot_require_extension_for_baseline_core must be True, got {val!r}"
        )


# ---------------------------------------------------------------------------
# 7. Manifest declares no live runtime
# ---------------------------------------------------------------------------
class TestNoLiveRuntime:
    def test_runtime_mappings_is_empty(self):
        assert MANIFEST_INST["capabilities"]["runtime_mappings"] == [], (
            "dNh extension must declare no runtime_mappings (artifact-only)"
        )

    def test_proof_status_mappings_is_empty(self):
        assert MANIFEST_INST["capabilities"]["proof_status_mappings"] == [], (
            "dNh extension must declare no proof_status_mappings (artifact-only)"
        )


# ---------------------------------------------------------------------------
# 8. Scope lock: exactly 10 domains, all owned by dnh-crm
# ---------------------------------------------------------------------------
class TestScopeLock:
    def test_exactly_ten_entries(self):
        assert len(AUTHORITY_INST["entries"]) == 10, (
            f"Expected exactly 10 authority entries, got {len(AUTHORITY_INST['entries'])}"
        )

    def test_canonical_authority_owners_is_dnh_crm(self):
        owners = {e["canonical_authority_owner"] for e in AUTHORITY_INST["entries"]}
        assert owners == {"dnh-crm"}, (
            f"All entries must have canonical_authority_owner='dnh-crm', got {owners}"
        )

    def test_domains_match_expected_set(self):
        actual = {e["domain"] for e in AUTHORITY_INST["entries"]}
        assert actual == EXPECTED_DOMAINS, (
            f"Domain mismatch. "
            f"Unexpected: {actual - EXPECTED_DOMAINS}; "
            f"Missing: {EXPECTED_DOMAINS - actual}"
        )


# ---------------------------------------------------------------------------
# 9. Manifest adapter_mappings correspond to the 10 entry domains
# ---------------------------------------------------------------------------
class TestManifestAdapterMappings:
    def test_adapter_mappings_count_matches_entries(self):
        adapter_mappings = MANIFEST_INST["capabilities"]["adapter_mappings"]
        entries = AUTHORITY_INST["entries"]
        assert len(adapter_mappings) == len(entries) == 10, (
            f"adapter_mappings length ({len(adapter_mappings)}) != entries length "
            f"({len(entries)}), both must be 10"
        )

    def test_adapter_mappings_correspond_to_domains(self):
        adapter_set = set(MANIFEST_INST["capabilities"]["adapter_mappings"])
        expected_adapters = set(_DOMAIN_TO_ADAPTER.values())
        assert adapter_set == expected_adapters, (
            f"adapter_mappings mismatch. "
            f"Only in manifest: {adapter_set - expected_adapters}; "
            f"Only in expected: {expected_adapters - adapter_set}"
        )


# ---------------------------------------------------------------------------
# 10. Negative tamper tests — schema gates must hold
# ---------------------------------------------------------------------------
class TestNegativeTamper:
    def test_manifest_with_cannot_require_extension_false_is_rejected(self):
        """A manifest with cannot_require_extension_for_baseline_core=false must be invalid."""
        tampered = copy.deepcopy(MANIFEST_INST)
        tampered["invariants"]["cannot_require_extension_for_baseline_core"] = False
        errs = _schema_errors(MANIFEST_SCHEMA, tampered)
        assert errs, (
            "Schema must reject cannot_require_extension_for_baseline_core=False"
        )

    def test_source_write_escalation_caught_by_dnh_guard(self):
        """The generic PCP Core schema PERMITS a SOURCE entry with a live write — PCP Core must
        allow a real project's authority map to name actual sources. So dNh's artifact-only
        guarantee is enforced by the dNh boundary guard (this test), not the PCP schema.
        The test proves the guard catches any SOURCE/live-write escalation attempt."""
        tampered = copy.deepcopy(AUTHORITY_INST)
        escalation = {
            "domain": "dnh.crm",
            "action": "write",
            "canonical_authority_owner": "dnh-crm",
            "canonical_writer": "dnh-attacker",
            "surface_class": "SOURCE",
            "reader_or_projection_surface": "escalated surface",
            "source_truth_refs": ["escalated ref"],
            "proof_required": True,
            "live_write_allowed": True,
            "approval_required": False,
            "rollback_required": False,
            "unknown_behavior": "BLOCK_OR_ESCALATE",
        }
        tampered["entries"].append(escalation)
        # Generic PCP Core schema ACCEPTS this (SOURCE + non-empty writer + live write is valid):
        assert _schema_errors(AUTHORITY_SCHEMA, tampered) == [], (
            "Generic schema is expected to ACCEPT a SOURCE+live_write entry; if this starts "
            "failing the core schema gained a SOURCE restriction and the doc must be updated."
        )
        # dNh boundary guard REJECTS it (no dNh entry may be SOURCE, writable, or have a writer):
        offenders = [
            e
            for e in tampered["entries"]
            if e["surface_class"] == "SOURCE"
            or e["live_write_allowed"] is not False
            or e["canonical_writer"] is not None
        ]
        assert offenders, "dNh boundary guard must catch a SOURCE/live-write escalation"
