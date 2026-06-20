"""
Tests for schemas/project_control_plane/authority_map.schema.json

Validates the schema itself meta-validates (Draft2020-12), exercises a fully-valid
instance, and confirms each fail-closed rule rejects invalid instances.
"""

import json
import pathlib
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema loading — CWD-independent, resolved relative to THIS file.
# Repository root is 3 levels up: tests/project_control_plane/test_*.py
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "project_control_plane" / "authority_map.schema.json"


def _load_schema() -> dict:
    with _SCHEMA_PATH.open() as fh:
        return json.load(fh)


SCHEMA = _load_schema()


def errors(schema, inst):
    """Return all validation errors produced by Draft202012Validator."""
    return list(Draft202012Validator(schema).iter_errors(inst))


# ---------------------------------------------------------------------------
# Minimal valid SOURCE entry (read-only SOURCE — live_write_allowed false)
# ---------------------------------------------------------------------------
_VALID_ENTRY = {
    "domain": "pm.tasks",
    "action": "write",
    "canonical_authority_owner": "conport",
    "canonical_writer": None,
    "surface_class": "SOURCE",
    "reader_or_projection_surface": None,
    "source_truth_refs": ["schemas/project_control_plane/authority_map.schema.json"],
    "proof_required": True,
    "live_write_allowed": False,
    "approval_required": True,
    "rollback_required": True,
    "unknown_behavior": "BLOCK_OR_ESCALATE",
}

_VALID_INSTANCE = {
    "schema_version": "pcp.authority_map.v0",
    "project_id": "dopemux-mvp",
    "entries": [_VALID_ENTRY],
}

# Derived (non-SOURCE) entry — must have live_write_allowed=false and canonical_writer=null
_VALID_DERIVED_ENTRY = {
    **_VALID_ENTRY,
    "surface_class": "CACHE",
    "live_write_allowed": False,
    "canonical_writer": None,
}

# Writable SOURCE entry — live_write_allowed=true requires surface_class=SOURCE and non-null canonical_writer
_VALID_WRITABLE_ENTRY = {
    **_VALID_ENTRY,
    "surface_class": "SOURCE",
    "live_write_allowed": True,
    "canonical_writer": "conport-api",
}


# ---------------------------------------------------------------------------
# 1. Meta-validation: the schema itself must be a valid Draft 2020-12 schema.
# ---------------------------------------------------------------------------
class TestSchemaMetaValidation:
    def test_schema_meta_validates(self):
        """Draft202012Validator.check_schema must not raise for a valid schema."""
        Draft202012Validator.check_schema(SCHEMA)


# ---------------------------------------------------------------------------
# 2. Valid instance: no errors expected.
# ---------------------------------------------------------------------------
class TestValidInstance:
    def test_fully_valid_instance_produces_zero_errors(self):
        errs = errors(SCHEMA, _VALID_INSTANCE)
        assert errs == [], f"Unexpected validation errors: {errs}"

    def test_reader_projection_surface_can_be_null(self):
        instance = {**_VALID_INSTANCE, "entries": [{**_VALID_ENTRY, "reader_or_projection_surface": None}]}
        assert errors(SCHEMA, instance) == []

    def test_reader_projection_surface_can_be_string(self):
        instance = {**_VALID_INSTANCE, "entries": [{**_VALID_ENTRY, "reader_or_projection_surface": "dashboard"}]}
        assert errors(SCHEMA, instance) == []

    def test_surface_class_projection_is_valid(self):
        """PROJECTION with live_write_allowed=false and canonical_writer=null is valid."""
        entry = {**_VALID_ENTRY, "surface_class": "PROJECTION", "live_write_allowed": False, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance) == []

    def test_surface_class_mirror_is_valid(self):
        """MIRROR with live_write_allowed=false and canonical_writer=null is valid."""
        entry = {**_VALID_ENTRY, "surface_class": "MIRROR", "live_write_allowed": False, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance) == []

    def test_surface_class_cache_is_valid(self):
        """CACHE with live_write_allowed=false and canonical_writer=null is valid."""
        instance = {**_VALID_INSTANCE, "entries": [_VALID_DERIVED_ENTRY]}
        assert errors(SCHEMA, instance) == []

    def test_surface_class_index_is_valid(self):
        """INDEX with live_write_allowed=false and canonical_writer=null is valid."""
        entry = {**_VALID_ENTRY, "surface_class": "INDEX", "live_write_allowed": False, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance) == []

    def test_surface_class_adapter_is_valid(self):
        """ADAPTER with live_write_allowed=false and canonical_writer=null is valid."""
        entry = {**_VALID_ENTRY, "surface_class": "ADAPTER", "live_write_allowed": False, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance) == []

    def test_surface_class_unknown_is_valid(self):
        """UNKNOWN with live_write_allowed=false and canonical_writer=null is valid."""
        entry = {**_VALID_ENTRY, "surface_class": "UNKNOWN", "live_write_allowed": False, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance) == []

    def test_canonical_writer_can_be_null_on_source_readonly(self):
        """SOURCE with live_write_allowed=false may have canonical_writer=null."""
        instance = {**_VALID_INSTANCE, "entries": [{**_VALID_ENTRY, "canonical_writer": None}]}
        assert errors(SCHEMA, instance) == []

    def test_source_writable_with_nonnull_canonical_writer_is_valid(self):
        """SOURCE with live_write_allowed=true and a non-null canonical_writer is valid."""
        instance = {**_VALID_INSTANCE, "entries": [_VALID_WRITABLE_ENTRY]}
        assert errors(SCHEMA, instance) == []

    def test_cache_readonly_null_canonical_writer_is_valid(self):
        """CACHE with live_write_allowed=false and canonical_writer=null is valid."""
        entry = {**_VALID_ENTRY, "surface_class": "CACHE", "live_write_allowed": False, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance) == []


