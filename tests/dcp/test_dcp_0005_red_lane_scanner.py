import os
import json
from unittest import mock

import pytest
from dopemux.dcp.red_lane_scanner import RedLaneScanner
from dopemux.dcp.red_lane import Status, Severity

def test_clean_local_scan_returns_pass(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_clean"
    repo_root.mkdir()
    
    proof_dir = repo_root / "proof" / "TP-DCP-0005"
    proof_dir.mkdir(parents=True)
    proof_path = proof_dir / "PROOF.json"
    proof_path.write_text(json.dumps({
        "implementer_identity": "Agent",
        "audit": {"auditor_identity": "Human"},
        "head_sha": "expected123"
    }))
    
    f1 = repo_root / "src" / "dopemux" / "dcp" / "some_file.py"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("print('hello world')")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(
        changed_files=["src/dopemux/dcp/some_file.py"],
        proof_paths=["proof/TP-DCP-0005/PROOF.json"],
        expected_head_sha="expected123"
    )
    assert report.status == Status.PASS

def test_forbidden_file_path_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_forbidden_path"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))
    
    report = scanner.scan(
        changed_files=["src/dopemux_pr_merge_specialist/queue_drain.py"]
    )
    assert report.status == Status.BLOCKED
    assert any(f.category == "FORBIDDEN_PATH" for f in report.findings)

def test_forbidden_directory_path_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_forbidden_dir"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))
    
    report = scanner.scan(
        changed_files=["services/task-orchestrator/main.py"]
    )
    assert report.status == Status.BLOCKED
    assert any(f.category == "FORBIDDEN_PATH" for f in report.findings)

def test_merge_seam_queue_drain_string_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_merge_seam"
    repo_root.mkdir()
    f1 = repo_root / "bad_code.py"
    f1.write_text("import queue_drain\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(
        changed_files=["bad_code.py"]
    )
    assert report.status == Status.BLOCKED
    assert any(f.category == "MERGE_SEAM_VIOLATION" for f in report.findings)

def test_batch_merge_string_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_merge_seam2"
    repo_root.mkdir()
    f1 = repo_root / "bad_code.py"
    f1.write_text("batch_resolve_and_merge()\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["bad_code.py"])
    assert report.status == Status.BLOCKED

def test_live_write_ready_enabled_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_live_write"
    repo_root.mkdir()
    f1 = repo_root / "bad_code.py"
    f1.write_text("LIVE_WRITE_READY = True\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["bad_code.py"])
    assert report.status == Status.BLOCKED
    assert any(f.category == "LIVE_WRITE_CREEP" for f in report.findings)
    assert report.guards.live_write_ready_status == "OPERATIONAL"

def test_dopetask_execution_pattern_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_dopetask_execution"
    repo_root.mkdir()
    f1 = repo_root / "bad_code.py"
    f1.write_text("os.system('dopetask tp 123')\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["bad_code.py"])
    assert report.status == Status.BLOCKED
    assert any(f.category == "DOPETASK_EXECUTION" for f in report.findings)

def test_github_mutation_pattern_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_github_mutation"
    repo_root.mkdir()
    f1 = repo_root / "bad_code.py"
    f1.write_text("run('gh pr merge --auto')\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["bad_code.py"])
    assert report.status == Status.BLOCKED
    assert any(f.category == "MERGE_SEAM_VIOLATION" for f in report.findings)

def test_network_and_external_writes_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_bridge_write"
    repo_root.mkdir()
    f1 = repo_root / "bad_code.py"
    f1.write_text("import requests\nrequests.post('http://conport/api/decisions')\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["bad_code.py"])
    assert report.status == Status.BLOCKED
    # requests matches FORBIDDEN_CALL, /api/decisions matches EXTERNAL_WRITE_STATUS
    assert any(f.category == "FORBIDDEN_CALL" for f in report.findings)
    assert any(f.category == "EXTERNAL_WRITE_STATUS" for f in report.findings)
    
def test_stale_proof_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_stale_proof"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({"head_sha": "old123"}))
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"], expected_head_sha="new456")
    assert report.status == Status.BLOCKED
    assert any(f.category == "STALE_PROOF" for f in report.findings)

def test_auditor_same_as_implementer_returns_blocked(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_self_certification"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({
        "implementer_identity": "Gemini",
        "auditor_identity": "Gemini"
    }))
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"])
    assert report.status == Status.BLOCKED
    assert any(f.category == "SELF_CERTIFICATION" for f in report.findings)

def test_merge_readiness_checks(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_merge_readiness"
    repo_root.mkdir()
    mr = repo_root / "MERGE_READINESS.json"
    mr.write_text(json.dumps({
        "has_unknown_reviewers": True,
        "has_unresolved_blocking_threads": True,
        "failed_checks": True,
        "undocumented_residual_risk": True
    }))
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(merge_readiness_paths=["MERGE_READINESS.json"])
    assert report.status == Status.BLOCKED
    categories = [f.category for f in report.findings]
    assert "UNKNOWN_REVIEWER_OR_BOT" in categories
    assert "UNRESOLVED_BLOCKING_THREAD" in categories
    assert "CI_OR_WORKFLOW_MUTATION" in categories
    assert "UNCLASSIFIED_RISK" in categories

def test_scanner_rule_declarations_are_not_false_positives(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_rules"
    repo_root.mkdir()
    # We write a file matching the safe positive list
    f1 = repo_root / "src" / "dopemux" / "dcp" / "red_lane_rules.py"
    f1.parent.mkdir(parents=True, exist_ok=True)
    f1.write_text("re.compile('queue_drain')")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["src/dopemux/dcp/red_lane_rules.py"])
    # should be UNKNOWN because no proof, but NOT have the findings
    assert not any(f.category == "MERGE_SEAM_VIOLATION" for f in report.findings)

def test_test_fixtures_can_contain_forbidden_strings(tmp_path):
    repo_root = tmp_path / "tests" / "dcp" / "fixtures" / "tp_dcp_0005_clean"
    repo_root.mkdir(parents=True, exist_ok=True)
    f1 = repo_root / "bad.py"
    f1.write_text("queue_drain")
    
    scanner = RedLaneScanner(repo_root=str(tmp_path))
    report = scanner.scan(changed_files=["tests/dcp/fixtures/tp_dcp_0005_clean/bad.py"])
    assert report.status == Status.BLOCKED
    assert any(f.category == "MERGE_SEAM_VIOLATION" for f in report.findings)

def test_secret_redaction(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_secrets"
    repo_root.mkdir()
    f1 = repo_root / "bad.py"
    f1.write_text("requests.get('http://api', secret='ghp_1234567890abcdef1234567890abcdef')\n")
    
    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["bad.py"])
    assert report.status == Status.BLOCKED
    for f in report.findings:
        assert "ghp_" not in f.match
        assert "***REDACTED***" in f.match

def test_batch_resolve_script_path_returns_blocked(tmp_path):
    """scripts/batch_resolve_and_merge.py as FORBIDDEN_PATH file-path match (not just text content)."""
    repo_root = tmp_path / "tp_dcp_0005_batch_path"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(
        changed_files=["scripts/batch_resolve_and_merge.py"]
    )
    assert report.status == Status.BLOCKED
    assert any(f.category == "FORBIDDEN_PATH" for f in report.findings)


def test_queue_drain_bare_path_returns_blocked(tmp_path):
    """dopemux_pr_merge_specialist/queue_drain.py (without src/ prefix) as FORBIDDEN_PATH file-path match."""
    repo_root = tmp_path / "tp_dcp_0005_bare_path"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(
        changed_files=["dopemux_pr_merge_specialist/queue_drain.py"]
    )
    assert report.status == Status.BLOCKED
    assert any(f.category == "FORBIDDEN_PATH" for f in report.findings)


def test_report_json_serializes():
    scanner = RedLaneScanner(repo_root="/")
    report = scanner.scan()
    data = report.to_dict()
    assert data["report_family"] == "DCP_RED_LANE_REPORT"
    assert "findings" in data
    assert json.dumps(data)


# ---------------------------------------------------------------------------
# ADR-224 / TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R Phase A: narrow workflow carve-out
# ---------------------------------------------------------------------------

def test_carved_out_workflow_paths_are_not_forbidden_path_findings(tmp_path):
    repo_root = tmp_path / "tp_dcp_seam_lift_carveout_clean"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(
        changed_files=[
            ".github/workflows/embedded-audit.yml",
            ".github/workflows/pr-steward.yml",
        ]
    )
    assert not any(f.category == "FORBIDDEN_PATH" for f in report.findings)


def test_other_workflow_paths_still_forbidden_path_blocked(tmp_path):
    """The carve-out must be exact-filename scoped, not a blanket exemption."""
    repo_root = tmp_path / "tp_dcp_seam_lift_carveout_other"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(changed_files=[".github/workflows/ci-complete.yml"])
    assert report.status == Status.BLOCKED
    assert any(f.category == "FORBIDDEN_PATH" for f in report.findings)


def test_carved_out_workflow_still_subject_to_text_rules(tmp_path):
    """Path-level carve-out must not exempt content-level TEXT_RULES scanning."""
    repo_root = tmp_path / "tp_dcp_seam_lift_carveout_text_rules"
    repo_root.mkdir()
    wf_dir = repo_root / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "embedded-audit.yml").write_text("run: gh pr merge --auto\n")

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=[".github/workflows/embedded-audit.yml"])
    assert report.status == Status.BLOCKED
    assert not any(f.category == "FORBIDDEN_PATH" for f in report.findings)
    assert any(f.category == "MERGE_SEAM_VIOLATION" for f in report.findings)


# ---------------------------------------------------------------------------
# ADR-226 / TP-DOPECONTEXT-VECTOR-SPACE-0004 governance amendment (2026-09-03):
# narrow services/dope-context carve-out
# ---------------------------------------------------------------------------

def test_carved_out_dope_context_paths_are_not_forbidden_path_findings(tmp_path):
    repo_root = tmp_path / "tp_dopecontext_carveout_clean"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(
        changed_files=[
            "services/dope-context/eval/run_eval.py",
            "services/dope-context/eval/results/2026-09-03/run.md",
            "services/dope-context/src/pipeline/indexing_pipeline.py",
            "services/dope-context/src/mcp/server.py",
            "services/dope-context/tests/test_vector_space_invariants.py",
        ]
    )
    assert not any(f.category == "FORBIDDEN_PATH" for f in report.findings)


def test_other_dope_context_paths_still_forbidden_path_blocked(tmp_path):
    """Exact-file / single-directory carve-out — not a service-wide lift."""
    repo_root = tmp_path / "tp_dopecontext_carveout_other"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    for rel in (
        "services/dope-context/src/search/hybrid_search.py",
        "services/dope-context/src/mcp/server.py.bak",
        "services/dope-context/eval/../src/search/hybrid_search.py",
        "services/task-orchestrator/app/main.py",
    ):
        report = scanner.scan(changed_files=[rel])
        assert report.status == Status.BLOCKED, rel
        assert any(f.category == "FORBIDDEN_PATH" for f in report.findings), rel


def test_carved_out_dope_context_file_still_subject_to_text_rules(tmp_path):
    """Path-level carve-out must not exempt content-level TEXT_RULES scanning."""
    repo_root = tmp_path / "tp_dopecontext_carveout_text_rules"
    repo_root.mkdir()
    eval_dir = repo_root / "services" / "dope-context" / "eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "run_eval.py").write_text('os.system("gh pr merge --auto")\n')

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(changed_files=["services/dope-context/eval/run_eval.py"])
    assert report.status == Status.BLOCKED
    assert not any(f.category == "FORBIDDEN_PATH" for f in report.findings)
    assert any(f.category == "MERGE_SEAM_VIOLATION" for f in report.findings)


# ---------------------------------------------------------------------------
# TP-DMX-TRUST-GATE-FAIL-CLOSED-001: DMX-W1-04-F001 fail-closed completeness
# ---------------------------------------------------------------------------

def test_empty_proof_object_does_not_return_pass(tmp_path):
    """{} is parseable JSON but proves nothing; must not become PASS."""
    repo_root = tmp_path / "tp_trust_gate_empty_proof"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({}))

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"])
    assert report.status != Status.PASS
    assert report.guards.self_certification_status == "UNKNOWN"


def test_head_sha_only_proof_does_not_return_pass(tmp_path):
    """A proof carrying only head_sha (no identities) is an incomplete subset."""
    repo_root = tmp_path / "tp_trust_gate_head_only_proof"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({"head_sha": "expected123"}))

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"], expected_head_sha="expected123")
    assert report.status != Status.PASS
    assert report.guards.self_certification_status == "UNKNOWN"


def test_missing_implementer_identity_leaves_self_certification_unknown(tmp_path):
    repo_root = tmp_path / "tp_trust_gate_missing_implementer"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({"audit": {"auditor_identity": "Human"}}))

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"])
    assert report.guards.self_certification_status == "UNKNOWN"
    assert report.status != Status.PASS


