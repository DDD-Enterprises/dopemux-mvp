"""Tests for the DCP-aware export seam (``dopemux.pcp.dcp_extension_export``).

Verifies that the seam:
  - returns the unmodified generic export when no DCP extension is present;
  - enriches ``proof_manifest`` to PRESENT (with path) when a declared proof root exists;
  - enriches ``proof_manifest`` to ABSENT (DCP-assessed) when no proof root exists;
  - always produces output valid against project_evidence_export.schema.json;
  - never mutates the generic exporter's behaviour.
"""

import json
import pathlib
import subprocess

from jsonschema import Draft202012Validator

from dopemux.pcp.dcp_extension_export import export_evidence_with_dcp

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_EXPORT_SCHEMA = json.loads(
    (_REPO_ROOT / "schemas/project_control_plane/project_evidence_export.schema.json").read_text()
)
_VALIDATOR = Draft202012Validator(_EXPORT_SCHEMA)


def _run_git(path: pathlib.Path, *args: str) -> None:
    subprocess.check_call(
        ["git", *args], cwd=path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def _init_repo(path: pathlib.Path) -> None:
    _run_git(path, "init", "-q")
    _run_git(path, "config", "user.email", "t@example.com")
    _run_git(path, "config", "user.name", "t")
    (path / "README.md").write_text("seed")
    _run_git(path, "add", "-A")
    _run_git(path, "commit", "-q", "-m", "init")


def _make_dcp_repo(path: pathlib.Path, *, with_proof: bool) -> None:
    man = path / "schemas" / "dcp_extension"
    man.mkdir(parents=True)
    (man / "extension_manifest.dcp.json").write_text(
        json.dumps(
            {
                "capabilities": {
                    "proof_status_mappings": [
                        "schemas/dcp_extension/proof_status_map.dcp.json"
                    ]
                }
            }
        )
    )
    (man / "proof_status_map.dcp.json").write_text(
        json.dumps(
            {
                "schema_version": "pcp.proof_status_map.v0",
                "proof_pointers": [{"path": "PROOF.json", "freshness_state": "UNKNOWN"}],
            }
        )
    )
    if with_proof:
        (path / "PROOF.json").write_text(json.dumps({"ok": True}))
    _init_repo(path)


def _schema_errors(result: dict) -> list:
    return list(_VALIDATOR.iter_errors(result))


def test_no_dcp_returns_generic_export(tmp_path: pathlib.Path) -> None:
    _init_repo(tmp_path)
    result = export_evidence_with_dcp(tmp_path)
    assert result["proof_manifest"] == {"state": "ABSENT", "path": None, "freshness": "UNKNOWN"}
    assert _schema_errors(result) == []


def test_dcp_with_present_proof_root(tmp_path: pathlib.Path) -> None:
    _make_dcp_repo(tmp_path, with_proof=True)
    result = export_evidence_with_dcp(tmp_path)
    pm = result["proof_manifest"]
    assert pm["state"] == "PRESENT"
    assert pm["path"] == "PROOF.json"
    assert pm["freshness"] == "UNKNOWN"
    assert _schema_errors(result) == []
    reasons = [u["reason"] for u in result["unknowns"] if u["field"] == "proof_manifest"]
    assert reasons and "DCP proof-family mapping resolved" in reasons[0]


def test_dcp_with_absent_proof_root(tmp_path: pathlib.Path) -> None:
    _make_dcp_repo(tmp_path, with_proof=False)
    result = export_evidence_with_dcp(tmp_path)
    pm = result["proof_manifest"]
    assert pm["state"] == "ABSENT"
    assert pm["path"] is None
    assert _schema_errors(result) == []
    reasons = [u["reason"] for u in result["unknowns"] if u["field"] == "proof_manifest"]
    assert reasons and "no declared proof root present" in reasons[0]
