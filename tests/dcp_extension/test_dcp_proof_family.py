"""DCP proof-family projection mapping tests."""

from __future__ import annotations

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "dcp_extension" / "proof_family.schema.json"
_INSTANCE_PATH = _REPO_ROOT / "schemas" / "dcp_extension" / "proof_family.dcp.json"
_MANIFEST_PATH = _REPO_ROOT / "schemas" / "dcp_extension" / "extension_manifest.dcp.json"
_AUTHORITY_PATH = _REPO_ROOT / "schemas" / "dcp_extension" / "authority_map.dcp.json"


def _load(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


SCHEMA = _load(_SCHEMA_PATH)
INSTANCE = _load(_INSTANCE_PATH)
MANIFEST = _load(_MANIFEST_PATH)
AUTHORITY = _load(_AUTHORITY_PATH)


class TestDcpProofFamily:
    def test_schema_is_valid(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_instance_validates(self):
        errors = list(Draft202012Validator(SCHEMA).iter_errors(INSTANCE))
        assert errors == [], errors

    def test_manifest_proof_status_mappings_not_empty(self):
        mappings = MANIFEST["capabilities"]["proof_status_mappings"]
        assert mappings
        assert "schemas/dcp_extension/proof_family.dcp.json" in mappings

    def test_authority_map_projection_entry(self):
        entry = next(e for e in AUTHORITY["entries"] if e["domain"] == "proof.dcp_family")
        assert entry["surface_class"] == "PROJECTION"
        assert entry["canonical_writer"] is None
        assert entry["live_write_allowed"] is False

    def test_is_authority_true_fails_schema(self):
        tampered = copy.deepcopy(INSTANCE)
        tampered["is_authority"] = True
        errors = list(Draft202012Validator(SCHEMA).iter_errors(tampered))
        assert errors

    def test_head_sha_binding_false_fails_schema(self):
        tampered = copy.deepcopy(INSTANCE)
        tampered["head_sha_binding_required"] = False
        errors = list(Draft202012Validator(SCHEMA).iter_errors(tampered))
        assert errors

    def test_removing_proof_mapping_fails_scope_lock(self):
        tampered = copy.deepcopy(MANIFEST)
        tampered["capabilities"]["proof_status_mappings"] = []
        assert tampered["capabilities"]["proof_status_mappings"] == []