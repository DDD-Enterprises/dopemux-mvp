import json, pathlib
from jsonschema import Draft202012Validator
ROOT = pathlib.Path(__file__).resolve().parents[2]
def _load(p): return json.loads((ROOT / p).read_text())

def test_manifest_declares_proof_status_mapping():
    m = _load("schemas/dcp_extension/extension_manifest.dcp.json")
    assert "schemas/dcp_extension/proof_status_map.dcp.json" in m["capabilities"]["proof_status_mappings"]

def test_proof_pointers_validate_against_pcp_schema():
    schema = _load("schemas/project_control_plane/proof_pointer.schema.json")
    v = Draft202012Validator(schema)
    artifact = _load("schemas/dcp_extension/proof_status_map.dcp.json")
    ptrs = artifact["proof_pointers"]
    assert ptrs, "proof mapping must be non-empty"
    for p in ptrs:
        assert not list(v.iter_errors(p))

def test_authority_map_has_proof_domain():
    am = _load("schemas/dcp_extension/authority_map.dcp.json")
    e = next(x for x in am["entries"] if x["domain"] == "proof.dopemux_family")
    assert e["canonical_writer"] is None and e["live_write_allowed"] is False and e["surface_class"] == "ADAPTER"
