"""
DCP Core Contract Tests — TP-DCP-0001

Assertions:
  (a) Schema round-trip: each fixture instance validates against its schema.
  (b) Provenance presence-lint (SEPARATE from round-trip): every schema and every
      fixture instance carries provenance+validation blocks.
  (c) External/invented contracts carry validation_state == PROVISIONAL_UNVERIFIED_ENFORCEMENT.
  (d) dcp_proof_pointer: auditor_verdict and validation_state are DISTINCT fields in the schema.
  (e) Defer guard: schemas/dcp/ does NOT contain dcp_mutation_class, dcp_approval_artifact,
      dcp_project_resource_map schemas.

Run modes:
  python3 tests/dcp/test_dcp_contracts.py
  python3 -m pytest tests/dcp -q
"""
import json
import sys
import os
from pathlib import Path

# Resolve paths relative to THIS file so that both invocation modes work:
#   python3 tests/dcp/test_dcp_contracts.py   (from repo root)
#   python3 -m pytest tests/dcp -q            (pytest sets cwd to repo root)
_THIS_DIR = Path(__file__).resolve().parent
_FIXTURES_DIR = _THIS_DIR / "fixtures"
_SCHEMAS_DIR = _THIS_DIR.parent.parent / "schemas" / "dcp"

try:
    import jsonschema
    from jsonschema import Draft7Validator, validate as _jsonschema_validate
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

# ---------------------------------------------------------------------------
# Helper: load JSON safely
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Contract / schema registry
# ---------------------------------------------------------------------------

# Maps fixture key → schema filename (without directory)
_CONTRACT_REGISTRY = {
    "dcp_red_lane_taxonomy": "dcp_red_lane_taxonomy.schema.json",
    "dcp_control_snapshot": "dcp_control_snapshot.schema.json",
    "dcp_proof_pointer": "dcp_proof_pointer.schema.json",
    "dcp_evidence_hit": "dcp_evidence_hit.schema.json",
    "dcp_chronicle_receipt": "dcp_chronicle_receipt.schema.json",
    "dcp_helper_receipt": "dcp_helper_receipt.schema.json",
}

# Contracts that are EXTERNAL_PROPOSED or SYNTHESIS_INVENTED must carry
# validation_state == PROVISIONAL_UNVERIFIED_ENFORCEMENT in their fixture.
_EXTERNAL_OR_INVENTED_CONTRACTS = {
    "dcp_control_snapshot",
    "dcp_proof_pointer",
    "dcp_evidence_hit",
    "dcp_chronicle_receipt",
    "dcp_helper_receipt",
}

# Deferred contract schema names that must NOT exist in schemas/dcp/
_DEFERRED_SCHEMA_STEMS = {
    "dcp_mutation_class",
    "dcp_approval_artifact",
    "dcp_project_resource_map",
}


# ---------------------------------------------------------------------------
# (a) Schema round-trip: fixture instances validate against their schemas
# ---------------------------------------------------------------------------

def test_schema_round_trip():
    """(a) Each fixture instance validates against its corresponding .v0 schema."""
    assert _HAS_JSONSCHEMA, "jsonschema is required for round-trip tests; install it."

    fixture_path = _FIXTURES_DIR / "dcp_core_fixture.json"
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    fixture = _load_json(fixture_path)

    errors = []
    for contract_key, schema_filename in _CONTRACT_REGISTRY.items():
        schema_path = _SCHEMAS_DIR / schema_filename
        assert schema_path.exists(), f"Schema not found: {schema_path}"

        schema = _load_json(schema_path)

        assert contract_key in fixture, (
            f"Fixture is missing instance for contract '{contract_key}'"
        )
        instance = fixture[contract_key]

        try:
            validator = Draft7Validator(schema)
            validation_errors = list(validator.iter_errors(instance))
            if validation_errors:
                for ve in validation_errors:
                    errors.append(
                        f"[{contract_key}] JSONSchema validation error at "
                        f"'{'/'.join(str(p) for p in ve.absolute_path)}': {ve.message}"
                    )
        except Exception as exc:
            errors.append(f"[{contract_key}] Unexpected validation exception: {exc}")

    assert not errors, "Round-trip failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# (b) Provenance presence-lint (SEPARATE from round-trip)
# ---------------------------------------------------------------------------

