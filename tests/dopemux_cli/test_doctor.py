from __future__ import annotations

import json
from pathlib import Path

from dopemux_pr_steward.cli import main as steward_main


VALID_POLICY = {
    "mode": "check_only",
    "mutates_github": False,
    "fail_closed_on_unknown": True,
    "required_artifacts": [
        "MERGE_READINESS.json",
        "REVIEW_ITEM_LEDGER.json",
        "THREAD_DISPOSITIONS.json",
        "CI_TRIAGE.json",
        "PR_STATE_SNAPSHOT.json",
    ],
    "trusted_reviewer_associations": [
        "OWNER",
        "MEMBER",
        "COLLABORATOR",
    ],
}


def _write_policy(workspace: Path, payload: dict) -> Path:
    path = workspace / "config" / "pr_steward" / "policy.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_doctor_passes_valid_matching_scaffold_policy(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path, VALID_POLICY)
    before = policy_path.read_text(encoding="utf-8")

    rc = steward_main(["doctor", "--workspace", str(tmp_path), "--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert payload["status"] == "PASS"
    assert payload["checks"]["config_schema"]["status"] == "PASS"
    assert payload["checks"]["scaffold_skew"]["status"] == "PASS"
    assert policy_path.read_text(encoding="utf-8") == before


def test_doctor_fails_closed_on_invalid_config(tmp_path: Path, capsys) -> None:
    _write_policy(tmp_path, {"mode": "check_only", "mutates_github": False})

    rc = steward_main(["doctor", "--workspace", str(tmp_path), "--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 2
    assert payload["status"] == "BLOCKED"
    assert payload["checks"]["config_schema"]["status"] == "FAIL"
    assert "required_artifacts" in payload["checks"]["config_schema"]["message"]


def test_doctor_fails_closed_on_scaffold_skew(tmp_path: Path, capsys) -> None:
    policy = dict(VALID_POLICY)
    policy["trusted_reviewer_associations"] = ["OWNER", "MEMBER"]
    _write_policy(tmp_path, policy)

    rc = steward_main(["doctor", "--workspace", str(tmp_path), "--format", "json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 2
    assert payload["status"] == "BLOCKED"
    assert payload["checks"]["config_schema"]["status"] == "PASS"
    assert payload["checks"]["scaffold_skew"]["status"] == "FAIL"
    assert "config/pr_steward/policy.json differs" in payload["checks"]["scaffold_skew"]["message"]


def test_doctor_fails_closed_on_unknown_schema(tmp_path: Path, capsys) -> None:
    _write_policy(tmp_path, VALID_POLICY)

    rc = steward_main(
        [
            "doctor",
            "--workspace",
            str(tmp_path),
            "--schema",
            str(tmp_path / "missing.schema.json"),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 2
    assert payload["status"] == "BLOCKED"
    assert payload["reason_code"] == "UNKNOWN_SCHEMA"


def test_doctor_help_describes_report_only_contract(capsys) -> None:
    rc = steward_main(["doctor", "--help"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "report-only" in captured.out
    assert "--workspace" in captured.out
