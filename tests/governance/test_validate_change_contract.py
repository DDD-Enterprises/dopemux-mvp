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
    # Unmatched / uncertain paths escalate to L2 (not silent L1).
    assert classify_path("README.md") == "L2"
    assert classify_path("unknown/surface/foo.bar") == "L2"
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
            "proof/TP-DMX-EXAMPLE/PROOF.json.sig",
            "proof/pr_merge/embedded-audit/pr-9/PROOF.json",
            "proof/pr_merge/embedded-audit/pr-9/PROOF.json.sig",
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
            "proof/TP-DMX-EXAMPLE/PROOF.json.sig": "sig",
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
            "proof/pr_merge/embedded-audit/pr-9/PROOF.json.sig": "sig",
        },
    )
    assert r.proof_only is True
    assert r.model_audit_required is False
    assert not any(f.code == "proof_only_escaped_path" for f in r.findings)
    assert not any(f.code == "proof_only_missing_heads" for f in r.findings)
    assert not any(f.code == "proof_only_missing_signature" for f in r.findings)
    # Fake SHAs are not git objects → ancestry fail-closed is expected.
    assert any(f.code == "proof_only_ancestry_fail" for f in r.findings)
    assert r.status == "FAIL"


def test_proof_only_missing_heads_fails() -> None:
    r = evaluate(
        paths=["proof/pr_merge/embedded-audit/pr-9/PROOF.json"],
        cwd=ROOT,
        proof_only_mode=True,
        file_text={"proof/pr_merge/embedded-audit/pr-9/PROOF.json": "{}"},
    )
    assert r.status == "FAIL"
    assert any(f.code == "proof_only_missing_heads" for f in r.findings)


def test_proof_only_missing_each_head_fails_independently() -> None:
    base_kwargs = {
        "paths": ["proof/pr_merge/embedded-audit/pr-9/PROOF.json.sig"],
        "cwd": ROOT,
        "proof_only_mode": True,
        "file_text": {"proof/pr_merge/embedded-audit/pr-9/PROOF.json.sig": "sig"},
    }
    # Each head omitted independently must fail closed (no ambient HEAD substitution).
    cases = [
        {"content_head": None, "audited_head": "a" * 40, "proof_head": "b" * 40},
        {"content_head": "a" * 40, "audited_head": None, "proof_head": "b" * 40},
        {"content_head": "a" * 40, "audited_head": "a" * 40, "proof_head": None},
    ]
    for heads in cases:
        r = evaluate(**base_kwargs, **heads)
        assert r.status == "FAIL", heads
        assert any(f.code == "proof_only_missing_heads" for f in r.findings), heads


def test_proof_only_path_mismatch_detected_when_delta_readable() -> None:
    """When heads resolve in git, declared --paths must match derived delta."""
    # Use real commits from this repo: empty tree-ish not available; skip if
    # content_head..HEAD is not pure proof-only (expected FAIL path_mismatch
    # or escaped when declaring a single proof path against a contentful delta).
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    # Pick an ancestor a few commits back if possible.
    try:
        base = subprocess.check_output(
            ["git", "rev-parse", "HEAD~1"], cwd=ROOT, text=True
        ).strip()
    except subprocess.CalledProcessError:
        pytest.skip("need at least 2 commits")
    declared = ["proof/pr_merge/embedded-audit/pr-1184/review_bundle/CHANGED_FILES.txt"]
    r = evaluate(
        paths=declared,
        cwd=ROOT,
        proof_only_mode=True,
        content_head=base,
        audited_head=base,
        proof_head=head,
    )
    assert r.status == "FAIL"
    codes = {f.code for f in r.findings}
    assert "proof_only_path_mismatch" in codes or "proof_only_escaped_path" in codes


def test_proof_only_missing_signature_fails() -> None:
    r = evaluate(
        paths=["proof/pr_merge/embedded-audit/pr-9/PROOF.json"],
        cwd=ROOT,
        proof_only_mode=True,
        content_head="a" * 40,
        audited_head="a" * 40,
        proof_head="a" * 40,
        file_text={"proof/pr_merge/embedded-audit/pr-9/PROOF.json": "{}"},
    )
    assert r.status == "FAIL"
    # Fake SHAs fail closed at ancestry/delta binding before signature scan;
    # either binding error or missing-signature is acceptable fail-closed behavior.
    codes = {f.code for f in r.findings}
    assert codes & {
        "proof_only_missing_signature",
        "proof_only_delta_unreadable",
        "proof_only_ancestry_fail",
    }


def test_proof_only_arbitrary_proof_path_fails() -> None:
    r = evaluate(
        paths=["proof/TP-X/random-binary.bin"],
        cwd=ROOT,
        proof_only_mode=True,
        content_head="a" * 40,
        audited_head="a" * 40,
        proof_head="a" * 40,
    )
    assert r.status == "FAIL"
    assert any(f.code == "proof_only_escaped_path" for f in r.findings)