def test_missing_auditor_identity_leaves_self_certification_unknown(tmp_path):
    repo_root = tmp_path / "tp_trust_gate_missing_auditor"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({"implementer_identity": "Agent"}))

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"])
    assert report.guards.self_certification_status == "UNKNOWN"
    assert report.status != Status.PASS


def test_distinct_identities_still_produce_none_self_certification(tmp_path):
    """Positive case: both identities present and distinct -> legitimately NONE, PASS reachable."""
    repo_root = tmp_path / "tp_trust_gate_distinct_identities"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({
        "implementer_identity": "Agent",
        "audit": {"auditor_identity": "Human"},
        "head_sha": "expected123",
    }))

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"], expected_head_sha="expected123")
    assert report.guards.self_certification_status == "NONE"
    assert report.status == Status.PASS


def test_malformed_proof_json_does_not_return_pass(tmp_path):
    repo_root = tmp_path / "tp_trust_gate_malformed_proof"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text('{"packet_id": "TP-DCP-0005",')  # truncated / invalid JSON

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan(proof_paths=["PROOF.json"])
    assert report.status != Status.PASS
    assert any(f.category == "MALFORMED_PROOF" for f in report.findings)


def test_no_proof_paths_supplied_does_not_return_pass(tmp_path):
    repo_root = tmp_path / "tp_trust_gate_no_proof"
    repo_root.mkdir()

    scanner = RedLaneScanner(repo_root=str(repo_root))
    report = scanner.scan()
    assert report.status != Status.PASS