def test_provenance_presence_lint():
    """
    (b) SEPARATE from round-trip. Every schema and every fixture instance
    carries both 'provenance' (with 'tag' and 'source_ref') and 'validation'
    (with 'state' and 'notes') blocks.
    """
    errors = []

    # Check each schema file
    for contract_key, schema_filename in _CONTRACT_REGISTRY.items():
        schema_path = _SCHEMAS_DIR / schema_filename
        assert schema_path.exists(), f"Schema not found: {schema_path}"
        schema = _load_json(schema_path)

        # Every schema must declare 'provenance' and 'validation' in 'properties'
        props = schema.get("properties", {})
        if "provenance" not in props:
            errors.append(f"[schema:{contract_key}] Missing 'provenance' property declaration.")
        else:
            prov_props = props["provenance"].get("properties", {})
            if "tag" not in prov_props:
                errors.append(f"[schema:{contract_key}] provenance missing 'tag' sub-property.")
            if "source_ref" not in prov_props:
                errors.append(f"[schema:{contract_key}] provenance missing 'source_ref' sub-property.")

        if "validation" not in props:
            errors.append(f"[schema:{contract_key}] Missing 'validation' property declaration.")
        else:
            val_props = props["validation"].get("properties", {})
            if "state" not in val_props:
                errors.append(f"[schema:{contract_key}] validation missing 'state' sub-property.")
            if "notes" not in val_props:
                errors.append(f"[schema:{contract_key}] validation missing 'notes' sub-property.")

        # 'provenance' and 'validation' must be in 'required'
        required = schema.get("required", [])
        if "provenance" not in required:
            errors.append(f"[schema:{contract_key}] 'provenance' not in schema 'required'.")
        if "validation" not in required:
            errors.append(f"[schema:{contract_key}] 'validation' not in schema 'required'.")

    # Check each fixture instance
    fixture_path = _FIXTURES_DIR / "dcp_core_fixture.json"
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
    fixture = _load_json(fixture_path)

    for contract_key in _CONTRACT_REGISTRY:
        if contract_key not in fixture:
            errors.append(f"[fixture:{contract_key}] Missing fixture instance.")
            continue
        instance = fixture[contract_key]

        # Check provenance block
        if "provenance" not in instance:
            errors.append(f"[fixture:{contract_key}] Missing 'provenance' block.")
        else:
            prov = instance["provenance"]
            if "tag" not in prov or not prov["tag"]:
                errors.append(f"[fixture:{contract_key}] provenance.tag missing or empty.")
            if "source_ref" not in prov or not prov["source_ref"]:
                errors.append(f"[fixture:{contract_key}] provenance.source_ref missing or empty.")

        # Check validation block
        if "validation" not in instance:
            errors.append(f"[fixture:{contract_key}] Missing 'validation' block.")
        else:
            val = instance["validation"]
            if "state" not in val or not val["state"]:
                errors.append(f"[fixture:{contract_key}] validation.state missing or empty.")
            if "notes" not in val or not val["notes"]:
                errors.append(f"[fixture:{contract_key}] validation.notes missing or empty.")

    assert not errors, "Provenance presence-lint failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# (c) External/invented contracts carry PROVISIONAL_UNVERIFIED_ENFORCEMENT
# ---------------------------------------------------------------------------

def test_external_invented_contracts_are_provisional():
    """
    (c) EXTERNAL_PROPOSED and SYNTHESIS_INVENTED contracts must carry
    validation_state == 'PROVISIONAL_UNVERIFIED_ENFORCEMENT' in their
    fixture instances (checked at both validation.state and top-level
    validation_state where applicable).
    """
    fixture_path = _FIXTURES_DIR / "dcp_core_fixture.json"
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
    fixture = _load_json(fixture_path)

    errors = []
    for contract_key in _EXTERNAL_OR_INVENTED_CONTRACTS:
        if contract_key not in fixture:
            errors.append(f"[fixture:{contract_key}] Missing fixture instance.")
            continue
        instance = fixture[contract_key]

        # Check validation.state in the standard block
        val_block = instance.get("validation", {})
        state = val_block.get("state", "")
        if state != "PROVISIONAL_UNVERIFIED_ENFORCEMENT":
            errors.append(
                f"[fixture:{contract_key}] validation.state is '{state}'; "
                f"expected 'PROVISIONAL_UNVERIFIED_ENFORCEMENT' for external/invented contract."
            )

        # Also check top-level validation_state if the schema uses it as a sibling field
        if "validation_state" in instance:
            top_state = instance["validation_state"]
            if top_state != "PROVISIONAL_UNVERIFIED_ENFORCEMENT":
                errors.append(
                    f"[fixture:{contract_key}] top-level validation_state is '{top_state}'; "
                    f"expected 'PROVISIONAL_UNVERIFIED_ENFORCEMENT'."
                )

    assert not errors, "Provisional state failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# (d) dcp_proof_pointer: auditor_verdict and validation_state are DISTINCT fields
