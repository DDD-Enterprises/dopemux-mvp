"""
DCP Contracts Consistency Tests — DMX-DCP-TOOLING-101

Verifies that schemas/dcp/manifest.json is internally consistent and truthful:

  (a) manifest validates against dcp_contracts_manifest.schema.json
  (b) every schema_file entry exists on disk
  (c) every .schema.json in schemas/dcp/ (except the manifest schema itself) has
      EXACTLY ONE entry in the manifest — no unlisted schemas, no duplicates
  (d) every ci_gates name exists as a job name or step name in
      .github/workflows/ci-complete.yml
  (e) every L2/L3 entry has non-empty runtime_producers AND runtime_consumers

Negative-path unit tests (using synthetic dicts):
  - a bogus ci_gate name must fail the gate-existence check
  - an L2 entry missing runtime_producers must fail the producers/consumers check

Run:
  cd <repo-root>
  PYTHONPATH=src python3 -m pytest tests/dcp/test_contracts_consistency.py -v
"""

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants — resolved relative to this file so both invocation modes work
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
_SCHEMAS_DIR = _REPO_ROOT / "schemas" / "dcp"
_MANIFEST_PATH = _SCHEMAS_DIR / "manifest.json"
_MANIFEST_SCHEMA_PATH = _SCHEMAS_DIR / "dcp_contracts_manifest.schema.json"
_CI_WORKFLOW_PATH = _REPO_ROOT / ".github" / "workflows" / "ci-complete.yml"

# The manifest schema file is excluded from the "every schema must have an entry" check
_MANIFEST_SCHEMA_FILENAME = "dcp_contracts_manifest.schema.json"