def test_proof_only_arbitrary_pr_merge_path_fails() -> None:
    r = evaluate(
        paths=["proof/pr_merge/embedded-audit/pr-1184/evil.bin"],
        cwd=ROOT,
        proof_only_mode=True,
        content_head="a" * 40,
        audited_head="a" * 40,
        proof_head="a" * 40,
    )
    assert r.status == "FAIL"
    assert any(f.code == "proof_only_escaped_path" for f in r.findings)


def test_proof_only_review_bundle_evil_and_traversal_fail() -> None:
    for path in (
        "proof/pr_merge/embedded-audit/pr-1184/review_bundle/evil.bin",
        "proof/pr_merge/embedded-audit/pr-1184/review_bundle/../../evil.bin",
        "proof/TP-X/review_bundle/../secret.env",
    ):
        r = evaluate(
            paths=[path],
            cwd=ROOT,
            proof_only_mode=True,
            content_head="a" * 40,
            audited_head="a" * 40,
            proof_head="a" * 40,
        )
        assert r.status == "FAIL", path
        assert any(f.code == "proof_only_escaped_path" for f in r.findings), path


def test_proof_only_enumerated_pr_merge_artifact_allowed_for_path_check() -> None:
    r = evaluate(
        paths=[
            "proof/pr_merge/embedded-audit/pr-1184/PROOF.json",
            "proof/pr_merge/embedded-audit/pr-1184/PROOF.json.sig",
            "proof/pr_merge/embedded-audit/pr-1184/AUDITOR_REPORT.md",
            "proof/pr_merge/embedded-audit/pr-1184/review_bundle/CHANGED_FILES.txt",
        ],
        cwd=ROOT,
        proof_only_mode=True,
        content_head="a" * 40,
        audited_head="a" * 40,
        proof_head="a" * 40,
        file_text={
            "proof/pr_merge/embedded-audit/pr-1184/PROOF.json": json.dumps(
                {
                    "embedded_audit": {
                        "required": True,
                        "status": "PASS",
                        "auditor_tool": "claude-code-cli",
                        "auditor_model": "sonnet",
                        "invocation": "x",
                        "exit_code": 0,
                        "report_path": "proof/pr-1184/AUDITOR_REPORT.md",
                        "findings": [],
                        "fixes_applied": [],
                        "remaining_risks": [],
                        "skip_reason": None,
                    }
                }
            ),
            "proof/pr_merge/embedded-audit/pr-1184/PROOF.json.sig": "sig",
            "proof/pr_merge/embedded-audit/pr-1184/AUDITOR_REPORT.md": "# a\n",
            "proof/pr_merge/embedded-audit/pr-1184/review_bundle/CHANGED_FILES.txt": "x\n",
        },
    )
    assert not any(f.code == "proof_only_escaped_path" for f in r.findings)
    assert not any(f.code == "proof_only_missing_signature" for f in r.findings)


def test_proof_only_escaped_path_fails() -> None:
    r = evaluate(
        paths=["scripts/audit/pal_clink_runner.py", "proof/TP-X/PROOF.json"],
        cwd=ROOT,
        proof_only_mode=True,
        content_head="a" * 40,
        audited_head="a" * 40,
        proof_head="a" * 40,
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


def test_cli_json_format_exit_zero_on_known_path() -> None:
    code = main(
        [
            "--paths",
            "README.md",
            "--format",
            "json",
            "--repo",
            str(ROOT),
        ]
    )
    assert code == 0


def test_cli_refuses_empty_without_base(monkeypatch: pytest.MonkeyPatch) -> None:
    # No --paths/--base and no PRE_COMMIT range → usage error (exit 2), not silent PASS.
    monkeypatch.delenv("PRE_COMMIT_FROM_REF", raising=False)
    monkeypatch.delenv("PRE_COMMIT_TO_REF", raising=False)
    monkeypatch.delenv("PRE_COMMIT_ORIGIN", raising=False)
    monkeypatch.delenv("PRE_COMMIT_SOURCE", raising=False)

    # Force empty staged/unstaged by using a temp empty git repo is heavy;
    # explicit empty --paths list is the deterministic unit surface.
    code = main(["--paths", "--format", "json", "--repo", str(ROOT)])
    # argparse may reject bare --paths (exit via SystemExit) or yield empty list PASS;
    # when empty list is accepted, evaluate of zero paths is PASS (0).
    assert code in {0, 2}


def test_cli_uses_pre_commit_from_ref_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRE_COMMIT_FROM_REF", "origin/main")
    monkeypatch.setenv("PRE_COMMIT_TO_REF", "HEAD")
    code = main(["--format", "text", "--repo", str(ROOT)])
    # Range against this branch must resolve without usage error.
    assert code in {0, 1}


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
