# tests/pr_steward/test_intake_security_release_fixture.py
from __future__ import annotations

from pathlib import Path

from tools.pr_steward.classifier import build_artifacts
from tools.pr_steward.collector import load_fixture

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "security_release_red_lane"


def test_fixture_workflow_touch_without_approval_is_needs_supervisor():
    harvest = load_fixture(FIXTURE_DIR)
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=9001,
        strict=True,
        allow_closed=False,
    )
    readiness = artifacts["MERGE_READINESS.json"]
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is False
    assert readiness["readiness"] == "NEEDS_SUPERVISOR"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]
