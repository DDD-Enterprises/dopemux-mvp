"""Focused regression tests for the standalone Control Tower kit CLI."""

import importlib.util
import hashlib
from importlib.machinery import SourceFileLoader
import json
import subprocess
import zipfile
from argparse import Namespace
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CT_PATH = REPO / ".control-tower" / "bin" / "ct"
LOADER = SourceFileLoader("control_tower_ct", str(CT_PATH))
SPEC = importlib.util.spec_from_loader("control_tower_ct", LOADER)
ct = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ct)


def valid_route(packet_id="TP-TEST-001"):
    return {
        "schema_version": "1.0",
        "packet_id": packet_id,
        "stage": "bounded-repair",
        "risk_lane": "L3",
        "selection": {
            "runner": "Codex",
            "runner_availability": "PROVEN",
            "model": "cheap-agent",
            "effort": "medium",
        },
        "justification": {
            "why_runner": "available",
            "why_model": "adequate",
            "why_effort": "bounded",
            "alternatives_considered": [{"route": "local", "reason": "deterministic"}],
        },
        "audit": {
            "required": True,
            "runner": "Claude CLI",
            "model": "sonnet",
            "effort": "medium",
            "independence": "distinct runtime",
            "rationale": "fresh audit after freeze",
        },
    }


def test_route_validation_matches_shipped_schema_for_wrong_values():
    route = valid_route()
    route["schema_version"] = "9.9"
    route["selection"]["effort"] = []
    assert ct.validate_route_obj(route, REPO)

    route = valid_route()
    route["audit"]["required"] = "true"
    assert ct.validate_route_obj(route, REPO)


def test_route_validation_rejects_blank_required_fields_without_traceback():
    route = valid_route()
    route["packet_id"] = "   "
    route["justification"]["alternatives_considered"] = [{}]
    errors = ct.validate_route_obj(route, REPO)
    assert any("packet_id" in error for error in errors)
    assert any("alternatives" in error for error in errors)
    assert ct.validate_route_obj([], REPO)

    route = valid_route()
    route["justification"]["alternatives_considered"] = [{"route": " ", "reason": " "}]
    errors = ct.validate_route_obj(route, REPO)
    assert any("alternatives_considered" in error for error in errors)


def test_route_validation_rejects_malformed_risk_without_type_error():
    route = valid_route()
    route["risk_lane"] = []
    errors = ct.validate_route_obj(route, REPO)
    assert any("risk_lane" in error for error in errors)


def test_route_validation_matches_jsonschema_oracle():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (REPO / ".control-tower/schemas/route_decision.schema.json").read_text()
    )
    jsonschema.Draft202012Validator(schema).validate(valid_route())
    invalid = valid_route()
    invalid["schema_version"] = "9.9"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(invalid)

    return_schema = json.loads(
        (REPO / ".control-tower/schemas/return_packet.schema.json").read_text()
    )
    return_packet = {
        "return_id": "RETURN-001",
        "packet_id": "TP-001",
        "decision_needed": "operator decision",
        "reason": "audit gate",
        "head_sha": "a" * 40,
    }
    jsonschema.Draft202012Validator(return_schema).validate(return_packet)
    return_packet["reason"] = ""
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(return_schema).validate(return_packet)


def test_validate_route_cli_reports_malformed_json(tmp_path, capsys):
    malformed = tmp_path / "route.json"
    malformed.write_text("{")
    result = ct.cmd_validate_route(Namespace(file=str(malformed)))
    captured = capsys.readouterr()
    assert result == 2
    assert "JSONDecodeError" in captured.out
    assert "Traceback" not in captured.out


