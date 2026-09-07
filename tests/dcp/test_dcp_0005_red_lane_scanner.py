import os
import json
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
# TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-001: FORBIDDEN_PATHS is consumed
# here via `pattern.match(fpath)` (start-anchored, not full-string) — a
# different call shape than dcp_surface_guard's `pattern.search(rel)`. Both
# consumers must independently fail closed on an embedded/trailing control
# character.
# ---------------------------------------------------------------------------

_NEWLINE_BYPASS_SCANNER_PROBES = (
    "services/dope-context/src/\nsecret.py",
    "services/dope-context/src/index_profile.py\n",
    ".github/workflows/embedded-audit.yml\n",
    "services/task-orchestrator/x/\ny",
    "services/dope-context/src/index_profile.py\t",
    "services/dope-context/src/index_profile.py\r",
)


def test_scanner_blocks_newline_and_control_character_paths(tmp_path):
    # TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002: donor assertion adapted.
    # Every probe below contains a control character, so under the new
    # unconditional short-circuit (§2/§3.1 of the -002 packet) it is now
    # rejected by MALFORMED_PATH_CONTROL_CHARACTER before FORBIDDEN_PATHS
    # matching ever runs -- these paths are never reached by the FORBIDDEN_PATH
    # rule in normal operation, only under the isolated mutation in
    # test_isolated_mutation_control_character_short_circuit below (where the
    # short-circuit is disabled and the six wildcard/exemption-spoof probes in
    # that mutation test fall through to the still-safe, unmutated
    # FORBIDDEN_PATH rule instead).
    repo_root = tmp_path / "tp_dcp_0005_newline_bypass"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    for fpath in _NEWLINE_BYPASS_SCANNER_PROBES:
        report = scanner.scan(changed_files=[fpath])
        assert report.status == Status.BLOCKED, fpath
        assert any(
            f.category == "MALFORMED_PATH_CONTROL_CHARACTER" for f in report.findings
        ), fpath


def test_scanner_legitimate_exemptions_unaffected(tmp_path):
    repo_root = tmp_path / "tp_dcp_0005_exemptions_unaffected"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    for fpath in (
        ".github/workflows/embedded-audit.yml",
        ".github/workflows/pr-steward.yml",
        "services/dope-context/eval/run_eval.py",
        "services/dope-context/src/index_profile.py",
    ):
        report = scanner.scan(changed_files=[fpath])
        assert not any(f.category == "FORBIDDEN_PATH" for f in report.findings), fpath


# ---------------------------------------------------------------------------
# TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002: full regression matrix per
# packet section 3.2, supersedes the "port only" plan the -001-era donor block
# above was limited to. Covers the newly-discovered exact-match gap, arbitrary
# malformed paths (proving the rule is unconditional, not scoped to protected
# subtrees), and the clean-control boundary (paths that must remain
# unaffected).
# ---------------------------------------------------------------------------

_EXACT_MATCH_CONTROL_CHAR_PROBES = (
    "scripts/dopetask\n",
    "scripts/taskx\r",
    "scripts/batch_resolve_and_merge.py\t",
    "src/dopemux_pr_merge_specialist/queue_drain.py\x7f",
    "dopemux_pr_merge_specialist/queue_drain.py\n",
)

_ARBITRARY_MALFORMED_PROBES = (
    "docs/readme.md\n",
    "some/totally/unrelated/file.txt\x01",
)

_CLEAN_CONTROL_BOUNDARY_PATHS = (
    ".github/workflows/embedded-audit.yml",
    ".github/workflows/pr-steward.yml",
    "services/dope-context/eval/run_eval.py",
    "services/dope-context/src/index_profile.py",
    "README.md",
    "path with a literal space and a tilde~",  # 0x20, 0x7E: not C0/DEL
)


def test_scanner_blocks_exact_match_control_character_paths(tmp_path):
    """The bug this packet exists to fix: PR #1322's \\Z re-anchoring is
    correct in isolation but regressed these five exact-match FORBIDDEN_PATHS
    rules specifically, since they have no `.*`/DOTALL and (before this
    packet) the scanner had no independent control-character short-circuit.
    """
    repo_root = tmp_path / "tp_dcp_0005_exact_match_control_char"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    for fpath in _EXACT_MATCH_CONTROL_CHAR_PROBES:
        report = scanner.scan(changed_files=[fpath])
        assert report.status == Status.BLOCKED, fpath
        assert any(
            f.category == "MALFORMED_PATH_CONTROL_CHARACTER" for f in report.findings
        ), fpath


