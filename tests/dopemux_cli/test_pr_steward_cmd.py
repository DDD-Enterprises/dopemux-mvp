from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner

from dopemux.cli import cli
from dopemux_pr_steward.cli import main as steward_main


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


def test_doctor_placeholder_fails_closed(capsys):
    rc = steward_main(["doctor"])

    captured = capsys.readouterr()
    assert rc == 2
    assert "TP-DMX-STEWARD-DOCTOR-303" in captured.err


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