def test_return_pack_cli_requires_reason_and_decision():
    result = subprocess.run(
        [
            str(CT_PATH),
            "return-pack",
            "--packet-id",
            "TP-RETURN-001",
            "--packet",
            "missing.json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--reason" in result.stderr
    assert "--decision-needed" in result.stderr


def test_tool_info_only_proves_successful_version_probe(monkeypatch):
    monkeypatch.setattr(ct.shutil, "which", lambda name: "/tmp/fake-tool")
    monkeypatch.setattr(
        ct, "run", lambda cmd: {"returncode": 1, "stdout": "", "stderr": "failed"}
    )
    info = ct.tool_info("fake", ["--version"])
    assert info["availability"] == "UNKNOWN"
    assert info["returncode"] == 1


def test_l0_route_record_omits_optional_audit_fields(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(ct, "repo_root", lambda: REPO)
    monkeypatch.setattr(ct, "state_dir", lambda repo: state)
    args = Namespace(
        packet_id="TP-L0-001",
        stage="inspection",
        risk="L0",
        runner="Codex",
        runner_availability="PROVEN",
        agent_role="implementer",
        custom_agent=None,
        model="cheap-agent",
        effort="low",
        why_runner="local",
        why_model="adequate",
        why_effort="low risk",
        cost_latency_tradeoff=None,
        alternative=["local|selected|deterministic"],
        evidence=[],
        fallback_runner=None,
        fallback_model=None,
        fallback_trigger=None,
        audit_required=False,
        audit_runner=None,
        audit_model=None,
        audit_effort=None,
        audit_independence=None,
        audit_rationale=None,
    )
    assert ct.cmd_route_record(args) == 0
    route_path = state / "routes" / "TP-L0-001.json"
    recorded = json.loads(route_path.read_text())
    assert recorded["audit"] == {"required": False}
    assert ct.validate_route_obj(recorded, REPO) == []

    legacy = valid_route("TP-LEGACY-001")
    legacy["risk_lane"] = "L1"
    legacy["audit"] = {
        "required": False,
        "runner": None,
        "model": None,
        "effort": None,
        "independence": None,
        "rationale": "",
    }
    assert ct.validate_route_obj(legacy, REPO) == []


def test_runner_inventory_does_not_probe_models_by_default(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ct, "repo_root", lambda: tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(ct, "state_dir", lambda repo: state)
    monkeypatch.setattr(
        ct.shutil, "which", lambda name: "/tmp/fake-agy" if name == "agy" else None
    )
    monkeypatch.setattr(
        ct, "tool_info", lambda name, args: {"tool": name, "availability": "UNKNOWN"}
    )

    def fake_run(cmd, cwd=None):
        calls.append(cmd)
        return {"returncode": 0, "stdout": "", "stderr": ""}

    monkeypatch.setattr(ct, "run", fake_run)
    assert ct.cmd_runner_inventory(Namespace(probe_models=False)) == 0
    assert ["agy", "models"] not in calls


def test_secret_scan_fails_closed_for_oversized_and_unreadable(tmp_path, monkeypatch):
    oversized = tmp_path / "oversized.bin"
    oversized.write_bytes(b"x" * (ct.MAX_SCAN_BYTES + 1))
    assert ct.scan_files([oversized])[0]["pattern"] == "UNSCANNABLE_OVERSIZED"

    unreadable = tmp_path / "unreadable.bin"
    unreadable.write_bytes(b"safe")
    original = Path.open

    def fail_read(self, *args, **kwargs):
        if self == unreadable:
            raise OSError("permission denied")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_read)
    result = ct.scan_files([unreadable])
    assert result == [{"path": str(unreadable), "pattern": "UNSCANNABLE_UNREADABLE"}]
    assert "permission denied" not in json.dumps(result)


def test_secret_scan_reports_only_redacted_sink_metadata(tmp_path):
    canary = "sk-" + "A" * 48
    source = tmp_path / "source.txt"
    source.write_text(canary)
    result = ct.scan_files([source])
    rendered = json.dumps(result)
    assert result == [{"path": str(source), "pattern": "OPENAI_KEY"}]
    assert canary not in rendered


def test_packet_identity_supports_json_and_markdown(tmp_path):
    packet_json = tmp_path / "packet.json"
    packet_json.write_text(json.dumps({"id": "TP-JSON-001"}))
    assert ct.packet_identity(packet_json) == "TP-JSON-001"
    packet_md = tmp_path / "packet.md"
    packet_md.write_text("# Task Packet: TP-MD-001\n\nBody\n")
    assert ct.packet_identity(packet_md) == "TP-MD-001"


def test_get_route_rejects_stored_route_identity_mismatch(tmp_path, monkeypatch):
    routes = tmp_path / "routes"
    routes.mkdir()
    route = valid_route("TP-OTHER-001")
    (routes / "TP-REQUESTED-001.json").write_text(json.dumps(route))
    monkeypatch.setattr(ct, "routes_dir", lambda repo: routes)
    with pytest.raises(SystemExit, match="identity mismatch"):
        ct.get_route(REPO, "TP-REQUESTED-001")


def _write_archive(
    path, tamper=False, duplicate_inventory=False, invalid_inventory=None
):
    root = "PROOF_project_packet_20260908"
    payload = {
        "payload.txt": b"payload\n",
        "PROOF_REVIEW/nested/SHA256SUMS.txt": b"nested historical manifest\n",
        "SECRET_SCAN_REPORT.json": b'{"hits": [], "status": "PASS"}\n',
    }
    sums = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in payload.items()
    )
    if tamper:
        payload["payload.txt"] = b"tampered\n"
    inventory = [
        {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        for name, data in payload.items()
    ]
    if duplicate_inventory:
        inventory.append(dict(inventory[0]))
    if invalid_inventory:
        field, value = invalid_inventory
        inventory[0][field] = value
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in payload.items():
            archive.writestr(f"{root}/{name}", data)
        archive.writestr(f"{root}/SHA256SUMS.txt", sums)
        archive.writestr(f"{root}/FILE_INVENTORY.json", json.dumps(inventory))


def test_verify_zip_checks_root_manifest_and_member_hashes(tmp_path, capsys):
    good = tmp_path / "good.zip"
    _write_archive(good)
    assert ct.cmd_verify_zip(Namespace(zip=str(good))) == 0
    assert "manifest verified" in capsys.readouterr().out

    bad = tmp_path / "bad.zip"
    _write_archive(bad, tamper=True)
    assert ct.cmd_verify_zip(Namespace(zip=str(bad))) == 2
    assert "hash mismatch" in capsys.readouterr().out

    duplicate = tmp_path / "duplicate-inventory.zip"
    _write_archive(duplicate, duplicate_inventory=True)
    assert ct.cmd_verify_zip(Namespace(zip=str(duplicate))) == 2
    assert "malformed FILE_INVENTORY" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("field", "value"),
    [("sha256", None), ("sha256", []), ("bytes", True), ("bytes", "7")],
)
def test_verify_zip_rejects_malformed_inventory_types(tmp_path, capsys, field, value):
    archive = tmp_path / f"invalid-{field}-{type(value).__name__}.zip"
    _write_archive(archive, invalid_inventory=(field, value))
    assert ct.cmd_verify_zip(Namespace(zip=str(archive))) == 2
    assert "malformed FILE_INVENTORY" in capsys.readouterr().out


def test_proof_pack_output_round_trips_through_manifest_verifier(tmp_path, monkeypatch):
    fake_repo = tmp_path / "repo"
    state = fake_repo / "state"
    routes = state / "routes"
    routes.mkdir(parents=True)
    (routes / "TP-PACK-001.json").write_text(json.dumps(valid_route("TP-PACK-001")))
    monkeypatch.setattr(ct, "repo_root", lambda: fake_repo)
    monkeypatch.setattr(ct, "ct_root", lambda repo: REPO / ".control-tower")
    monkeypatch.setattr(ct, "state_dir", lambda repo: state)
    monkeypatch.setattr(
        ct,
        "load_project",
        lambda repo: {
            "project_name": "test",
            "downloads": {"proof": str(tmp_path / "downloads")},
        },
    )
    monkeypatch.setattr(
        ct,
        "git_state",
        lambda repo: {
            "repo_root": str(repo),
            "head_sha": "a" * 40,
            "branch": "test",
            "origin": "example/repo",
            "merge_base_origin_main": "b" * 40,
        },
    )
    monkeypatch.setattr(
        ct,
        "run",
        lambda cmd, cwd=None: {"cmd": cmd, "returncode": 0, "stdout": "", "stderr": ""},
    )
    packet = tmp_path / "TP-PACK-001.json"
    packet.write_text(json.dumps({"id": "TP-PACK-001", "target": "test"}))
    args = Namespace(
        packet_id="TP-PACK-001",
        packet=str(packet),
        proof_dir=None,
        include=[],
        reason=None,
        decision_needed=None,
    )
    assert ct.cmd_proof_pack(args) == 0
    archives = list((tmp_path / "downloads").glob("*.zip"))
    assert len(archives) == 1
    assert ct.cmd_verify_zip(Namespace(zip=str(archives[0]))) == 0

    packet.write_text(json.dumps({"id": "TP-OTHER-001", "target": "crosswired"}))
    with pytest.raises(SystemExit, match="packet identity mismatch"):
        ct.cmd_proof_pack(args)
    packet.write_text(json.dumps({"id": "TP-PACK-001", "target": "test"}))
    return_args = Namespace(
        packet_id="TP-PACK-001",
        packet=str(packet),
        proof_dir=None,
        include=[],
        reason=" ",
        decision_needed="operator decision",
    )
    assert ct.cmd_return_pack(return_args) == 2