# ---------------------------------------------------------------------------
# Helpers (also called directly by negative-path unit tests)
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    with open(_MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_manifest_schema() -> dict:
    with open(_MANIFEST_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def collect_ci_names() -> set:
    """Return all job names and step names found in ci-complete.yml.

    Parses ``name:`` lines rather than importing a YAML library, so this
    works even when pyyaml is not installed in the test environment.

    GitHub Actions workflow files use two forms:
      - Job names:  ``  job-key:\n    name: "Job Name"`` (key ``name:`` at
        arbitrary indentation, no preceding ``-``)
      - Step names: ``      - name: Step Name`` (preceded by ``- `` list marker)

    We match both with a single regex:
      ``\\s*(?:-\\s+)?name:\\s+(.+)``
    """
    import re
    _name_re = re.compile(r"\s*(?:-\s+)?name:\s+(.+)")
    names: set = set()
    with open(_CI_WORKFLOW_PATH, encoding="utf-8") as f:
        for line in f:
            m = _name_re.match(line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    names.add(value)
    return names


def validate_ci_gates(contract_id: str, ci_gates: list, known_ci_names: set) -> list:
    """Return a list of gate names that do NOT appear in known_ci_names.

    Returns an empty list when all gates are valid (or when ci_gates is empty).
    """
    bad = [g for g in ci_gates if g not in known_ci_names]
    return bad


def validate_l2_l3_runtime(contract_id: str, level: str, producers: list, consumers: list) -> bool:
    """Return True when the entry satisfies the L2/L3 runtime requirement.

    L2 and L3 contracts MUST have non-empty runtime_producers AND
    runtime_consumers.  L0/L1 contracts always pass this check.
    """
    if level not in ("L2", "L3"):
        return True
    return bool(producers) and bool(consumers)


# ---------------------------------------------------------------------------
# (a) manifest validates against dcp_contracts_manifest.schema.json
# ---------------------------------------------------------------------------

def test_manifest_validates_against_schema():
    """Skip gracefully when jsonschema is not importable."""
    jsonschema = pytest.importorskip("jsonschema", reason="jsonschema not installed")

    manifest = load_manifest()
    manifest_schema = load_manifest_schema()

    try:
        validator_cls = jsonschema.Draft7Validator
    except AttributeError:
        validator_cls = jsonschema.Draft4Validator  # fallback

    validator = validator_cls(manifest_schema)
    errors = list(validator.iter_errors(manifest))
    assert errors == [], (
        f"manifest.json failed schema validation with {len(errors)} error(s):\n"
        + "\n".join(f"  [{i+1}] {e.message} (path: {list(e.path)})" for i, e in enumerate(errors[:5]))
    )


# ---------------------------------------------------------------------------
# (b) every schema_file in the manifest exists on disk
# ---------------------------------------------------------------------------

def test_all_schema_files_exist():
    manifest = load_manifest()
    missing = []
    for entry in manifest["contracts"]:
        path = _REPO_ROOT / entry["schema_file"]
        if not path.exists():
            missing.append(entry["schema_file"])
    assert missing == [], (
        f"{len(missing)} schema_file(s) listed in manifest do not exist on disk:\n"
        + "\n".join(f"  {p}" for p in missing)
    )


# ---------------------------------------------------------------------------
# (c) every .schema.json (except the manifest schema) has exactly one manifest entry
# ---------------------------------------------------------------------------

def test_no_unlisted_schemas_and_no_duplicates():
    manifest = load_manifest()

    # Build sets
    listed_files = [entry["schema_file"] for entry in manifest["contracts"]]
    listed_basenames = [Path(f).name for f in listed_files]

    # Check for duplicate entries in the manifest
    seen: dict = {}
    duplicates = []
    for basename in listed_basenames:
        if basename in seen:
            duplicates.append(basename)
        seen[basename] = True
    assert duplicates == [], (
        f"Duplicate schema entries in manifest: {duplicates}"
    )

    # Collect actual .schema.json files (excluding the manifest schema itself)
    actual_schema_files = {
        f.name
        for f in _SCHEMAS_DIR.glob("*.schema.json")
        if f.name != _MANIFEST_SCHEMA_FILENAME
    }

    # Check for unlisted schemas
    unlisted = actual_schema_files - set(listed_basenames)
    assert unlisted == set(), (
        f"Schemas in schemas/dcp/ that are NOT listed in manifest: {sorted(unlisted)}"
    )

    # Check for listed schemas that don't exist on disk
    extra = set(listed_basenames) - actual_schema_files
    assert extra == set(), (
        f"Manifest entries that have no corresponding .schema.json file: {sorted(extra)}"
    )


# ---------------------------------------------------------------------------
# (d) every ci_gates name must appear in ci-complete.yml
# ---------------------------------------------------------------------------

def test_ci_gate_names_exist_in_workflow():
    manifest = load_manifest()
    known_ci_names = collect_ci_names()

    failures = []
    for entry in manifest["contracts"]:
        bad_gates = validate_ci_gates(
            entry["contract_id"], entry["ci_gates"], known_ci_names
        )
        if bad_gates:
            failures.append(
                f"  {entry['contract_id']}: unknown ci_gates {bad_gates}"
            )

    assert failures == [], (
        f"{len(failures)} contract(s) reference non-existent CI gate names:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# (e) L2/L3 entries must have non-empty runtime_producers AND runtime_consumers
# ---------------------------------------------------------------------------

def test_l2_l3_entries_have_runtime_coupling():
    manifest = load_manifest()
    failures = []
    for entry in manifest["contracts"]:
        ok = validate_l2_l3_runtime(
            entry["contract_id"],
            entry["level"],
            entry["runtime_producers"],
            entry["runtime_consumers"],
        )
        if not ok:
            failures.append(
                f"  {entry['contract_id']} (level={entry['level']}): "
                f"runtime_producers={entry['runtime_producers']!r}, "
                f"runtime_consumers={entry['runtime_consumers']!r}"
            )
    assert failures == [], (
        f"{len(failures)} L2/L3 contract(s) missing runtime coupling:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Negative-path unit tests — synthetic dicts (do NOT touch real manifest)
# ---------------------------------------------------------------------------

class TestNegativePathCiGate:
    """A bogus ci_gate name MUST be detected as invalid."""

    def test_bogus_ci_gate_fails(self):
        known = collect_ci_names()
        bad_gates = validate_ci_gates(
            "DCP_FAKE_CONTRACT",
            ["🚀 This Gate Does Not Exist In The Workflow"],
            known,
        )
        assert bad_gates == ["🚀 This Gate Does Not Exist In The Workflow"], (
            "Expected bogus gate name to be flagged; helper returned empty list"
        )

    def test_real_ci_gate_passes(self):
        known = collect_ci_names()
        bad_gates = validate_ci_gates(
            "DCP_RED_LANE_TAXONOMY",
            ["🔴 Run DCP red-lane gate (TP-DMX-DCP-CI-GATE-001)"],
            known,
        )
        assert bad_gates == [], (
            f"Real gate name was wrongly flagged as missing: {bad_gates}"
        )


class TestNegativePathL2RuntimeCoupling:
    """An L2 entry missing runtime_producers MUST fail the coupling check."""

    def test_l2_missing_producers_fails(self):
        ok = validate_l2_l3_runtime(
            "DCP_FAKE_L2",
            level="L2",
            producers=[],          # missing!
            consumers=["src/dopemux/dcp/consumer.py"],
        )
        assert ok is False, (
            "Expected L2 entry with empty producers to fail; helper returned True"
        )

    def test_l2_missing_consumers_fails(self):
        ok = validate_l2_l3_runtime(
            "DCP_FAKE_L2",
            level="L2",
            producers=["src/dopemux/dcp/producer.py"],
            consumers=[],          # missing!
        )
        assert ok is False, (
            "Expected L2 entry with empty consumers to fail; helper returned True"
        )

    def test_l2_both_present_passes(self):
        ok = validate_l2_l3_runtime(
            "DCP_FAKE_L2",
            level="L2",
            producers=["src/dopemux/dcp/producer.py"],
            consumers=["src/dopemux/dcp/consumer.py"],
        )
        assert ok is True, (
            "Expected L2 entry with both producers and consumers to pass"
        )

    def test_l0_empty_runtime_passes(self):
        ok = validate_l2_l3_runtime(
            "DCP_FAKE_L0",
            level="L0",
            producers=[],
            consumers=[],
        )
        assert ok is True, (
            "Expected L0 entry with empty runtime arrays to pass (L0 has no coupling requirement)"
        )