# ---------------------------------------------------------------------------
# 3. Fail-closed rejection tests — each must produce at least one error.
# ---------------------------------------------------------------------------
class TestFailClosedRejections:
    def test_rejects_unknown_behavior_warn(self):
        """unknown_behavior must be const 'BLOCK_OR_ESCALATE'; 'WARN' must be rejected."""
        entry = {**_VALID_ENTRY, "unknown_behavior": "WARN"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for unknown_behavior='WARN'"

    def test_rejects_unknown_behavior_ignore(self):
        """Any value other than the pinned const must be rejected."""
        entry = {**_VALID_ENTRY, "unknown_behavior": "IGNORE"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for unknown_behavior='IGNORE'"

    def test_rejects_missing_canonical_writer(self):
        """Removing required key 'canonical_writer' must produce errors."""
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "canonical_writer"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'canonical_writer'"

    def test_rejects_missing_domain(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "domain"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'domain'"

    def test_rejects_missing_action(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "action"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'action'"

    def test_rejects_missing_canonical_authority_owner(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "canonical_authority_owner"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'canonical_authority_owner'"

    def test_rejects_missing_surface_class(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "surface_class"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'surface_class'"

    def test_rejects_missing_reader_or_projection_surface(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "reader_or_projection_surface"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'reader_or_projection_surface'"

    def test_rejects_missing_source_truth_refs(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "source_truth_refs"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'source_truth_refs'"

    def test_rejects_missing_proof_required(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "proof_required"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'proof_required'"

    def test_rejects_missing_live_write_allowed(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "live_write_allowed"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'live_write_allowed'"

    def test_rejects_missing_approval_required(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "approval_required"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'approval_required'"

    def test_rejects_missing_rollback_required(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "rollback_required"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'rollback_required'"

    def test_rejects_missing_unknown_behavior(self):
        entry = {k: v for k, v in _VALID_ENTRY.items() if k != "unknown_behavior"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'unknown_behavior'"

    def test_rejects_wrong_schema_version(self):
        """schema_version const must be 'pcp.authority_map.v0'; any other value rejected."""
        instance = {**_VALID_INSTANCE, "schema_version": "v1"}
        assert errors(SCHEMA, instance), "Expected rejection for schema_version='v1'"

    def test_rejects_schema_version_wrong_prefix(self):
        instance = {**_VALID_INSTANCE, "schema_version": "pcp.authority_map.v1"}
        assert errors(SCHEMA, instance), "Expected rejection for schema_version with wrong version"

    def test_rejects_surface_class_invalid_value(self):
        """'BOSS' is not in the enum; must be rejected."""
        entry = {**_VALID_ENTRY, "surface_class": "BOSS"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for surface_class='BOSS'"

    def test_rejects_surface_class_lowercase(self):
        """'source' (lowercase) is not in the enum; must be rejected."""
        entry = {**_VALID_ENTRY, "surface_class": "source"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for surface_class='source'"

    def test_rejects_extra_top_level_key(self):
        """additionalProperties is false at the top level; extra keys must be rejected."""
        instance = {**_VALID_INSTANCE, "unexpected_field": "should_fail"}
        assert errors(SCHEMA, instance), "Expected rejection for top-level extra key"

    def test_rejects_extra_entry_key(self):
        """additionalProperties is false on authority_entry; extra keys must be rejected."""
        entry = {**_VALID_ENTRY, "rogue_field": "bad"}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for extra entry key"

    def test_rejects_missing_schema_version(self):
        instance = {k: v for k, v in _VALID_INSTANCE.items() if k != "schema_version"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'schema_version'"

    def test_rejects_missing_project_id(self):
        instance = {k: v for k, v in _VALID_INSTANCE.items() if k != "project_id"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'project_id'"

    def test_rejects_missing_entries(self):
        instance = {k: v for k, v in _VALID_INSTANCE.items() if k != "entries"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'entries'"

    # -----------------------------------------------------------------------
    # Hardened schema: new rejection tests
    # -----------------------------------------------------------------------

    def test_rejects_empty_entries_array(self):
        """entries now has minItems:1; an empty array must be rejected."""
        instance = {**_VALID_INSTANCE, "entries": []}
        assert errors(SCHEMA, instance), "Expected rejection for empty entries array"

    def test_rejects_generated_from_fixture_field(self):
        """generated_from_fixture was removed from schema; additionalProperties:false rejects it."""
        instance = {**_VALID_INSTANCE, "generated_from_fixture": True}
        assert errors(SCHEMA, instance), "Expected rejection for unknown property 'generated_from_fixture'"

    def test_rejects_empty_string_project_id(self):
        """project_id now has minLength:1; empty string must be rejected."""
        instance = {**_VALID_INSTANCE, "project_id": ""}
        assert errors(SCHEMA, instance), "Expected rejection for empty string project_id"

    def test_rejects_empty_source_truth_refs(self):
        """source_truth_refs now has minItems:1; empty list must be rejected."""
        entry = {**_VALID_ENTRY, "source_truth_refs": []}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for empty source_truth_refs"

    def test_rejects_cache_with_live_write_allowed_true(self):
        """CACHE is a derived surface; live_write_allowed=true must be rejected."""
        entry = {**_VALID_ENTRY, "surface_class": "CACHE", "live_write_allowed": True, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for CACHE with live_write_allowed=true"

    def test_rejects_cache_with_nonnull_canonical_writer(self):
        """CACHE is a derived surface; canonical_writer must be null; non-null must be rejected."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "CACHE",
            "live_write_allowed": False,
            "canonical_writer": "some-writer",
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for CACHE with non-null canonical_writer"

    def test_rejects_source_writable_with_null_canonical_writer(self):
        """SOURCE with live_write_allowed=true but canonical_writer=null must be rejected."""
        entry = {**_VALID_ENTRY, "surface_class": "SOURCE", "live_write_allowed": True, "canonical_writer": None}
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for SOURCE writable with null canonical_writer"

    def test_rejects_projection_with_live_write_allowed_true(self):
        """PROJECTION is a derived surface; live_write_allowed=true must be rejected."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "PROJECTION",
            "live_write_allowed": True,
            "canonical_writer": None,
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for PROJECTION with live_write_allowed=true"

    def test_rejects_mirror_with_live_write_allowed_true(self):
        """MIRROR is a derived surface; live_write_allowed=true must be rejected."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "MIRROR",
            "live_write_allowed": True,
            "canonical_writer": None,
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for MIRROR with live_write_allowed=true"

    def test_rejects_index_with_live_write_allowed_true(self):
        """INDEX is a derived surface; live_write_allowed=true must be rejected."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "INDEX",
            "live_write_allowed": True,
            "canonical_writer": None,
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for INDEX with live_write_allowed=true"

    def test_rejects_adapter_with_live_write_allowed_true(self):
        """ADAPTER is a derived surface; live_write_allowed=true must be rejected."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "ADAPTER",
            "live_write_allowed": True,
            "canonical_writer": None,
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for ADAPTER with live_write_allowed=true"

    def test_rejects_unknown_surface_with_live_write_allowed_true(self):
        """UNKNOWN is a derived surface; live_write_allowed=true must be rejected."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "UNKNOWN",
            "live_write_allowed": True,
            "canonical_writer": None,
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for UNKNOWN with live_write_allowed=true"

    def test_rejects_projection_with_nonnull_canonical_writer(self):
        """PROJECTION is a derived surface; canonical_writer must be null."""
        entry = {
            **_VALID_ENTRY,
            "surface_class": "PROJECTION",
            "live_write_allowed": False,
            "canonical_writer": "some-writer",
        }
        instance = {**_VALID_INSTANCE, "entries": [entry]}
        assert errors(SCHEMA, instance), "Expected rejection for PROJECTION with non-null canonical_writer"
