"""Offline deterministic autoreview loop integration test."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from scripts.audit.run_embedded_audit import run_cli as run_embedded_audit_cli
from tools.copilot_repair import generate_repair_packet, render_repair_packet


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "autoreview" / "offline_pr"
FIXED_TS = "2026-01-01T00:00:00Z"
REPO = "DDD-Enterprises/dopemux-mvp"
PR_NUMBER = "704"
HEAD_SHA = "head000000000000000000000000000000000000"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_steward(fixture_dir: Path, out_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.pr_steward.intake",
            "--fixture-dir",
            str(fixture_dir),
            "--repo",
            REPO,
            "--pr",
            PR_NUMBER,
            "--out",
            str(out_dir),
            "--strict",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_action_bridge(
    artifact_dir: Path,
    out_dir: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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


def test_offline_autoreview_loop_reaches_ready_without_live_github(
    tmp_path: Path,
) -> None:
    initial_steward_dir = tmp_path / "01_pr_steward_initial"
    bridge_dir = tmp_path / "02_action_bridge"
    copilot_dir = tmp_path / "03_copilot"
    audit_dir = tmp_path / "04_embedded_audit"
    final_steward_dir = tmp_path / "05_pr_steward_final"

    initial = _run_steward(FIXTURE / "initial", initial_steward_dir)
    assert initial.returncode == 2, initial.stderr
    initial_readiness = _load_json(initial_steward_dir / "MERGE_READINESS.json")
    assert initial_readiness["readiness"] == "NEEDS_IMPLEMENTER"
    assert initial_readiness["mutation_performed"] is False

    bridge = _run_action_bridge(initial_steward_dir, bridge_dir)
    assert bridge.returncode == 0, bridge.stderr
    action_plan = _load_json(bridge_dir / "ACTION_PLAN.json")
    assert action_plan["mutation_performed"] is False
    assert [item["target_role"] for item in action_plan["actions"]] == ["implementer"]

    repair_packet = generate_repair_packet(
        action_plan,
        generated_at=FIXED_TS,
        source_action_plan_id="ACTION_PLAN.json",
    )
    jsonschema.Draft202012Validator(
        _load_json(ROOT / "schemas" / "copilot" / "repair_packet.schema.json")
    ).validate(repair_packet)
    copilot_dir.mkdir()
    (copilot_dir / "COPILOT_REPAIR_PACKET.json").write_text(
        json.dumps(repair_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (copilot_dir / "PR_REPAIR_PACKET.md").write_text(
        render_repair_packet(repair_packet),
        encoding="utf-8",
    )
    assert repair_packet["mutation_performed"] is False
    assert repair_packet["copilot_authority"] == "implementer-only"

    embedded_exit = run_embedded_audit_cli(
        [
            "--packet-id",
            "TP-DMX-AUTOREVIEW-E2E-105",
            "--repo",
            REPO,
            "--pr",
            PR_NUMBER,
            "--head-sha",
            HEAD_SHA,
            "--route-json",
            str(FIXTURE / "audit" / "AUDITOR_ROUTE.json"),
            "--pal-output-json",
            str(FIXTURE / "audit" / "PAL_CLINK_AUDIT_OUTPUT.json"),
            "--out",
            str(audit_dir),
            "--generated-at",
            FIXED_TS,
        ],
        env={"EMBEDDED_AUDIT_TOKEN": "redacted-test-token"},
    )
    assert embedded_exit == 0
    audit_proof = _load_json(audit_dir / "PROOF.json")
    assert audit_proof["embedded_audit"]["status"] == "PASS"
    assert audit_proof["provenance"]["token_value_recorded"] is False
    assert "redacted-test-token" not in json.dumps(audit_proof)

    final = _run_steward(FIXTURE / "final", final_steward_dir)
    assert final.returncode == 0, final.stderr
    final_readiness = _load_json(final_steward_dir / "MERGE_READINESS.json")
    assert final_readiness["readiness"] == "READY"
    assert final_readiness["embedded_audit"]["status"] == "PASS"
    assert final_readiness["mutation_performed"] is False
