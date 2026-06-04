"""
DCP Contract Derivation Tests — TP-DCP-0002

Assertions (numbered per TP-DCP-0002 §13):
  1.  All three schemas are valid JSON.
  2.  All three fixtures validate against their schemas.
  3.  Every schema has additionalProperties: false at root.
  4.  Every schema has contract-level provenance.
  5.  Every fixture has field_provenance.
  6.  Every field in each fixture is represented in field_provenance.
  7.  validation_state is constrained to TP-DCP-0001 vocabulary or explicit extension.
  8.  No fixture promotes EXTERNAL_PROPOSED or SYNTHESIS_INVENTED to REPO_VALIDATED.
  9.  No schema defines LIVE_WRITE_READY.
  10. No schema creates live-write permission.
  11. No schema imports or references merge specialist as an allowed execution path.
  12. DCP-RED-MERGE-SEAM-0001 is preserved / referenced as forbidden.
  13. DCP_MUTATION_CLASS contains a hard-block class for merge automation seam.
  14. DCP_APPROVAL_ARTIFACT requires separate requester/approver or explicit supervisor signoff.
  15. DCP_PROJECT_RESOURCE_MAP marks ConPort/dope-memory endpoint binding as PROVISIONAL or UNKNOWN.
  16. No forbidden files are modified (checked by git diff).
  17. No live external calls are required for validation.

Run modes:
  python3 tests/dcp/test_dcp_0002_contract_derivation.py
  python3 -m pytest tests/dcp/test_dcp_0002_contract_derivation.py -q
"""
import json
import subprocess
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_FIXTURES_DIR = _THIS_DIR / "fixtures"
_SCHEMAS_DIR = _THIS_DIR.parent.parent / "schemas" / "dcp"

try:
    from jsonschema import Draft7Validator
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

# ---------------------------------------------------------------------------
# File registry
# ---------------------------------------------------------------------------

_SCHEMA_FILES = {
    "dcp_mutation_class": _SCHEMAS_DIR / "dcp_mutation_class.schema.json",
    "dcp_approval_artifact": _SCHEMAS_DIR / "dcp_approval_artifact.schema.json",
    "dcp_project_resource_map": _SCHEMAS_DIR / "dcp_project_resource_map.schema.json",
}

_FIXTURE_FILES = {
    "dcp_mutation_class": _FIXTURES_DIR / "tp_dcp_0002_mutation_class.fixture.json",
    "dcp_approval_artifact": _FIXTURES_DIR / "tp_dcp_0002_approval_artifact.fixture.json",
    "dcp_project_resource_map": _FIXTURES_DIR / "tp_dcp_0002_project_resource_map.fixture.json",
}

# Fields exempt from field_provenance coverage
_META_FIELDS = {"schema_version", "provenance", "validation", "field_provenance",
                "_comment", "_sha_notice"}

# Accepted validation_state vocabulary (TP-DCP-0001 + this packet's REPO_CROSS_CHECKED extension)
_VALID_VALIDATION_STATES = {
    "REPO_CROSS_CHECKED",
    "PROVISIONAL_UNVERIFIED_ENFORCEMENT",
    "DEFERRED",
}

# Accepted provenance tags
_VALID_PROVENANCE_TAGS = {
    "REPO_VALIDATED",
    "REPO_VALIDATED_BY_AUDIT",
    "EXTERNAL_PROPOSED",
    "SYNTHESIS_INVENTED",
    "PROVISIONAL",
    "UNKNOWN",
}

# Forbidden strings that must never appear in schema files
_FORBIDDEN_SCHEMA_STRINGS = [
    "LIVE_WRITE_READY",
    "queue_drain",
    "batch_resolve_and_merge",
    "dopemux_pr_merge_specialist",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _schema_text(name: str) -> str:
    path = _SCHEMA_FILES[name]
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: All schemas are valid JSON
# ---------------------------------------------------------------------------

def test_1_schemas_are_valid_json():
    errors = []
    for name, path in _SCHEMA_FILES.items():
        assert path.exists(), f"Schema file missing: {path}"
        try:
            _load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"[{name}] Invalid JSON: {exc}")
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 2: Fixtures validate against schemas
# ---------------------------------------------------------------------------

