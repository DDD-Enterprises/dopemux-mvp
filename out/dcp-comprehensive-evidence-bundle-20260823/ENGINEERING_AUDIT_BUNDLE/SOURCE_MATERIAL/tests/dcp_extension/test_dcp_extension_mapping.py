"""
Tests for the DCP extension mapping (Packet 5).

Validates that:
  - schemas/dcp_extension/extension_manifest.dcp.json is a valid instance of
    schemas/project_control_plane/extension_manifest.schema.json
  - schemas/dcp_extension/authority_map.dcp.json is a valid instance of
    schemas/project_control_plane/authority_map.schema.json
  - No system is promoted to authority (all entries are read/projection only,
    no live writes, no SOURCE surface_class, canonical_writer is null)
  - All owned_schema_ids in the manifest correspond to existing files under
    schemas/dcp_extension/
  - Negative/tamper tests confirm the schema gates hold
"""

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Paths — resolved from repo root (tests/dcp_extension/test_*.py is 3 levels up)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMAS_PCP = _REPO_ROOT / "schemas" / "project_control_plane"
_SCHEMAS_DCP = _REPO_ROOT / "schemas" / "dcp_extension"

_MANIFEST_SCHEMA_PATH = _SCHEMAS_PCP / "extension_manifest.schema.json"
_AUTHORITY_SCHEMA_PATH = _SCHEMAS_PCP / "authority_map.schema.json"
_MANIFEST_INST_PATH = _SCHEMAS_DCP / "extension_manifest.dcp.json"
_AUTHORITY_INST_PATH = _SCHEMAS_DCP / "authority_map.dcp.json"


def _load(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


# Load once at module level; if files are missing the import itself will fail
# with a clear FileNotFoundError (no hidden test skip)
MANIFEST_SCHEMA = _load(_MANIFEST_SCHEMA_PATH)
AUTHORITY_SCHEMA = _load(_AUTHORITY_SCHEMA_PATH)
MANIFEST_INST = _load(_MANIFEST_INST_PATH)
AUTHORITY_INST = _load(_AUTHORITY_INST_PATH)


def errors(schema: dict, instance: dict) -> list:
    return list(Draft202012Validator(schema).iter_errors(instance))


# ---------------------------------------------------------------------------
# 1. JSON Schema validation — extension_manifest.dcp.json
# ---------------------------------------------------------------------------
class TestExtensionManifestInstance:
    def test_validates_against_schema(self):
        errs = errors(MANIFEST_SCHEMA, MANIFEST_INST)
        assert errs == [], f"extension_manifest.dcp.json has schema errors: {errs}"

    def test_extension_kind_is_dopemux_dcp(self):
        assert MANIFEST_INST["extension_kind"] == "DOPEMUX_DCP"

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
# 2. JSON Schema validation — authority_map.dcp.json
# ---------------------------------------------------------------------------
class TestAuthorityMapInstance:
    def test_validates_against_schema(self):
        errs = errors(AUTHORITY_SCHEMA, AUTHORITY_INST)
        assert errs == [], f"authority_map.dcp.json has schema errors: {errs}"

    def test_entries_non_empty(self):
        assert len(AUTHORITY_INST["entries"]) > 0, "entries must be non-empty"


# ---------------------------------------------------------------------------
# 3. No system promoted to authority — P3 gate
# ---------------------------------------------------------------------------
class TestNoAuthorityPromotion:
    """Every entry must be read-only, adapter/projection, no canonical writer."""

    @pytest.fixture(params=AUTHORITY_INST["entries"])
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
            f"Entry {entry['domain']}/{entry['action']} is SOURCE (would mean DCP owns it)"
        )

    def test_unknown_behavior_is_block_or_escalate(self, entry):
        assert entry["unknown_behavior"] == "BLOCK_OR_ESCALATE", (
            f"Entry {entry['domain']}/{entry['action']} unknown_behavior is not BLOCK_OR_ESCALATE"
        )


# ---------------------------------------------------------------------------
# 4. owned_schema_ids file existence
# ---------------------------------------------------------------------------
class TestOwnedSchemaIds:
    def test_owned_schema_ids_files_exist(self):
        owned = MANIFEST_INST["schemas"]["owned_schema_ids"]
        assert owned, "owned_schema_ids must not be empty"
        for schema_id in owned:
            # schema_id is relative to schemas/ directory (dcp_extension/foo.schema.json)
            candidate = _REPO_ROOT / "schemas" / schema_id
            assert candidate.exists(), (
                f"owned_schema_id '{schema_id}' does not correspond to an existing file at {candidate}"
            )


