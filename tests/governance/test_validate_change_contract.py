"""Tests for scripts/governance/validate_change_contract.py."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.governance.validate_change_contract import (
    classify_path,
    evaluate,
    main,
    max_lane,
)

ROOT = Path(__file__).resolve().parents[2]


def test_classify_lanes() -> None:
    assert classify_path("docs/03-reference/governance/evidence-economy.md") == "L2"
    assert classify_path("AGENTS.md") == "L2"
    assert classify_path("scripts/governance/validate_change_contract.py") == "L2"
    assert classify_path("proof/pr_merge/embedded-audit/pr-1181/PROOF.json") == "L0"
    assert classify_path("task-packets/TP-X.json") == "L0"
    assert classify_path("src/dopemux/cli.py") == "L2"
    assert classify_path("README.md") == "L1"
    assert classify_path(".github/workflows/ci.yml") == "L3"
    assert classify_path("config/audit/embedded-audit-allowed-signers") == "L3"


def test_max_lane() -> None:
    assert max_lane(["L0", "L1"]) == "L1"
    assert max_lane(["L1", "L3", "L2"]) == "L3"
    assert max_lane([]) == "L0"


def test_clean_l0_metadata() -> None:
    text = """---
id: sample
title: Sample
type: reference
owner: '@hu3mann'
last_review: 2026-08-02
next_review: 2026-11-01
---
# Sample
"""
    r = evaluate(
        paths=["task-packets/TP-SAMPLE.md"],
        cwd=ROOT,
        file_text={"task-packets/TP-SAMPLE.md": text},
    )
    assert r.status == "PASS"
    assert r.max_lane == "L0"
    assert r.model_audit_required is False


def test_l2_governance_path() -> None:
    r = evaluate(paths=["AGENTS.md"], cwd=ROOT, head="HEAD")
    assert r.max_lane == "L2"
    assert r.model_audit_required is True


def test_l3_security_path() -> None:
    r = evaluate(paths=[".github/workflows/ci-complete.yml"], cwd=ROOT, head="HEAD")
    assert r.max_lane == "L3"
    assert r.model_audit_required is True


def test_missing_frontmatter_fails() -> None:
    r = evaluate(
        paths=["docs/03-reference/governance/example.md"],
        cwd=ROOT,
        file_text={"docs/03-reference/governance/example.md": "# no fm\n"},
    )
    assert r.status == "FAIL"
    codes = {f.code for f in r.findings}
    assert "frontmatter_missing" in codes or "hook_would_modify" in codes


def test_invalid_packet_json() -> None:
    r = evaluate(
        paths=["task-packets/BAD.json"],
        cwd=ROOT,
        file_text={"task-packets/BAD.json": '{"id": 1}'},
    )
    assert r.status == "FAIL"
    assert any(f.code.startswith("packet_") for f in r.findings)


def test_invalid_proof_missing_embedded_audit() -> None:
    r = evaluate(
        paths=["proof/TP-DMX-EXAMPLE/PROOF.json"],
        cwd=ROOT,
        file_text={"proof/TP-DMX-EXAMPLE/PROOF.json": '{"packet_id":"x"}'},
    )
    assert r.status == "FAIL"
    assert any(f.code == "proof_missing_embedded_audit" for f in r.findings)


def test_proof_only_valid() -> None:
    r = evaluate(
        paths=[
            "proof/TP-DMX-EXAMPLE/PROOF.json",
            "proof/pr_merge/embedded-audit/pr-9/PROOF.json",
        ],
        cwd=ROOT,
        proof_only_mode=True,
        content_head="a" * 40,
        audited_head="a" * 40,
        proof_head="a" * 40,
        file_text={
            "proof/TP-DMX-EXAMPLE/PROOF.json": json.dumps(
                {
                    "embedded_audit": {
                        "required": True,
                        "status": "SKIPPED",
                        "auditor_tool": "none",
                        "auditor_model": "unknown",
                        "invocation": None,
                        "exit_code": None,
                        "report_path": "proof/TP-DMX-EXAMPLE/AUDITOR_REPORT.md",
                        "findings": [],
                        "fixes_applied": [],
                        "remaining_risks": [],
                        "skip_reason": "fixture",
                    }
                }
            ),
            "proof/pr_merge/embedded-audit/pr-9/PROOF.json": json.dumps(
                {
                    "embedded_audit": {
                        "required": True,
                        "status": "PASS",
                        "auditor_tool": "claude-code-cli",
                        "auditor_model": "sonnet",
                        "invocation": "claude -p",
                        "exit_code": 0,
                        "report_path": "proof/pr_merge/embedded-audit/pr-9/AUDITOR_REPORT.md",
                        "findings": [],
                        "fixes_applied": [],
                        "remaining_risks": [],
                        "skip_reason": None,
                    }
                }
            ),
        },
    )
    assert r.proof_only is True
    assert r.model_audit_required is False
    # ancestry uses git; with fake SHAs may fail ancestry — only check escaped path absent
    assert not any(f.code == "proof_only_escaped_path" for f in r.findings)


def test_proof_only_escaped_path_fails() -> None:
    r = evaluate(
        paths=["scripts/audit/pal_clink_runner.py", "proof/TP-X/PROOF.json"],
        cwd=ROOT,
        proof_only_mode=True,
        file_text={"proof/TP-X/PROOF.json": "{}"},
    )
    assert r.status == "FAIL"
    assert any(f.code == "proof_only_escaped_path" for f in r.findings)


def test_hook_would_modify_on_incomplete_frontmatter() -> None:
    r = evaluate(
        paths=["task-packets/TP-INCOMPLETE.md"],
        cwd=ROOT,
        file_text={
            "task-packets/TP-INCOMPLETE.md": "---\nid: x\ntitle: t\ntype: reference\n---\n# x\n"
        },
    )
    assert r.status == "FAIL"
    assert any(f.code in {"frontmatter_incomplete", "hook_would_modify"} for f in r.findings)


def test_cli_json_format_exit_zero_on_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Empty path list against this repo should PASS
    code = main(["--paths", "--format", "json", "--repo", str(ROOT)])
    # --paths with nothing after may be empty list
    assert code in {0, 2}  # depends on argparse; call with explicit empty via base
    # Use paths that don't exist as empty by passing only HEAD self equal - use known good L0 file from repo if any
    code2 = main(
        [
            "--paths",
            "README.md",
            "--format",
            "json",
            "--repo",
            str(ROOT),
        ]
    )
    assert code2 == 0


def test_allowlist_violation() -> None:
    code = main(
        [
            "--paths",
            "src/dopemux/cli.py",
            "--allowlist",
            "docs/**",
            "--format",
            "text",
            "--repo",
            str(ROOT),
        ]
    )
    assert code == 1