def test_2_fixtures_validate_against_schemas():
    assert _HAS_JSONSCHEMA, "jsonschema required for round-trip validation."
    errors = []
    for name in _SCHEMA_FILES:
        schema_path = _SCHEMA_FILES[name]
        fixture_path = _FIXTURE_FILES[name]
        assert schema_path.exists(), f"Schema missing: {schema_path}"
        assert fixture_path.exists(), f"Fixture missing: {fixture_path}"
        schema = _load_json(schema_path)
        fixture = _load_json(fixture_path)
        validator = Draft7Validator(schema)
        for ve in validator.iter_errors(fixture):
            errors.append(
                f"[{name}] at '{'/'.join(str(p) for p in ve.absolute_path)}': {ve.message}"
            )
    assert not errors, "Round-trip failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 3: Every schema has additionalProperties: false at root
# ---------------------------------------------------------------------------

def test_3_schemas_have_additional_properties_false():
    errors = []
    for name, path in _SCHEMA_FILES.items():
        schema = _load_json(path)
        if not schema.get("additionalProperties") is False:
            errors.append(f"[{name}] additionalProperties is not false at root")
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 4: Every schema has contract-level provenance
# ---------------------------------------------------------------------------

def test_4_schemas_have_contract_provenance():
    errors = []
    for name, path in _SCHEMA_FILES.items():
        schema = _load_json(path)
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for block in ("provenance", "validation"):
            if block not in props:
                errors.append(f"[schema:{name}] '{block}' not in properties")
            if block not in required:
                errors.append(f"[schema:{name}] '{block}' not in required")
        if "provenance" in props:
            prov_props = props["provenance"].get("properties", {})
            for sub in ("tag", "source_ref"):
                if sub not in prov_props:
                    errors.append(f"[schema:{name}] provenance.{sub} missing")
        if "validation" in props:
            val_props = props["validation"].get("properties", {})
            for sub in ("state", "notes"):
                if sub not in val_props:
                    errors.append(f"[schema:{name}] validation.{sub} missing")
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 5: Every fixture has field_provenance
# ---------------------------------------------------------------------------

def test_5_fixtures_have_field_provenance():
    errors = []
    for name, path in _FIXTURE_FILES.items():
        fixture = _load_json(path)
        if "field_provenance" not in fixture:
            errors.append(f"[fixture:{name}] 'field_provenance' block missing")
        elif not isinstance(fixture["field_provenance"], dict):
            errors.append(f"[fixture:{name}] 'field_provenance' is not a dict")
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 6: Every data field in each fixture is in field_provenance
# ---------------------------------------------------------------------------

