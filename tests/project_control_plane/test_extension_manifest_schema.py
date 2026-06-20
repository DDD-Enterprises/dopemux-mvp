"""
Tests for schemas/project_control_plane/extension_manifest.schema.json

Validates the schema itself meta-validates (Draft2020-12), exercises fully-valid
instances for DOPEMUX_DCP and DNH_CRM extension kinds, and confirms each
fail-closed invariant and required-field rule rejects invalid instances.
"""

import json
import pathlib
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema loading — CWD-independent, resolved relative to THIS file.
# Repository root is 3 levels up: tests/project_control_plane/test_*.py
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "project_control_plane" / "extension_manifest.schema.json"


def _load_schema() -> dict:
    with _SCHEMA_PATH.open() as fh:
        return json.load(fh)


SCHEMA = _load_schema()


def errors(schema, inst):
    """Return all validation errors produced by Draft202012Validator."""
    return list(Draft202012Validator(schema).iter_errors(inst))


# ---------------------------------------------------------------------------
# Minimal valid instances
# ---------------------------------------------------------------------------
_VALID_INVARIANTS = {
    "cannot_override_core_fail_closed": True,
    "cannot_weaken_proof_gates": True,
    "cannot_weaken_audit_gates": True,
    "cannot_promote_adapter_to_authority": True,
    "cannot_require_extension_for_baseline_core": True,
}

_VALID_CAPABILITIES = {
    "authority_map_contributions": [],
    "red_lane_contributions": [],
    "evidence_export_sections": [],
    "proof_status_mappings": [],
    "runtime_mappings": [],
    "adapter_mappings": [],
}

_VALID_EXTENSION_IDENTITY = {
    "project_id_patterns": ["dopemux-*"],
    "repo_markers": [".dopemux"],
    "discovery_hints": ["look for pyproject.toml with [tool.dopemux]"],
}

_VALID_SCHEMAS = {
    "owned_schema_ids": [],
    "core_schema_extensions": [],
    "forbidden_core_overrides": [],
}

_VALID_DCP_INSTANCE = {
    "schema_version": "pcp.extension_manifest.v0",
    "extension_id": "dopemux-dcp-v0",
    "extension_kind": "DOPEMUX_DCP",
    "extension_identity": _VALID_EXTENSION_IDENTITY,
    "capabilities": _VALID_CAPABILITIES,
    "schemas": _VALID_SCHEMAS,
    "invariants": _VALID_INVARIANTS,
}

_VALID_CRM_INSTANCE = {
    "schema_version": "pcp.extension_manifest.v0",
    "extension_id": "dnh-crm-v0",
    "extension_kind": "DNH_CRM",
    "extension_identity": {
        "project_id_patterns": ["dnh-*"],
        "repo_markers": [".dnh"],
        "discovery_hints": [],
    },
    "capabilities": {
        **_VALID_CAPABILITIES,
        "authority_map_contributions": ["crm.contacts.write"],
        "adapter_mappings": ["crm-adapter"],
    },
    "schemas": {
        "owned_schema_ids": ["https://dnh.dev/schemas/crm/contact.schema.json"],
        "core_schema_extensions": [],
        "forbidden_core_overrides": [
            "https://dopemux.dev/schemas/project_control_plane/authority_map.schema.json"
        ],
    },
    "invariants": _VALID_INVARIANTS,
}


# ---------------------------------------------------------------------------
# 1. Meta-validation
# ---------------------------------------------------------------------------
class TestSchemaMetaValidation:
    def test_schema_meta_validates(self):
        """Draft202012Validator.check_schema must not raise for a valid schema."""
        Draft202012Validator.check_schema(SCHEMA)


