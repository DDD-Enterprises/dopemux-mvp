"""Tests for the read-only PR Action Bridge CLI."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "pr_action_bridge"
SCHEMA_PATH = ROOT / "schemas" / "pr_action_bridge" / "action_plan.schema.json"
CLI_SRC = ROOT / "tools" / "pr_action_bridge" / "cli.py"
MAIN_SRC = ROOT / "tools" / "pr_action_bridge" / "__main__.py"
WRAPPER = ROOT / "scripts" / "pr-action-bridge"
FIXED_TS = "2026-01-01T00:00:00Z"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _write_artifact_dir(tmp_path: Path, fixture_name: str) -> Path:
    fixture = _load_fixture(fixture_name)
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    mapping = {
        "MERGE_READINESS.json": fixture["merge_readiness"],
        "REVIEW_ITEM_LEDGER.json": fixture["review_ledger"],
        "THREAD_DISPOSITIONS.json": fixture["thread_dispositions"],
        "CI_TRIAGE.json": fixture["ci_triage"],
    }
    for filename, payload in mapping.items():
        (artifact_dir / filename).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return artifact_dir


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_module_cli_writes_action_plan_and_repair_packet(tmp_path: Path) -> None:
    artifact_dir = _write_artifact_dir(tmp_path, "needs_implementer_failed_check.json")
    out_dir = tmp_path / "out"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_action_bridge",
            "--artifact-dir",
            str(artifact_dir),
            "--out",
            str(out_dir),
            "--generated-at",
            FIXED_TS,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    action_plan = json.loads((out_dir / "ACTION_PLAN.json").read_text(encoding="utf-8"))
    repair_packet = (out_dir / "REPAIR_PACKET.md").read_text(encoding="utf-8")
    jsonschema.validate(action_plan, _load_schema())
    assert action_plan["generated_at"] == FIXED_TS
    assert action_plan["mutation_performed"] is False
    assert action_plan["actions"][0]["category"] == "failed-check"
    assert "Implementer Actions" in repair_packet
    assert "failed-check" in repair_packet


def test_wrapper_script_invokes_module_cli(tmp_path: Path) -> None:
    artifact_dir = _write_artifact_dir(tmp_path, "ready_green.json")
    out_dir = tmp_path / "out"

    result = subprocess.run(
        [
            str(WRAPPER),
            "--artifact-dir",
            artifact_dir.name,
            "--out",
            out_dir.name,
            "--generated-at",
            FIXED_TS,
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    action_plan = json.loads(
        (tmp_path / out_dir.name / "ACTION_PLAN.json").read_text(encoding="utf-8")
    )
    repair_packet = (tmp_path / out_dir.name / "REPAIR_PACKET.md").read_text(
        encoding="utf-8"
    )
    assert action_plan["actions"] == []
    assert action_plan["mutation_performed"] is False
    assert "No actions required" in repair_packet


def test_missing_required_artifact_fails_closed(tmp_path: Path) -> None:
    artifact_dir = _write_artifact_dir(tmp_path, "ready_green.json")
    (artifact_dir / "CI_TRIAGE.json").unlink()
    out_dir = tmp_path / "out"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_action_bridge",
            "--artifact-dir",
            str(artifact_dir),
            "--out",
            str(out_dir),
            "--generated-at",
            FIXED_TS,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "CI_TRIAGE.json" in result.stderr
    assert not (out_dir / "ACTION_PLAN.json").exists()
    assert not (out_dir / "REPAIR_PACKET.md").exists()


def test_invalid_generated_at_fails_before_writing_outputs(tmp_path: Path) -> None:
    artifact_dir = _write_artifact_dir(tmp_path, "ready_green.json")
    out_dir = tmp_path / "out"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_action_bridge",
            "--artifact-dir",
            str(artifact_dir),
            "--out",
            str(out_dir),
            "--generated-at",
            "not-a-timestamp",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "--generated-at must be an ISO 8601 timestamp" in result.stderr
    assert not (out_dir / "ACTION_PLAN.json").exists()
    assert not (out_dir / "REPAIR_PACKET.md").exists()


def test_cli_sources_do_not_import_pr_merge_or_embed_gh_mutation() -> None:
    for source_path in (CLI_SRC, MAIN_SRC):
        source = source_path.read_text(encoding="utf-8")
        assert "pr_merge" not in source
        for forbidden in ("gh pr merge", "gh pr approve", "gh pr ready", "gh pr comment"):
            assert forbidden not in source