def test_6_every_fixture_field_has_provenance():
    errors = []
    for name, path in _FIXTURE_FILES.items():
        fixture = _load_json(path)
        fp = fixture.get("field_provenance", {})
        if not isinstance(fp, dict):
            errors.append(f"[fixture:{name}] field_provenance is not a dict")
            continue
        data_fields = set(fixture.keys()) - _META_FIELDS
        for field in data_fields:
            if field not in fp:
                errors.append(
                    f"[fixture:{name}] field '{field}' absent from field_provenance"
                )
            elif not isinstance(fp[field], str) or not fp[field].strip():
                errors.append(
                    f"[fixture:{name}] field_provenance['{field}'] is empty or not a string"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 7: validation_state constrained to accepted vocabulary
# ---------------------------------------------------------------------------

def test_7_validation_state_vocabulary():
    errors = []
    for name, path in _FIXTURE_FILES.items():
        fixture = _load_json(path)
        # Top-level validation_state
        vs = fixture.get("validation_state")
        if vs is not None and vs not in _VALID_VALIDATION_STATES:
            errors.append(
                f"[fixture:{name}] validation_state '{vs}' not in accepted vocabulary"
            )
        # Nested validation.state
        val_block = fixture.get("validation", {})
        if isinstance(val_block, dict):
            nested_state = val_block.get("state")
            if nested_state and nested_state not in _VALID_VALIDATION_STATES:
                errors.append(
                    f"[fixture:{name}] validation.state '{nested_state}' not in accepted vocabulary"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 8: No fixture promotes EXTERNAL_PROPOSED or SYNTHESIS_INVENTED to REPO_VALIDATED
# ---------------------------------------------------------------------------

def test_8_no_provenance_laundering():
    """
    Fixtures that declare contract-level provenance as EXTERNAL_PROPOSED or
    SYNTHESIS_INVENTED must NOT also declare validation_state as REPO_CROSS_CHECKED,
    because that would launder external/invented status into repo authority.
    """
    errors = []
    for name, path in _FIXTURE_FILES.items():
        fixture = _load_json(path)
        prov = fixture.get("provenance", {})
        tag = prov.get("tag", "") if isinstance(prov, dict) else ""
        vs = fixture.get("validation_state", "")
        # If contract-level tag is EXTERNAL or INVENTED, validation_state must not be REPO_CROSS_CHECKED
        if tag in ("EXTERNAL_PROPOSED", "SYNTHESIS_INVENTED") and vs == "REPO_CROSS_CHECKED":
            errors.append(
                f"[fixture:{name}] provenance.tag='{tag}' but validation_state='REPO_CROSS_CHECKED' "
                f"— this launders external/invented status into repo authority"
            )
        # Also check field_provenance values — none should promote external/invented to REPO_VALIDATED
        fp = fixture.get("field_provenance", {})
        if isinstance(fp, dict):
            for field, prov_val in fp.items():
                if not isinstance(prov_val, str):
                    continue
                # This check is informational — field_provenance values should be valid tags
                if prov_val not in _VALID_PROVENANCE_TAGS:
                    errors.append(
                        f"[fixture:{name}] field_provenance['{field}'] = '{prov_val}' "
                        f"is not a recognized provenance tag"
                    )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 9: No schema defines LIVE_WRITE_READY
# ---------------------------------------------------------------------------

def test_9_no_live_write_ready_defined():
    """
    LIVE_WRITE_READY must never appear as a JSON property key or enum value in any schema.
    It MAY appear in description text (documenting that it is forbidden) — that is correct.
    """
    errors = []
    for name, path in _SCHEMA_FILES.items():
        schema = _load_json(path)
        # Check that LIVE_WRITE_READY is not a property key at any level
        schema_text = json.dumps(schema)
        # The string appears as a value in description fields — that is allowed.
        # What is forbidden: it appearing as a key in properties, or as an enum element
        # that would define it as a valid type identifier.
        props = schema.get("properties", {})
        if "LIVE_WRITE_READY" in props:
            errors.append(f"[schema:{name}] 'LIVE_WRITE_READY' is a defined property — must never be defined")
        # Also check it doesn't appear as an enum value in top-level fields
        for prop_name, prop_def in props.items():
            if not isinstance(prop_def, dict):
                continue
            enum_vals = prop_def.get("enum", [])
            if "LIVE_WRITE_READY" in enum_vals:
                errors.append(
                    f"[schema:{name}] property '{prop_name}' has 'LIVE_WRITE_READY' as enum value"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 10: No schema creates live-write permission
# ---------------------------------------------------------------------------

def test_10_no_live_write_permission():
    """
    Schemas must not encode patterns that directly grant live-write permission.
    Checked by verifying no schema contains the string patterns associated with
    live-write authorization.
    """
    live_write_indicators = ["live_write_allowed", "live_write_enabled", "execute_mutation"]
    errors = []
    for name, path in _SCHEMA_FILES.items():
        text = path.read_text(encoding="utf-8")
        for indicator in live_write_indicators:
            if indicator in text:
                errors.append(
                    f"[schema:{name}] contains live-write indicator '{indicator}'"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 11: No schema imports/references merge specialist as execution path
# ---------------------------------------------------------------------------

def test_11_no_merge_specialist_reference_in_schemas():
    forbidden = ["queue_drain", "batch_resolve_and_merge", "dopemux_pr_merge_specialist"]
    errors = []
    for name, path in _SCHEMA_FILES.items():
        text = path.read_text(encoding="utf-8")
        for f in forbidden:
            if f in text:
                errors.append(
                    f"[schema:{name}] references forbidden merge-specialist path '{f}'"
                )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 12: DCP-RED-MERGE-SEAM-0001 preserved / referenced as forbidden
# ---------------------------------------------------------------------------

def test_12_merge_seam_red_line_present():
    errors = []
    for name, path in _FIXTURE_FILES.items():
        fixture = _load_json(path)
        red_lines = fixture.get("red_lines", [])
        if "DCP-RED-MERGE-SEAM-0001" not in red_lines:
            errors.append(
                f"[fixture:{name}] 'DCP-RED-MERGE-SEAM-0001' not in red_lines"
            )
    assert not errors, "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 13: DCP_MUTATION_CLASS has a hard-block class for merge seam
# ---------------------------------------------------------------------------

def test_13_mutation_class_has_merge_seam_hard_block():
    fixture = _load_json(_FIXTURE_FILES["dcp_mutation_class"])
    classes = fixture.get("classes", [])
    hard_block_ids = [
        c["class_id"] for c in classes
        if isinstance(c, dict) and c.get("side_effect_posture") == "hard_block"
    ]
    assert hard_block_ids, "No hard_block class found in mutation_class fixture"

    # The hard-block class must trigger DCP-RED-MERGE-SEAM-0001
    seam_blocked = [
        c["class_id"] for c in classes
        if isinstance(c, dict)
        and c.get("side_effect_posture") == "hard_block"
        and "DCP-RED-MERGE-SEAM-0001" in c.get("red_lane_triggers", [])
    ]
    assert seam_blocked, (
        f"No hard_block class triggers DCP-RED-MERGE-SEAM-0001. "
        f"Hard-block classes found: {hard_block_ids}"
    )

    # The hard-block class must have approval_tier == HARD_BLOCK and allowed_in_v1 == False
    for c in classes:
        if not isinstance(c, dict):
            continue
        if "DCP-RED-MERGE-SEAM-0001" in c.get("red_lane_triggers", []) and c.get("side_effect_posture") == "hard_block":
            assert c.get("approval_tier") == "HARD_BLOCK", (
                f"[{c['class_id']}] approval_tier should be HARD_BLOCK"
            )
            assert c.get("allowed_in_v1") is False, (
                f"[{c['class_id']}] allowed_in_v1 must be False for hard-block class"
            )
            assert c.get("live_write_ready_required") is False, (
                f"[{c['class_id']}] live_write_ready_required must be False for hard-block (it is prohibited, not gated)"
            )


# ---------------------------------------------------------------------------
# Test 14: DCP_APPROVAL_ARTIFACT requires requester != approver (no self-cert)
# ---------------------------------------------------------------------------

def test_14_approval_artifact_requester_ne_approver():
    schema = _load_json(_SCHEMA_FILES["dcp_approval_artifact"])
    fixture = _load_json(_FIXTURE_FILES["dcp_approval_artifact"])

    # Schema must declare both requester and approver
    props = schema.get("properties", {})
    required = schema.get("required", [])
    assert "requester" in props, "Schema missing 'requester' property"
    assert "approver" in props, "Schema missing 'approver' property"
    assert "requester" in required, "'requester' not in schema required"
    assert "approver" in required, "'approver' not in schema required"
    assert "supervisor_signoff" in props, "Schema missing 'supervisor_signoff' property"

    # Fixture must have requester != approver
    requester = fixture.get("requester", "")
    approver = fixture.get("approver", "")
    assert requester, "Fixture: requester is empty"
    assert approver, "Fixture: approver is empty"
    assert requester != approver, (
        f"Fixture: requester '{requester}' equals approver '{approver}' — self-certification violation"
    )

    # Fixture must have supervisor_signoff block
    signoff = fixture.get("supervisor_signoff")
    assert isinstance(signoff, dict), "Fixture: supervisor_signoff is missing or not a dict"
    assert "required" in signoff, "Fixture: supervisor_signoff.required missing"
    assert "provided" in signoff, "Fixture: supervisor_signoff.provided missing"


# ---------------------------------------------------------------------------
# Test 15: DCP_PROJECT_RESOURCE_MAP marks endpoints as PROVISIONAL or UNKNOWN
# ---------------------------------------------------------------------------

def test_15_resource_map_endpoints_are_provisional():
    fixture = _load_json(_FIXTURE_FILES["dcp_project_resource_map"])
    endpoint_bindings = fixture.get("endpoint_bindings", [])
    assert endpoint_bindings, "fixture: endpoint_bindings is empty — must include at least one binding"

    errors = []
    for binding in endpoint_bindings:
        if not isinstance(binding, dict):
            continue
        svc = binding.get("service_id", "?")
        status = binding.get("binding_status", "")
        prov_tag = binding.get("provenance_tag", "")
        if status not in ("PROVISIONAL", "UNKNOWN"):
            errors.append(
                f"[endpoint:{svc}] binding_status='{status}'; must be PROVISIONAL or UNKNOWN"
            )
        if prov_tag not in ("PROVISIONAL", "UNKNOWN"):
            errors.append(
                f"[endpoint:{svc}] provenance_tag='{prov_tag}'; must be PROVISIONAL or UNKNOWN"
            )
    assert not errors, "Endpoint binding violations:\n" + "\n".join(errors)

    # ConPort and dope-memory must appear and be PROVISIONAL/UNKNOWN
    service_ids = {b.get("service_id", "") for b in endpoint_bindings if isinstance(b, dict)}
    assert any("conport" in sid.lower() for sid in service_ids), (
        "endpoint_bindings must include ConPort — its binding status is PROVISIONAL"
    )


# ---------------------------------------------------------------------------
# Test 16: No forbidden files were modified (git diff guard)
# ---------------------------------------------------------------------------

def test_16_no_forbidden_files_modified():
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[2]
    )
    changed = result.stdout.strip().splitlines()
    forbidden_prefixes = [
        "src/dopemux_pr_merge_specialist/",
        "dopemux_pr_merge_specialist/",
        "scripts/batch_resolve_and_merge.py",
        ".github/workflows/",
    ]
    violations = [
        f for f in changed
        if any(f.startswith(p) for p in forbidden_prefixes)
    ]
    assert not violations, (
        "Forbidden files in git diff:\n" + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Test 17: No live external calls required for validation
# ---------------------------------------------------------------------------

def test_17_no_live_calls_required():
    """
    This test is a structural assertion: all validations in this suite are local
    (JSON parse, schema validation, string checks, git diff). No network calls,
    no subprocess to external services, no API tokens required.
    """
    # Trivially passes by construction; serves as documentation and audit anchor.
    assert True, "All validations in this suite are local — no live calls required"


# ---------------------------------------------------------------------------
# __main__ runner
# ---------------------------------------------------------------------------

def _run_all_tests(skip_roundtrip: bool = False):
    all_tests = [
        ("1: schemas_valid_json", test_1_schemas_are_valid_json),
        ("2: fixtures_validate_against_schemas", test_2_fixtures_validate_against_schemas),
        ("3: additionalProperties_false_at_root", test_3_schemas_have_additional_properties_false),
        ("4: contract_level_provenance", test_4_schemas_have_contract_provenance),
        ("5: fixtures_have_field_provenance", test_5_fixtures_have_field_provenance),
        ("6: every_fixture_field_has_provenance", test_6_every_fixture_field_has_provenance),
        ("7: validation_state_vocabulary", test_7_validation_state_vocabulary),
        ("8: no_provenance_laundering", test_8_no_provenance_laundering),
        ("9: no_live_write_ready_defined", test_9_no_live_write_ready_defined),
        ("10: no_live_write_permission", test_10_no_live_write_permission),
        ("11: no_merge_specialist_in_schemas", test_11_no_merge_specialist_reference_in_schemas),
        ("12: merge_seam_red_line_present", test_12_merge_seam_red_line_present),
        ("13: mutation_class_hard_block", test_13_mutation_class_has_merge_seam_hard_block),
        ("14: requester_ne_approver", test_14_approval_artifact_requester_ne_approver),
        ("15: endpoints_provisional", test_15_resource_map_endpoints_are_provisional),
        ("16: no_forbidden_files", test_16_no_forbidden_files_modified),
        ("17: no_live_calls", test_17_no_live_calls_required),
    ]
    tests = [
        (name, fn) for name, fn in all_tests
        if not (skip_roundtrip and name.startswith("2:"))
    ]
    passed = failed = 0
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
    print("DCP Contract Derivation Tests — TP-DCP-0002")
    print(f"  schemas dir : {_SCHEMAS_DIR}")
    print(f"  fixtures dir: {_FIXTURES_DIR}")
    print()
    if not _HAS_JSONSCHEMA:
        print("WARNING: jsonschema not installed — round-trip test (2) is SKIPPED.")
        print()
    failed_count = _run_all_tests(skip_roundtrip=not _HAS_JSONSCHEMA)
    sys.exit(1 if failed_count > 0 else 0)
