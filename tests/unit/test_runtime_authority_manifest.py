from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "runtime_authority_manifest.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_runtime_authority.py"


def _load_verifier_module():
    spec = importlib.util.spec_from_file_location("verify_runtime_authority", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_has_required_system_entry_keys() -> None:
    manifest = _load_manifest()

    assert manifest["schema_version"] == "1.0"
    systems = manifest["systems"]
    assert isinstance(systems, list)
    assert {entry["system"] for entry in systems} == {
        "ADHD Engine",
        "ConPort",
        "Repo Truth Extractor",
        "dope-context",
        "dope-memory",
        "dopecon-bridge",
        "dopemux",
        "dopetask",
        "task-orchestrator",
    }

    for entry in systems:
        assert {"system", "expected_paths", "authority_status", "validation_mode"} <= set(entry)
        assert isinstance(entry["expected_paths"], list)
        assert entry["authority_status"]
        assert entry["validation_mode"]


def test_static_verifier_passes_current_manifest_and_reports_known_conflicts() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(MANIFEST_PATH),
            "--check",
            "static",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["summary"]["errors"] == 0

    codes = [finding["code"] for finding in report["findings"]]
    assert "expected_port_conflict" in codes
    assert "expected_runtime_pointer_conflict" in codes

    sort_keys = [
        (
            finding["severity"],
            finding["system"],
            finding["code"],
            finding.get("path", ""),
            finding["message"],
        )
        for finding in report["findings"]
    ]
    assert sort_keys == sorted(
        sort_keys,
        key=lambda item: (
            {"error": 0, "warning": 1, "info": 2}.get(item[0], 99),
            item[1],
            item[2],
            item[3],
            item[4],
        ),
    )


def test_verifier_returns_nonzero_for_unexpected_missing_authority_file(tmp_path: Path) -> None:
    manifest = {
        "repo_identity": {
            "origin_hint": "",
            "repo_marker": "",
            "require_identity_match": False,
        },
        "systems": [
            {
                "authority_status": "canonical",
                "expected_paths": [
                    {
                        "path": "missing-authority.py",
                        "required": True,
                    }
                ],
                "system": "missing-system",
                "validation_mode": "static_required",
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--check",
            "static",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["summary"]["errors"] == 1
    assert report["findings"][0]["code"] == "expected_path_missing"


def test_unknown_authority_paths_are_advisory(tmp_path: Path) -> None:
    module = _load_verifier_module()
    repo_root = tmp_path
    manifest = {
        "systems": [
            {
                "authority_status": "unknown",
                "expected_paths": [
                    {
                        "path": "candidate-only.py",
                        "required": True,
                    }
                ],
                "system": "unknown-system",
                "validation_mode": "static_required",
            }
        ],
    }

    report = module.verify_manifest(manifest, repo_root)

    assert report["ok"] is True
    assert report["summary"]["errors"] == 0
    assert any(finding["code"] == "unknown_authority_not_asserted" for finding in report["findings"])
    assert any(
        finding["code"] == "expected_path_missing" and finding["severity"] == "warning"
        for finding in report["findings"]
    )
