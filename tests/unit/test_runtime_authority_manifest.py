from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "runtime_authority_manifest.json"
VERIFIER = REPO_ROOT / "scripts" / "verify_runtime_authority.py"

REQUIRED_SYSTEMS = {
    "dopemux",
    "dopetask",
    "taskx",
    "task-orchestrator",
    "ConPort",
    "dope-memory",
    "working-memory-assistant",
    "dope-context",
    "dopecon-bridge",
    "ADHD Engine",
    "Repo Truth Extractor",
    "Leantime",
    "Serena",
}

REQUIRED_FIELDS = {
    "system",
    "domain",
    "authority_status",
    "expected_paths",
    "expected_ports",
    "forbidden_authority_paths",
    "known_conflicts",
    "validation_mode",
    "notes",
}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def systems_by_name() -> dict[str, dict]:
    return {entry["system"]: entry for entry in load_manifest()["systems"]}


def conflict_ids(entry: dict) -> set[str]:
    return {conflict["id"] for conflict in entry["known_conflicts"]}


def test_manifest_json_parses() -> None:
    manifest = load_manifest()
    assert manifest["schema_version"] == "1.0"
    assert isinstance(manifest["systems"], list)


def test_required_systems_exist() -> None:
    assert set(systems_by_name()) == REQUIRED_SYSTEMS


def test_every_entry_has_required_fields() -> None:
    for entry in load_manifest()["systems"]:
        assert REQUIRED_FIELDS <= set(entry)
        assert isinstance(entry["expected_paths"], list)
        assert isinstance(entry["expected_ports"], list)
        assert isinstance(entry["forbidden_authority_paths"], list)
        assert isinstance(entry["known_conflicts"], list)
        assert isinstance(entry["notes"], list)


def test_known_task_orchestrator_conflict_is_represented() -> None:
    task_orchestrator = systems_by_name()["task-orchestrator"]
    assert task_orchestrator["authority_status"] == "CONFLICTING"
    assert "task_orchestrator_unsupported_runtime_variant" in conflict_ids(task_orchestrator)
    assert "task_orchestrator_port_3014_vs_8000" not in conflict_ids(task_orchestrator)
    ports = {item["port"]: item["status"] for item in task_orchestrator["expected_ports"]}
    assert ports[8000] == "observed"
    assert 3014 not in ports


def test_known_conport_conflict_is_represented() -> None:
    conport = systems_by_name()["ConPort"]
    assert conport["authority_status"] == "CONFLICTING"
    assert "conport_runtime_surface_split" in conflict_ids(conport)
    assert "conport_3004_3005_contract_split" in conflict_ids(conport)


def test_dope_memory_port_drift_is_represented() -> None:
    dope_memory = systems_by_name()["dope-memory"]
    ports = {item["port"]: item["status"] for item in dope_memory["expected_ports"]}
    assert ports[3020] == "observed"
    assert ports[8096] == "conflicting"
    assert "dope_memory_3020_vs_8096" in conflict_ids(dope_memory)


def test_taskx_is_shim_only_not_runtime_authority() -> None:
    taskx = systems_by_name()["taskx"]
    assert taskx["authority_status"] == "SHIM_ONLY"
    forbidden_domains = {
        item["forbidden_domain"] for item in taskx["forbidden_authority_paths"]
    }
    assert "execution_runtime" in forbidden_domains


def test_dopecon_bridge_is_transport_only_not_domain_authority() -> None:
    bridge = systems_by_name()["dopecon-bridge"]
    assert bridge["authority_status"] == "TRANSPORT_ONLY"
    forbidden_domains = {
        item["forbidden_domain"] for item in bridge["forbidden_authority_paths"]
    }
    assert "pm_workflow_decision_progress_authority" in forbidden_domains


def run_verifier(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_verifier_produces_stable_output() -> None:
    args = (
        "--manifest",
        "config/runtime_authority_manifest.json",
        "--check",
        "static",
    )
    first = run_verifier(*args)
    second = run_verifier(*args)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert first.stdout == second.stdout
    assert "SUMMARY status=passed failures=0" in first.stdout


def test_verifier_exits_nonzero_for_missing_required_path(tmp_path: Path) -> None:
    manifest = copy.deepcopy(load_manifest())
    by_name = {entry["system"]: entry for entry in manifest["systems"]}
    target_entry = by_name["dopemux"]
    required_path = next(
        (p for p in target_entry["expected_paths"] if p.get("required", True)),
        None,
    )
    assert required_path is not None, "dopemux must have at least one required expected_path"
    required_path["path"] = "missing-required-file.txt"
    temp_manifest = tmp_path / "runtime_authority_manifest.json"
    temp_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result = run_verifier(
        "--manifest",
        str(temp_manifest),
        "--system",
        "dopemux",
        "--check",
        "static",
    )

    assert result.returncode == 1
    assert "missing required expected path missing-required-file.txt" in result.stdout
