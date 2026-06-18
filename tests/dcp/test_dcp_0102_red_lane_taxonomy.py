import json
from pathlib import Path

import pytest

from dopemux.dcp.red_lane import Status
from dopemux.dcp.red_lane_scanner import RedLaneScanner


REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = REPO_ROOT / "schemas" / "dcp" / "dcp_red_lane_taxonomy.instance.json"
TAXONOMY_SCHEMA_PATH = REPO_ROOT / "schemas" / "dcp" / "dcp_red_lane_taxonomy.schema.json"


def test_repo_taxonomy_instance_validates_against_schema():
    jsonschema = pytest.importorskip("jsonschema", reason="jsonschema not installed")

    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    schema = json.loads(TAXONOMY_SCHEMA_PATH.read_text(encoding="utf-8"))

    jsonschema.Draft7Validator(schema).validate(taxonomy)
    lane_ids = {lane["id"] for lane in taxonomy["lanes"]}
    assert "DCP-RED-MERGE-SEAM-0001" in lane_ids
    assert taxonomy["validation"]["state"] == "REPO_CROSS_CHECKED"


def test_scanner_report_exposes_repo_taxonomy_metadata():
    scanner = RedLaneScanner(repo_root=str(REPO_ROOT))
    report = scanner.scan(
        changed_files=["src/dopemux/dcp/red_lane.py"],
        proof_paths=["proof/DMX-DCP-TOOLING-101/PROOF.json"],
    )

    assert report.status == Status.PASS
    assert report.scanner.taxonomy_id == "dcp-red-lane-taxonomy-v0-seed"
    assert report.scanner.taxonomy_path == "schemas/dcp/dcp_red_lane_taxonomy.instance.json"
    assert "DCP-RED-MERGE-SEAM-0001" in report.scanner.taxonomy_lane_ids

    payload = report.to_dict()
    assert payload["scanner"]["taxonomy_id"] == report.scanner.taxonomy_id
    assert payload["scanner"]["taxonomy_path"] == report.scanner.taxonomy_path
    assert payload["scanner"]["taxonomy_lane_ids"] == report.scanner.taxonomy_lane_ids


def test_scanner_missing_taxonomy_is_explicit_not_silent(tmp_path):
    proof = tmp_path / "PROOF.json"
    proof.write_text(
        json.dumps({
            "implementer_identity": "Agent",
            "audit": {"auditor_identity": "Human"},
            "head_sha": "expected123"
        }),
        encoding="utf-8",
    )

    scanner = RedLaneScanner(repo_root=str(tmp_path))
    report = scanner.scan(proof_paths=["PROOF.json"], expected_head_sha="expected123")

    assert report.status == Status.PASS
    assert report.scanner.taxonomy_id == "UNKNOWN"
    assert report.scanner.taxonomy_path == "schemas/dcp/dcp_red_lane_taxonomy.instance.json"
    assert report.scanner.taxonomy_lane_ids == []