# ---------------------------------------------------------------------------

def test_proof_pointer_auditor_verdict_distinct_from_validation_state():
    """
    (d) In dcp_proof_pointer schema: auditor_verdict and validation_state must be
    DISTINCT sibling fields (not aliases, not proxies, not the same field).
    Both must be declared in 'properties' and in 'required'.
    """
    schema_path = _SCHEMAS_DIR / "dcp_proof_pointer.schema.json"
    assert schema_path.exists(), f"Schema not found: {schema_path}"
    schema = _load_json(schema_path)

    props = schema.get("properties", {})
    required = schema.get("required", [])

    assert "auditor_verdict" in props, (
        "dcp_proof_pointer schema: 'auditor_verdict' not declared in 'properties'. "
        "Must be a distinct field from 'validation_state'."
    )
    assert "validation_state" in props, (
        "dcp_proof_pointer schema: 'validation_state' not declared in 'properties'. "
        "Must be a distinct field from 'auditor_verdict'."
    )

    assert "auditor_verdict" in required, (
        "dcp_proof_pointer schema: 'auditor_verdict' not in 'required'."
    )
    assert "validation_state" in required, (
        "dcp_proof_pointer schema: 'validation_state' not in 'required'."
    )

    # They must be distinct: not the same object reference (trivially true for JSON load),
    # and must have different descriptions/semantics.
    av_desc = props["auditor_verdict"].get("description", "")
    vs_desc = props["validation_state"].get("description", "")

    assert av_desc != vs_desc or (av_desc == "" and vs_desc == ""), (
        "auditor_verdict and validation_state have identical descriptions — "
        "they may be proxies of each other. Ensure they carry distinct semantics."
    )

    # Verify in fixture that both fields are present and have different values
    fixture_path = _FIXTURES_DIR / "dcp_core_fixture.json"
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
    fixture = _load_json(fixture_path)

    assert "dcp_proof_pointer" in fixture, "Fixture missing dcp_proof_pointer instance."
    pp = fixture["dcp_proof_pointer"]

    assert "auditor_verdict" in pp, (
        "Fixture dcp_proof_pointer: missing 'auditor_verdict' field."
    )
    assert "validation_state" in pp, (
        "Fixture dcp_proof_pointer: missing 'validation_state' field."
    )

    assert pp["auditor_verdict"] != pp["validation_state"], (
        f"Fixture dcp_proof_pointer: auditor_verdict ('{pp['auditor_verdict']}') must not "
        f"equal validation_state ('{pp['validation_state']}') — they are DISTINCT fields."
    )


# ---------------------------------------------------------------------------
# (e) Defer guard: deferred contracts MUST NOT be present in schemas/dcp/
# ---------------------------------------------------------------------------

def test_deferred_contracts_absent():
    """
    (e) The three deferred contracts (dcp_mutation_class, dcp_approval_artifact,
    dcp_project_resource_map) must NOT have schema files in schemas/dcp/.
    Locking any of these without direct repo derivation stops the packet.
    """
    assert _SCHEMAS_DIR.exists(), f"Schema directory not found: {_SCHEMAS_DIR}"

    present_deferred = []
    for schema_file in _SCHEMAS_DIR.glob("*.schema.json"):
        stem = schema_file.stem.replace(".schema", "")
        if stem in _DEFERRED_SCHEMA_STEMS:
            present_deferred.append(str(schema_file))

    assert not present_deferred, (
        "Deferred contracts found in schemas/dcp/ — this stops the packet:\n"
        + "\n".join(present_deferred)
    )


# ---------------------------------------------------------------------------
# (b2) Per-field provenance coverage lint
#      Every data field in a fixture instance must appear as a key in
#      field_provenance. "Meta" fields (schema_version, provenance, validation,
#      field_provenance) are exempt. dcp_red_lane_taxonomy is handled separately
#      via per-lane provenance_tag.
# ---------------------------------------------------------------------------

# Contracts that carry a flat `field_provenance` dict (excludes red_lane_taxonomy
# which uses per-lane provenance_tag instead)
_FIELD_PROVENANCE_CONTRACTS = {
    "dcp_control_snapshot",
    "dcp_proof_pointer",
    "dcp_evidence_hit",
    "dcp_chronicle_receipt",
    "dcp_helper_receipt",
}

# Fields exempt from field_provenance coverage (structural / meta fields)
_META_FIELDS = {"schema_version", "provenance", "validation", "field_provenance"}


