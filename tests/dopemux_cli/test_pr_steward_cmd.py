from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner
import pytest

from dopemux.cli import cli
from dopemux_pr_steward.cli import main as steward_main
from scripts.audit.run_embedded_audit import build_evidence_gate_proof
from tests.pr_merge_specialist.test_workflow_artifact_verifier import install_artifact_transport


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_dopemux_pr_steward_help_lists_versioned_subcommands():
    result = CliRunner().invoke(cli, ["pr-steward", "--help"])

    assert result.exit_code == 0
    assert "intake" in result.output
    assert "bridge" in result.output
    assert "gate" in result.output
    assert "audit" in result.output
    assert "doctor" in result.output


def test_importable_pr_steward_cli_help_lists_contract(capsys):
    rc = steward_main(["--help"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "dopemux-pr-steward" in captured.out
    assert "contract-version" in captured.out


def test_intake_subcommand_forwards_documented_flags(monkeypatch, tmp_path: Path):
    import tools.pr_steward.intake as intake

    captured: dict[str, list[str]] = {}

    def fake_intake_main(argv: list[str]) -> int:
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(intake, "main", fake_intake_main)

    rc = steward_main(
        [
            "intake",
            "--repo",
            "owner/repo",
            "--pr",
            "1",
            "--out",
            str(tmp_path / "artifacts"),
            "--proof-path",
            "proof/PROOF.json",
            "--strict",
            "--format",
            "text",
        ]
    )

    assert rc == 0
    assert captured["argv"] == [
        "--repo",
        "owner/repo",
        "--pr",
        "1",
        "--out",
        str(tmp_path / "artifacts"),
        "--strict",
        "--proof-path",
        "proof/PROOF.json",
        "--format",
        "text",
    ]


def test_gate_subcommand_uses_packaged_steward_gate(tmp_path: Path, capsys):
    readiness = _write_json(
        tmp_path / "MERGE_READINESS.json",
        {
            "generated_at": "2026-05-31T12:00:00Z",
            "readiness": "READY",
            "pr": {"number": 301, "head_sha": "abc123"},
            "proof": {"proof_head_sha": "abc123"},
            "embedded_audit": {"status": "PASS"},
        },
    )
    proof = _write_json(
        tmp_path / "PROOF.json",
        {
            "generated_at": "2026-05-31T12:00:00Z",
            "head_sha": "abc123",
            "embedded_audit": {"status": "PASS"},
        },
    )

    rc = steward_main(
        [
            "gate",
            "--head-sha",
            "abc123",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "301",
            "--base-sha",
            "base123",
            "--required-class",
            "FINALIZATION",
            "--merge-readiness",
            str(readiness),
            "--audit-proof",
            str(proof),
            "--now",
            "2026-05-31T12:15:00Z",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["allowed"] is True
    assert payload["reason_code"] == "ALLOW_FINALIZATION"


@pytest.mark.parametrize("base", [None, "f" * 40, "b" * 40])
def test_gate_cli_requires_matching_explicit_base(tmp_path: Path, capsys, base, monkeypatch):
    head = "a" * 40
    proof = build_evidence_gate_proof(
        packet_id="TP-CLI-PROVENANCE",
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=301,
        head_sha=head,
        base_sha="b" * 40,
        change_contract={"status": "PASS", "max_lane": "L0", "model_audit_required": False},
        local_attestation=None,
        generated_at="2026-05-31T12:00:00Z",
    )
    proof_path = _write_json(tmp_path / "PROOF.json", proof)
    install_artifact_transport(monkeypatch, proof_path.read_bytes())
    readiness_path = _write_json(tmp_path / "MERGE_READINESS.json", {
        "generated_at": "2026-05-31T12:00:00Z",
        "readiness": "READY",
        "pr": {"number": 301, "head_sha": head},
        "proof": {"proof_head_sha": head},
        "embedded_audit": proof["embedded_audit"],
    })
    args = [
        "gate", "--repo", "DDD-Enterprises/dopemux-mvp", "--pr", "301",
        "--head-sha", head, "--required-class", "FINALIZATION",
        "--merge-readiness", str(readiness_path), "--audit-proof", str(proof_path),
        "--now", "2026-05-31T12:15:00Z", "--format", "json",
    ]
    if base is not None:
        args.extend(["--base-sha", base])
    rc = steward_main(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["allowed"] is (base == "b" * 40)
    assert rc == (0 if base == "b" * 40 else 2)


def test_doctor_reports_implemented_checks(capsys):
    repo_root = Path(__file__).resolve().parents[2]
    rc = steward_main(["doctor", "--workspace", str(repo_root), "--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["status"] == "PASS"
    assert payload["checks"]["config_schema"]["status"] == "PASS"
    assert payload["checks"]["scaffold_skew"]["status"] == "PASS"
    assert captured.err == ""


@pytest.mark.parametrize("forged", [False, True])
def test_cli_requires_exact_authenticated_bytes_with_pinned_run(tmp_path, monkeypatch, capsys, forged):
    from tests.pr_merge_specialist.test_workflow_artifact_verifier import proof_bytes
    remote_bytes = proof_bytes()
    transport = install_artifact_transport(monkeypatch, remote_bytes)
    proof = json.loads(remote_bytes)
    local_bytes = json.dumps({**proof, "packet_id": "TP-FORGED"}).encode() if forged else remote_bytes
    path = tmp_path / "PROOF.json"
    path.write_bytes(local_bytes)
    readiness = _write_json(tmp_path / "MERGE_READINESS.json", {
        "generated_at": proof["generated_at"], "readiness": "READY",
        "pr": {"number": 1330, "head_sha": "a" * 40},
        "proof": {"proof_head_sha": "a" * 40}, "embedded_audit": proof["embedded_audit"],
    })
    rc = steward_main([
        "gate", "--repo", "DDD-Enterprises/dopemux-mvp", "--pr", "1330",
        "--head-sha", "a" * 40, "--base-sha", "b" * 40, "--audit-run-id", "23",
        "--required-class", "FINALIZATION", "--merge-readiness", str(readiness),
        "--audit-proof", str(path), "--now", "2026-09-07T12:15:00Z", "--format", "json",
    ])
    result = json.loads(capsys.readouterr().out)
    assert result["allowed"] is (not forged)
    assert rc == (2 if forged else 0)
    assert ("artifacts", transport.artifact["name"], 23) in transport.calls


def test_pr_steward_package_imports_outside_repo_root(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from dopemux_pr_steward.cli import main; print(main(['--contract-version']))",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0
    assert "contract-version 1.0.0" in result.stdout
    assert result.stdout.strip().endswith("0")


def test_installed_pr_steward_console_can_import_engines(tmp_path: Path):
    target = tmp_path / "site"
    repo_root = Path(__file__).resolve().parents[2]
    install = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target),
            str(repo_root),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert install.returncode == 0, install.stderr
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from dopemux_pr_steward.cli import build_parser; "
                "import pathlib; "
                "import tools.pr_steward.classifier as classifier; "
                "import dopemux.agent; "
                "import dopemux.orchestrator.validation; "
                "import dopemux.tui.widgets; "
                "import tools.copilot_repair.generator; "
                "import tools.auditor_router; "
                "import tools.pr_steward.intake; "
                "import tools.pr_action_bridge.compiler; "
                "from importlib.resources import files; "
                "build_parser(); "
                "print(pathlib.Path(classifier.__file__).with_name("
                "'known_reviewers.json').is_file()); "
                "print(files('dopemux_pr_steward').joinpath('config.schema.json').is_file()); "
                "print(files('dopemux.templates').joinpath("
                "'init/config/pr_steward/policy.json').is_file()); "
                "print(files('dopemux.templates').joinpath("
                "'init/config/pr_merge_specialist/policy.yaml').is_file()); "
                "print(files('dopemux.templates').joinpath("
                "'init/.github/workflows/pr-steward.yml').is_file()); "
                "print(files('dopemux.templates').joinpath("
                "'init/.github/workflows/embedded-audit.yml').is_file())"
            ),
        ],
        cwd=tmp_path,
        env={"PYTHONPATH": str(target)},
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.strip().splitlines() == [
        "True",
        "True",
        "True",
        "True",
        "True",
        "True",
    ]