# ---------------------------------------------------------------------------
# 2. Valid instances
# ---------------------------------------------------------------------------
class TestValidInstances:
    def test_fully_valid_dopemux_dcp_instance(self):
        errs = errors(SCHEMA, _VALID_DCP_INSTANCE)
        assert errs == [], f"Unexpected errors for DOPEMUX_DCP: {errs}"

    def test_fully_valid_dnh_crm_instance(self):
        errs = errors(SCHEMA, _VALID_CRM_INSTANCE)
        assert errs == [], f"Unexpected errors for DNH_CRM: {errs}"

    def test_project_extension_kind_valid(self):
        instance = {**_VALID_DCP_INSTANCE, "extension_kind": "PROJECT"}
        assert errors(SCHEMA, instance) == []

    def test_unknown_extension_kind_valid(self):
        instance = {**_VALID_DCP_INSTANCE, "extension_kind": "UNKNOWN"}
        assert errors(SCHEMA, instance) == []

    def test_optional_status_proposed(self):
        instance = {**_VALID_DCP_INSTANCE, "status": "PROPOSED"}
        assert errors(SCHEMA, instance) == []

    def test_optional_status_active(self):
        instance = {**_VALID_DCP_INSTANCE, "status": "ACTIVE"}
        assert errors(SCHEMA, instance) == []

    def test_optional_status_deprecated(self):
        instance = {**_VALID_DCP_INSTANCE, "status": "DEPRECATED"}
        assert errors(SCHEMA, instance) == []

    def test_optional_compatible_pcp_core_versions(self):
        instance = {**_VALID_DCP_INSTANCE, "compatible_pcp_core_versions": ["pcp.core.v0"]}
        assert errors(SCHEMA, instance) == []

    def test_non_empty_capabilities_arrays(self):
        caps = {
            **_VALID_CAPABILITIES,
            "authority_map_contributions": ["pm.tasks.read"],
            "red_lane_contributions": ["pm.tasks.red"],
            "evidence_export_sections": ["pm_evidence"],
            "proof_status_mappings": ["pm.proof.v0"],
            "runtime_mappings": ["pm.runtime.v0"],
            "adapter_mappings": ["pm.adapter.v0"],
        }
        instance = {**_VALID_DCP_INSTANCE, "capabilities": caps}
        assert errors(SCHEMA, instance) == []


# ---------------------------------------------------------------------------
# 3. Fail-closed invariant rejections
# ---------------------------------------------------------------------------
class TestInvariantRejections:
    def _instance_with_invariant(self, key: str, value: object) -> dict:
        inv = {**_VALID_INVARIANTS, key: value}
        return {**_VALID_DCP_INSTANCE, "invariants": inv}

    def test_rejects_cannot_override_core_fail_closed_false(self):
        instance = self._instance_with_invariant("cannot_override_core_fail_closed", False)
        assert errors(SCHEMA, instance), "Expected rejection: cannot_override_core_fail_closed=False"

    def test_rejects_cannot_weaken_proof_gates_false(self):
        instance = self._instance_with_invariant("cannot_weaken_proof_gates", False)
        assert errors(SCHEMA, instance), "Expected rejection: cannot_weaken_proof_gates=False"

    def test_rejects_cannot_weaken_audit_gates_false(self):
        instance = self._instance_with_invariant("cannot_weaken_audit_gates", False)
        assert errors(SCHEMA, instance), "Expected rejection: cannot_weaken_audit_gates=False"

    def test_rejects_cannot_promote_adapter_to_authority_false(self):
        instance = self._instance_with_invariant("cannot_promote_adapter_to_authority", False)
        assert errors(SCHEMA, instance), "Expected rejection: cannot_promote_adapter_to_authority=False"

    def test_rejects_cannot_require_extension_for_baseline_core_false(self):
        instance = self._instance_with_invariant("cannot_require_extension_for_baseline_core", False)
        assert errors(SCHEMA, instance), "Expected rejection: cannot_require_extension_for_baseline_core=False"

    def test_rejects_invariant_string_true(self):
        """String 'true' is not boolean true — const:true must reject it."""
        instance = self._instance_with_invariant("cannot_override_core_fail_closed", "true")
        assert errors(SCHEMA, instance), "Expected rejection for string 'true' in invariant"

    def test_rejects_invariant_integer_one(self):
        """Integer 1 is not boolean true — const:true must reject it."""
        instance = self._instance_with_invariant("cannot_weaken_proof_gates", 1)
        assert errors(SCHEMA, instance), "Expected rejection for integer 1 in invariant"

    def test_rejects_extra_invariant_key(self):
        """additionalProperties false on invariants block rejects unknown keys."""
        inv = {**_VALID_INVARIANTS, "sneaky_override": True}
        instance = {**_VALID_DCP_INSTANCE, "invariants": inv}
        assert errors(SCHEMA, instance), "Expected rejection for extra invariant key"