def test_per_field_provenance_coverage():
    """
    (b2) Per-field provenance coverage (SEPARATE from schema round-trip and from
    contract-level presence-lint).

    For every contract that uses a field_provenance dict: every data field in
    the fixture instance (instance.keys() - meta-set) must appear as a key in
    instance['field_provenance']. Values must be non-empty strings.

    For dcp_red_lane_taxonomy: every lane entry must have a non-empty provenance_tag.

    This test implements the REV1 §10 acceptance gate: 'every field ... tagged';
    it is structurally distinct from test_schema_round_trip (which only confirms
    jsonschema validity) and test_provenance_presence_lint (which only confirms
    the contract-level blocks exist).
    """
    fixture_path = _FIXTURES_DIR / "dcp_core_fixture.json"
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
    fixture = _load_json(fixture_path)

    errors = []

    # --- contracts with flat field_provenance ---
    for contract_key in _FIELD_PROVENANCE_CONTRACTS:
        if contract_key not in fixture:
            errors.append(f"[fixture:{contract_key}] Missing fixture instance.")
            continue
        instance = fixture[contract_key]

        fp = instance.get("field_provenance")
        if not isinstance(fp, dict):
            errors.append(
                f"[fixture:{contract_key}] 'field_provenance' is missing or not a dict."
            )
            continue

        data_fields = set(instance.keys()) - _META_FIELDS
        for field in data_fields:
            if field not in fp:
                errors.append(
                    f"[fixture:{contract_key}] Data field '{field}' is absent from "
                    f"field_provenance. Every data field must be tagged."
                )
            elif not isinstance(fp[field], str) or not fp[field].strip():
                errors.append(
                    f"[fixture:{contract_key}] field_provenance['{field}'] is empty "
                    f"or not a non-empty string."
                )

    # --- dcp_red_lane_taxonomy: per-lane provenance_tag ---
    if "dcp_red_lane_taxonomy" not in fixture:
        errors.append("[fixture:dcp_red_lane_taxonomy] Missing fixture instance.")
    else:
        lanes = fixture["dcp_red_lane_taxonomy"].get("lanes", [])
        if not lanes:
            errors.append(
                "[fixture:dcp_red_lane_taxonomy] 'lanes' list is empty or missing."
            )
        for i, lane in enumerate(lanes):
            pt = lane.get("provenance_tag", "")
            if not pt:
                errors.append(
                    f"[fixture:dcp_red_lane_taxonomy] Lane[{i}] id='{lane.get('id', '?')}' "
                    f"has empty or missing provenance_tag."
                )

    assert not errors, "Per-field provenance coverage failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Additional sanity: schema_version const ends .v0
# ---------------------------------------------------------------------------

def test_all_schemas_have_v0_version():
    """Sanity: every schema declares schema_version with a const value ending '.v0'."""
    errors = []
    for contract_key, schema_filename in _CONTRACT_REGISTRY.items():
        schema_path = _SCHEMAS_DIR / schema_filename
        assert schema_path.exists(), f"Schema not found: {schema_path}"
        schema = _load_json(schema_path)

        props = schema.get("properties", {})
        sv_prop = props.get("schema_version", {})
        const_val = sv_prop.get("const", "")
        if not const_val.endswith(".v0"):
            errors.append(
                f"[schema:{contract_key}] schema_version const '{const_val}' "
                f"does not end with '.v0'."
            )

    assert not errors, "schema_version .v0 check failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# __main__ runner — allows python3 tests/dcp/test_dcp_contracts.py
# ---------------------------------------------------------------------------

def _run_all_tests():
    tests = [
        ("(a) schema_round_trip", test_schema_round_trip),
        ("(b) provenance_presence_lint", test_provenance_presence_lint),
        ("(b2) per_field_provenance_coverage", test_per_field_provenance_coverage),
        ("(c) external_invented_contracts_are_provisional", test_external_invented_contracts_are_provisional),
        ("(d) proof_pointer_auditor_verdict_distinct", test_proof_pointer_auditor_verdict_distinct_from_validation_state),
        ("(e) deferred_contracts_absent", test_deferred_contracts_absent),
        ("sanity: all_schemas_have_v0_version", test_all_schemas_have_v0_version),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL  {name}")
            print(f"        {exc}")
            failed += 1
        except Exception as exc:
            print(f"  ERROR {name}")
            print(f"        {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\n{passed + failed} tests: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    print("DCP Core Contract Tests — TP-DCP-0001")
    print(f"  schemas dir : {_SCHEMAS_DIR}")
    print(f"  fixtures dir: {_FIXTURES_DIR}")
    print()
    if not _HAS_JSONSCHEMA:
        print("WARNING: jsonschema not installed — round-trip test (a) will be skipped.")
        print()
    failed_count = _run_all_tests()
    sys.exit(1 if failed_count > 0 else 0)