def test_cli_exits_nonzero_on_incomplete_proof(tmp_path):
    import subprocess
    import sys as _sys
    from pathlib import Path as _Path

    repo_root = tmp_path / "tp_trust_gate_cli_incomplete"
    repo_root.mkdir()
    proof = repo_root / "PROOF.json"
    proof.write_text(json.dumps({}))

    src_dir = _Path(__file__).resolve().parents[2] / "src"
    result = subprocess.run(
        [
            _sys.executable,
            "-m",
            "dopemux.dcp.red_lane_scanner",
            "--repo-root",
            str(repo_root),
            "--proof-paths",
            "PROOF.json",
        ],
        cwd=str(src_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002: control-character
# fail-closed short-circuit in RedLaneScanner.
#
# Background: PR #1322 re-anchored every FORBIDDEN_PATHS entry from `$` to
# `\Z` and added re.DOTALL to every wildcard-bearing pattern, closing a
# bypass for those rules. But the small set of exact-match, non-wildcard
# rules (scripts/dopetask, scripts/taskx, both queue_drain.py variants,
# scripts/batch_resolve_and_merge.py) regressed on this consumer
# specifically: under the old `$`, a trailing newline used to accidentally
# still match, so e.g. "scripts/dopetask\n" used to be blocked; under `\Z`
# it silently was not, and unlike .claude/hooks/dcp_surface_guard.py this
# scanner had no independent control-character layer standing in front of
# it. This block proves that gap is closed.
#
# The wildcard-rule probes below originate from PR #1321 (donor SHA
# 353bd8b245beb2c137f1ef94b45227d885328fed, tests/dcp/test_dcp_0005_red_lane_
# scanner.py lines 457-500, fetched and hash-verified before porting). Their
# assertion is adapted, not copied verbatim: -002's short-circuit intercepts
# every control-character path *before* FORBIDDEN_PATHS matching, so such a
# path now always produces a MALFORMED_PATH_CONTROL_CHARACTER finding, never
# a FORBIDDEN_PATH one — including for paths that also fall under a
# forbidden subtree.
# ---------------------------------------------------------------------------

_CONTROL_CHARACTER_BLOCK_PROBES = (
    # Exact-match FORBIDDEN_PATHS rules — the -002 regression this packet
    # closes. Each was silently NOT blocked by the scanner before this fix.
    "scripts/dopetask\n",
    "scripts/taskx\r",
    "scripts/batch_resolve_and_merge.py\t",
    "src/dopemux_pr_merge_specialist/queue_drain.py\x7f",
    "dopemux_pr_merge_specialist/queue_drain.py\n",
    # Wildcard FORBIDDEN_PATHS rules — already safe after PR #1322's \Z +
    # re.DOTALL re-anchoring; ported from PR #1321 to prove they stay safe.
    "services/dope-context/src/\nsecret.py",
    "services/dope-context/src/index_profile.py\n",
    "services/task-orchestrator/x/\ny",
    "services/dope-context/src/index_profile.py\t",
    "services/dope-context/src/index_profile.py\r",
    # Exemption-spoof — a near-miss of an exact carve-out exemption plus a
    # trailing control character must still be blocked, not treated as the
    # exact exempted filename.
    ".github/workflows/embedded-audit.yml\n",
    # Arbitrary malformed path — not itself a forbidden path anywhere,
    # proving the fail-closed rule is unconditional, not scoped to protected
    # subtrees.
    "docs/readme.md\n",
    "some/totally/unrelated/file.txt\x01",
)


@pytest.mark.parametrize("fpath", _CONTROL_CHARACTER_BLOCK_PROBES)
def test_scanner_blocks_control_character_paths(tmp_path, fpath):
    # Each probe is its own parametrized case (not a loop-with-bare-assert)
    # so that under the anti-vacuity mutation in
    # proof/TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002/MUTATION_EVIDENCE.md
    # every probe's actual pass/fail status is independently visible in the
    # pytest report, rather than the loop stopping at the first failure and
    # leaving the remaining probes unexercised.
    repo_root = tmp_path / "tp_dcp_0005_control_char_bypass"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(changed_files=[fpath])
    assert report.status == Status.BLOCKED, fpath
    assert any(
        f.category == "MALFORMED_PATH_CONTROL_CHARACTER"
        for f in report.findings
    ), fpath


@pytest.mark.parametrize(
    "fpath",
    (
        ".github/workflows/embedded-audit.yml",
        ".github/workflows/pr-steward.yml",
        "services/dope-context/eval/run_eval.py",
        "services/dope-context/src/index_profile.py",
        "README.md",
        "path with a literal space and a tilde~",  # 0x20, 0x7E: not C0/DEL
    ),
)
def test_scanner_legitimate_paths_unaffected_by_control_char_guard(tmp_path, fpath):
    """Clean-control: legitimate paths at and near the C0/DEL boundary must
    be unaffected — the fix must not be satisfiable by over-blocking."""
    repo_root = tmp_path / "tp_dcp_0005_control_char_clean"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    report = scanner.scan(changed_files=[fpath])
    assert not any(
        f.category == "MALFORMED_PATH_CONTROL_CHARACTER"
        for f in report.findings
    ), fpath


def test_scanner_control_char_short_circuit_skips_filesystem_access(tmp_path):
    """A malformed path must never reach the source-text loop's
    os.path.exists/open — a control character in a real path could behave
    unpredictably across filesystems, so it must be rejected before any
    filesystem call is attempted for it.

    A malformed path is guaranteed not to exist on disk anyway, so
    asserting only the report's shape (as an earlier version of this test
    did) does not actually prove the filesystem loop was never reached --
    os.path.exists could still be called and simply return False. Patch
    both calls directly and assert they are never invoked, so a refactor
    that moved the control-character check after the filesystem probe
    would fail this test even though the report would look identical.
    """
    repo_root = tmp_path / "tp_dcp_0005_control_char_no_fs"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    with mock.patch("os.path.exists") as mock_exists, mock.patch(
        "builtins.open"
    ) as mock_open:
        report = scanner.scan(changed_files=["some/unrelated/file.txt\n"])

    mock_exists.assert_not_called()
    mock_open.assert_not_called()
    assert report.status == Status.BLOCKED
    assert any(
        f.category == "MALFORMED_PATH_CONTROL_CHARACTER"
        for f in report.findings
    )
    # No TEXT_RULES finding is possible for a path the filesystem loop never
    # touched — the only finding present is the short-circuit's own.
    assert len(report.findings) == 1


def test_scanner_reports_original_changed_files_even_when_blocked(tmp_path):
    """report.inputs.changed_files reflects exactly what the caller passed,
    including paths the control-character short-circuit removes from
    further processing — telemetry must stay honest about scan inputs."""
    repo_root = tmp_path / "tp_dcp_0005_control_char_inputs"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    probe = "scripts/dopetask\n"
    report = scanner.scan(changed_files=[probe])
    assert report.inputs.changed_files == [probe]