# ---------------------------------------------------------------------------
# 4. Extension kind rejections
# ---------------------------------------------------------------------------
class TestExtensionKindRejections:
    def test_rejects_typo_dopmux_dcp(self):
        """'DOPMUX_DCP' is a typo — not in the enum — must be rejected."""
        instance = {**_VALID_DCP_INSTANCE, "extension_kind": "DOPMUX_DCP"}
        assert errors(SCHEMA, instance), "Expected rejection for typo 'DOPMUX_DCP'"

    def test_rejects_lowercase_extension_kind(self):
        instance = {**_VALID_DCP_INSTANCE, "extension_kind": "dopemux_dcp"}
        assert errors(SCHEMA, instance), "Expected rejection for lowercase extension_kind"

    def test_rejects_arbitrary_extension_kind(self):
        instance = {**_VALID_DCP_INSTANCE, "extension_kind": "CUSTOM_EXTENSION"}
        assert errors(SCHEMA, instance), "Expected rejection for arbitrary extension_kind"

    def test_rejects_missing_extension_kind(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "extension_kind"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'extension_kind'"


# ---------------------------------------------------------------------------
# 5. Required top-level key rejections
# ---------------------------------------------------------------------------
class TestRequiredKeyRejections:
    def test_rejects_missing_schema_version(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "schema_version"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'schema_version'"

    def test_rejects_wrong_schema_version(self):
        instance = {**_VALID_DCP_INSTANCE, "schema_version": "pcp.extension_manifest.v1"}
        assert errors(SCHEMA, instance), "Expected rejection for wrong schema_version const"

    def test_rejects_missing_extension_id(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "extension_id"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'extension_id'"

    def test_rejects_missing_extension_identity(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "extension_identity"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'extension_identity'"

    def test_rejects_missing_capabilities(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "capabilities"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'capabilities'"

    def test_rejects_missing_schemas(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "schemas"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'schemas'"

    def test_rejects_missing_invariants(self):
        instance = {k: v for k, v in _VALID_DCP_INSTANCE.items() if k != "invariants"}
        assert errors(SCHEMA, instance), "Expected rejection for missing 'invariants'"


# ---------------------------------------------------------------------------
# 6. additionalProperties rejections
# ---------------------------------------------------------------------------
class TestAdditionalPropertiesRejections:
    def test_rejects_extra_top_level_key(self):
        instance = {**_VALID_DCP_INSTANCE, "rogue_top_level": "bad"}
        assert errors(SCHEMA, instance), "Expected rejection for extra top-level key"

    def test_rejects_extra_capabilities_key(self):
        caps = {**_VALID_CAPABILITIES, "undeclared_cap": []}
        instance = {**_VALID_DCP_INSTANCE, "capabilities": caps}
        assert errors(SCHEMA, instance), "Expected rejection for extra capabilities key"

    def test_rejects_extra_schemas_key(self):
        schemas = {**_VALID_SCHEMAS, "sneaky_schema_list": []}
        instance = {**_VALID_DCP_INSTANCE, "schemas": schemas}
        assert errors(SCHEMA, instance), "Expected rejection for extra schemas key"

    def test_rejects_extra_extension_identity_key(self):
        identity = {**_VALID_EXTENSION_IDENTITY, "extra_hint": "nope"}
        instance = {**_VALID_DCP_INSTANCE, "extension_identity": identity}
        assert errors(SCHEMA, instance), "Expected rejection for extra extension_identity key"

    def test_rejects_status_not_in_enum(self):
        """'ACTIVE_BETA' is not in the status enum."""
        instance = {**_VALID_DCP_INSTANCE, "status": "ACTIVE_BETA"}
        assert errors(SCHEMA, instance), "Expected rejection for status='ACTIVE_BETA'"


# ---------------------------------------------------------------------------
# 7. Hardened schema: new rejection tests
# ---------------------------------------------------------------------------
class TestHardenedSchemaRejections:
    def test_rejects_empty_string_extension_id(self):
        """extension_id now has minLength:1; empty string must be rejected."""
        instance = {**_VALID_DCP_INSTANCE, "extension_id": ""}
        assert errors(SCHEMA, instance), "Expected rejection for empty string extension_id"