def test_scanner_blocks_arbitrary_malformed_paths_unconditionally(tmp_path):
    """The short-circuit must be unconditional -- not scoped to any protected
    subtree or existing FORBIDDEN_PATHS entry."""
    repo_root = tmp_path / "tp_dcp_0005_arbitrary_malformed"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    for fpath in _ARBITRARY_MALFORMED_PROBES:
        report = scanner.scan(changed_files=[fpath])
        assert report.status == Status.BLOCKED, fpath
        assert any(
            f.category == "MALFORMED_PATH_CONTROL_CHARACTER" for f in report.findings
        ), fpath


def test_scanner_clean_control_boundary_paths_unaffected(tmp_path):
    """Legitimate paths at and near the C0/DEL boundary (including a literal
    space 0x20 and tilde 0x7E, neither of which is a control character) must
    never trip the new short-circuit."""
    repo_root = tmp_path / "tp_dcp_0005_clean_control_boundary"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    for fpath in _CLEAN_CONTROL_BOUNDARY_PATHS:
        report = scanner.scan(changed_files=[fpath])
        assert not any(
            f.category == "MALFORMED_PATH_CONTROL_CHARACTER" for f in report.findings
        ), fpath


def test_scanner_short_circuit_skips_filesystem_access(tmp_path, monkeypatch):
    """PR #1325 review finding (thread PRRT_kwDOPyIw986fySn2): a shape-only
    assertion on the report can pass even if a later refactor moves the
    short-circuit after the filesystem loop. Assert the actual invariant:
    os.path.exists/open are never invoked for a malformed path."""
    import os as os_module
    from unittest import mock

    repo_root = tmp_path / "tp_dcp_0005_fs_non_invocation"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    with mock.patch.object(os_module.path, "exists") as mock_exists, mock.patch(
        "builtins.open"
    ) as mock_open:
        report = scanner.scan(changed_files=["scripts/dopetask\n"])

    assert report.status == Status.BLOCKED
    mock_exists.assert_not_called()
    mock_open.assert_not_called()


def test_isolated_mutation_control_character_short_circuit(monkeypatch, tmp_path):
    """Anti-vacuity mutation per packet section 4/9: disable *only* the new
    short-circuit (via a test-only monkeypatch, not a source edit) and
    collect every probe's actual result before asserting any expectation.
    Expected split: the 5 exact-match + 2 arbitrary-malformed probes (7 total)
    revert fully to Status.UNKNOWN with zero findings -- the true original
    bypass this packet closes. The 6 wildcard/exemption-spoof probes remain
    Status.BLOCKED via the independent, unmutated FORBIDDEN_PATH rule; only
    their finding category is absent (MALFORMED_PATH_CONTROL_CHARACTER no
    longer fires), never their status. Reporting all 13 as reverting to
    UNKNOWN would be the exact accuracy defect a live PR #1325 review finding
    (thread PRRT_kwDOPyIw986fya9B) caught in round 2 of the unauthorized
    implementation this packet supersedes -- this test exists to make that
    inaccuracy impossible to reintroduce silently.
    """
    import dopemux.dcp.red_lane_scanner as scanner_module

    assert scanner_module._has_control_chars("x\n") is True  # pre-mutation sanity check
    monkeypatch.setattr(scanner_module, "_has_control_chars", lambda s: False)
    assert scanner_module._has_control_chars("x\n") is False  # mutation landed, non-zero effect

    repo_root = tmp_path / "tp_dcp_0005_isolated_mutation"
    repo_root.mkdir()
    scanner = RedLaneScanner(repo_root=str(repo_root))

    all_probes = (
        list(_EXACT_MATCH_CONTROL_CHAR_PROBES)
        + list(_ARBITRARY_MALFORMED_PROBES)
        + list(_NEWLINE_BYPASS_SCANNER_PROBES)
    )
    results = []
    for fpath in all_probes:
        report = scanner.scan(changed_files=[fpath])
        results.append(
            {
                "probe_id": fpath,
                "probe_class": (
                    "exact_match"
                    if fpath in _EXACT_MATCH_CONTROL_CHAR_PROBES
                    else "arbitrary_malformed"
                    if fpath in _ARBITRARY_MALFORMED_PROBES
                    else "wildcard_exemption_spoof"
                ),
                "actual_status": report.status,
                "finding_categories": sorted({f.category for f in report.findings}),
            }
        )

    reverted = [
        r
        for r in results
        if r["probe_class"] in ("exact_match", "arbitrary_malformed")
    ]
    still_blocked = [r for r in results if r["probe_class"] == "wildcard_exemption_spoof"]

    assert len(reverted) == 7, results
    for r in reverted:
        assert r["actual_status"] == Status.UNKNOWN, r
        assert r["finding_categories"] == [], r

    assert len(still_blocked) == 6, results
    for r in still_blocked:
        assert r["actual_status"] == Status.BLOCKED, r
        assert "MALFORMED_PATH_CONTROL_CHARACTER" not in r["finding_categories"], r
        assert "FORBIDDEN_PATH" in r["finding_categories"], r
