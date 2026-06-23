"""Contract validation for DCP extension manifest and authority map."""

from __future__ import annotations

import json
import pathlib

from jsonschema import Draft202012Validator

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

pairs = [
    (
        _REPO_ROOT / "schemas" / "dcp_extension" / "proof_family.schema.json",
        _REPO_ROOT / "schemas" / "dcp_extension" / "proof_family.dcp.json",
    ),
    (
        _REPO_ROOT / "schemas" / "project_control_plane" / "extension_manifest.schema.json",
        _REPO_ROOT / "schemas" / "dcp_extension" / "extension_manifest.dcp.json",
    ),
    (
        _REPO_ROOT / "schemas" / "project_control_plane" / "authority_map.schema.json",
        _REPO_ROOT / "schemas" / "dcp_extension" / "authority_map.dcp.json",
    ),
]


def test_dcp_extension_contract_pairs_validate():
    for schema_path, inst_path in pairs:
        schema = json.loads(schema_path.read_text())
        inst = json.loads(inst_path.read_text())
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(inst))
        assert errors == [], f"{inst_path}: {errors}"