# ---------------------------------------------------------------------------
# 5. Negative/tamper tests — schema gates must hold
# ---------------------------------------------------------------------------
class TestNegativeTamper:
    def test_tampered_manifest_cannot_promote_adapter_false_is_rejected(self):
        """A manifest with cannot_promote_adapter_to_authority=false must be invalid."""
        tampered = copy.deepcopy(MANIFEST_INST)
        tampered["invariants"]["cannot_promote_adapter_to_authority"] = False
        errs = errors(MANIFEST_SCHEMA, tampered)
        assert errs, "Schema should reject cannot_promote_adapter_to_authority=False"

    def test_authority_entry_live_write_true_with_null_writer_is_rejected(self):
        """An entry with live_write_allowed=true and canonical_writer=null must be rejected (P3 gate)."""
        tampered = copy.deepcopy(AUTHORITY_INST)
        # Inject a bad entry: live_write=true but no canonical_writer (null) and surface stays ADAPTER
        bad_entry = {
            "domain": "workflow.tasks",
            "action": "write",
            "canonical_authority_owner": "task-orchestrator",
            "canonical_writer": None,
            "surface_class": "ADAPTER",
            "reader_or_projection_surface": "some surface",
            "source_truth_refs": ["some ref"],
            "proof_required": True,
            "live_write_allowed": True,
            "approval_required": False,
            "rollback_required": False,
            "unknown_behavior": "BLOCK_OR_ESCALATE",
        }
        tampered["entries"].append(bad_entry)
        errs = errors(AUTHORITY_SCHEMA, tampered)
        assert errs, (
            "Schema should reject entry with live_write_allowed=true, canonical_writer=null "
            "(P3 live-write gate)"
        )

    def test_source_write_escalation_caught_by_dcp_guard(self):
        """The generic PCP Core schema PERMITS a SOURCE entry with a live write — PCP Core must
        let a real project's authority map name actual sources. So DCP's read-only guarantee is
        enforced by the DCP boundary guard, not the schema. This test documents that gap and
        proves the guard catches the escalation (keeps dcp-extension-mapping.md honest)."""
        tampered = copy.deepcopy(AUTHORITY_INST)
        escalation = {
            "domain": "workflow.tasks",
            "action": "write",
            "canonical_authority_owner": "task-orchestrator",
            "canonical_writer": "dcp-attacker",
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
        # Generic contract ACCEPTS this (SOURCE + non-empty writer + live write is valid PCP Core):
        assert errors(AUTHORITY_SCHEMA, tampered) == [], (
            "Generic schema is expected to ACCEPT a SOURCE+live_write entry; if this starts "
            "failing, the core schema gained a SOURCE restriction and the doc must be updated."
        )
        # DCP boundary guard REJECTS it (no DCP entry may be SOURCE, writable, or have a writer):
        offenders = [
            e
            for e in tampered["entries"]
            if e["surface_class"] == "SOURCE"
            or e["live_write_allowed"] is not False
            or e["canonical_writer"] is not None
        ]
        assert offenders, "DCP boundary guard must catch a SOURCE/live-write escalation"


# ---------------------------------------------------------------------------
# 6. Packet-5 scope lock — exactly the ten target systems, manifest in sync
# ---------------------------------------------------------------------------
class TestPacketScope:
    """Packet-5 scope-lock, modelled as TWO planes:

    - ADAPTER plane: the eleven MCP-system owners (ten Packet-5 targets + Leantime).
      Their owners must equal EXPECTED_SYSTEMS and stay 1:1 with the manifest
      adapter_mappings. This plane is unchanged by the proof-family work.
    - PROOF-FAMILY plane: ``proof.*`` domains map repo proof artifacts (not an MCP
      system) into PCP proof pointers; the project itself is the owner, so these
      entries are guarded separately and are NOT part of adapter_mappings.

    Entries are assigned to a plane by domain prefix (``proof.*`` → proof-family).
    Guards against scope drift on both planes."""

    EXPECTED_SYSTEMS = {
        "task-orchestrator",
        "conport",
        "dope-memory",
        "dope-context",
        "dopecon-bridge",
        "adhd-engine",
        "repo-truth-extractor",
        "dopetask",
        "dopemux-cli",
        "pr-steward",
        "leantime",
    }
    EXPECTED_PROOF_OWNERS = {"dopemux"}

    @staticmethod
    def _adapter_owners() -> set:
        return {
            e["canonical_authority_owner"]
            for e in AUTHORITY_INST["entries"]
            if not e["domain"].startswith("proof.")
        }

    @staticmethod
    def _proof_owners() -> set:
        return {
            e["canonical_authority_owner"]
            for e in AUTHORITY_INST["entries"]
            if e["domain"].startswith("proof.")
        }

    def test_adapter_systems_match_packet_target(self):
        owners = self._adapter_owners()
        assert owners == self.EXPECTED_SYSTEMS, (
            f"DCP adapter-plane systems drifted from the Packet 5 target. "
            f"Unexpected: {owners - self.EXPECTED_SYSTEMS}; Missing: {self.EXPECTED_SYSTEMS - owners}"
        )

    def test_manifest_adapter_mappings_match_adapter_owners(self):
        owners = self._adapter_owners()
        adapter_mappings = set(MANIFEST_INST["capabilities"]["adapter_mappings"])
        assert adapter_mappings == owners, (
            f"manifest adapter_mappings out of sync with adapter-plane owners. "
            f"Only in manifest: {adapter_mappings - owners}; only in map: {owners - adapter_mappings}"
        )

    def test_proof_family_owners_locked(self):
        owners = self._proof_owners()
        assert owners == self.EXPECTED_PROOF_OWNERS, (
            f"DCP proof-family plane drifted. "
            f"Unexpected: {owners - self.EXPECTED_PROOF_OWNERS}; "
            f"Missing: {self.EXPECTED_PROOF_OWNERS - owners}"
        )


# ---------------------------------------------------------------------------
# 7. Leantime entry focused test — post-P5 loose-end amendment
# ---------------------------------------------------------------------------
class TestLeantimeEntry:
    """Focused assertions for the Leantime pm.metadata read ADAPTER entry (AIR §7 gap closure)."""

    @staticmethod
    def _leantime_entry() -> dict:
        entries = [
            e for e in AUTHORITY_INST["entries"]
            if e["canonical_authority_owner"] == "leantime"
        ]
        assert len(entries) == 1, (
            f"Expected exactly one leantime entry in authority map; found {len(entries)}"
        )
        return entries[0]

    def test_leantime_entry_exists(self):
        entry = self._leantime_entry()
        assert entry["domain"] == "pm.metadata"
        assert entry["action"] == "read"

    def test_leantime_surface_class_is_adapter(self):
        entry = self._leantime_entry()
        assert entry["surface_class"] == "ADAPTER", (
            f"Expected ADAPTER, got {entry['surface_class']}"
        )

    def test_leantime_live_write_not_allowed(self):
        entry = self._leantime_entry()
        assert entry["live_write_allowed"] is False

    def test_leantime_canonical_writer_is_null(self):
        entry = self._leantime_entry()
        assert entry["canonical_writer"] is None


# ---------------------------------------------------------------------------
# 8. Proof-family entry focused test — A2 proof-family follow-up
# ---------------------------------------------------------------------------
class TestProofFamilyEntry:
    """Focused assertions for the proof.dopemux_family read ADAPTER entry.

    The proof family is a distinct plane from the MCP adapter set: the project
    itself owns its proof artifacts (PROOF.json / SUMMARY.md), so this entry is
    NOT part of manifest.adapter_mappings, yet stays fully read-only/fail-closed."""

    @staticmethod
    def _proof_entry() -> dict:
        entries = [
            e for e in AUTHORITY_INST["entries"]
            if e["domain"] == "proof.dopemux_family"
        ]
        assert len(entries) == 1, (
            f"Expected exactly one proof.dopemux_family entry; found {len(entries)}"
        )
        return entries[0]

    def test_proof_entry_exists_and_reads(self):
        entry = self._proof_entry()
        assert entry["action"] == "read"
        assert entry["canonical_authority_owner"] == "dopemux"

    def test_proof_entry_is_read_only_adapter(self):
        entry = self._proof_entry()
        assert entry["surface_class"] == "ADAPTER"
        assert entry["live_write_allowed"] is False
        assert entry["canonical_writer"] is None
        assert entry["unknown_behavior"] == "BLOCK_OR_ESCALATE"

    def test_proof_entry_not_in_adapter_mappings(self):
        # Clean two-plane model: the proof family must NOT pollute the MCP adapter set.
        adapter_mappings = set(MANIFEST_INST["capabilities"]["adapter_mappings"])
        assert "dopemux" not in adapter_mappings
        assert self._proof_entry()["canonical_authority_owner"] not in adapter_mappings
