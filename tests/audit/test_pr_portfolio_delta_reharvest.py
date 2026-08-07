import json
import os
import shutil
import zipfile
import pytest
from pathlib import Path

from scripts.audit.pr_portfolio_delta_reharvest import (
    fetch_pr_details_graphql,
    handle_rebuild_zip,
    build_normalized_zip,
    compute_single_pair_topology,
    compute_pr_git_topology,
    sha256_file
)


def test_reconciliation_exact_match_and_mismatch(monkeypatch):
    """
    S1: Proves exact file count reconciliation and closed failure on mismatch (no +/-1 tolerance for generic PRs).
    """
    def fake_run_cmd(cmd):
        if "graphql" in cmd:
            query_data = {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "changedFiles": 10,
                            "reviewDecision": "APPROVED",
                            "reviews": {"nodes": []},
                            "files": {
                                "totalCount": 9,
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                                "nodes": [{"path": f"file{i}.py", "additions": 1, "deletions": 0} for i in range(9)]
                            }
                        }
                    }
                }
            }
            return json.dumps(query_data)
        elif "git diff" in cmd:
            return "\n".join([f"file{i}.py" for i in range(9)])
        return ""

    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd", fake_run_cmd)

    # 9 collected vs 10 aggregate => MUST fail closed (not reconciled)
    details = fetch_pr_details_graphql(999)
    assert details["file_count"] == 9
    assert details["aggregate_changed_files"] == 10
    assert details["file_count_reconciled"] is False

    # Exact match test (10 collected vs 10 aggregate)
    def fake_run_cmd_exact(cmd):
        if "graphql" in cmd:
            query_data = {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "changedFiles": 10,
                            "reviewDecision": "APPROVED",
                            "reviews": {"nodes": []},
                            "files": {
                                "totalCount": 10,
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                                "nodes": [{"path": f"file{i}.py", "additions": 1, "deletions": 0} for i in range(10)]
                            }
                        }
                    }
                }
            }
            return json.dumps(query_data)
        elif "git diff" in cmd:
            return "\n".join([f"file{i}.py" for i in range(10)])
        return ""

    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd", fake_run_cmd_exact)
    details_exact = fetch_pr_details_graphql(998)
    assert details_exact["file_count"] == 10
    assert details_exact["aggregate_changed_files"] == 10
    assert details_exact["file_count_reconciled"] is True

    # Documented exception for PR 1123 (16205 vs 16206)
    def fake_run_cmd_1123(cmd):
        if "graphql" in cmd:
            query_data = {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "changedFiles": 16206,
                            "reviewDecision": "NONE",
                            "reviews": {"nodes": []},
                            "files": {
                                "totalCount": 16205,
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                                "nodes": [{"path": f"file{i}.py", "additions": 1, "deletions": 0} for i in range(16205)]
                            }
                        }
                    }
                }
            }
            return json.dumps(query_data)
        elif "git diff" in cmd:
            return "\n".join([f"file{i}.py" for i in range(16205)])
        return ""

    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd", fake_run_cmd_1123)
    details_1123 = fetch_pr_details_graphql(1123)
    assert details_1123["file_count_reconciled"] is True
    assert details_1123["exception_reason"] is not None


def test_rebuild_zip_offline_no_network_or_git(tmp_path, monkeypatch):
    """
    S1: Proves --rebuild-zip executes completely offline without network or Git calls.
    """
    # Create fake frozen evidence artifacts
    artifacts = [
        "OBSERVATION_SNAPSHOT.json",
        "OPEN_PR_LEDGER.csv",
        "PR_TOPOLOGY.json",
        "PR_TOPOLOGY.csv",
        "PAIR_RELATIONSHIPS.json",
        "PAIR_RELATIONSHIPS.csv",
        "CAPABILITY_PREFLIGHT.md",
        "DELTA_REHARVEST_REPORT.md"
    ]
    sums = []
    for art in artifacts:
        fp = tmp_path / art
        content = f"sample content for {art}\n"
        fp.write_text(content, encoding="utf-8")
        h = sha256_file(fp)
        sums.append(f"{h}  {art}")

    sha_file = tmp_path / "SHA256SUMS.txt"
    sha_file.write_text("\n".join(sums) + "\n", encoding="utf-8")

    # Forbid subprocess / run_cmd / network calls
    def forbid_network(*args, **kwargs):
        pytest.fail("Network or Git command was invoked during offline rebuild mode!")

    monkeypatch.setattr("subprocess.run", forbid_network)
    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd", forbid_network)

    # handle_rebuild_zip calls sys.exit(0) on success
    with pytest.raises(SystemExit) as exc:
        handle_rebuild_zip(tmp_path)
    assert exc.value.code == 0

    assert (tmp_path / "portfolio_reharvest.zip").exists()
    assert (tmp_path / "portfolio_reharvest.zip.sha256").exists()


def test_rebuild_zip_reproducibility(tmp_path):
    """
    S1: Proves two consecutive offline rebuilds from identical inputs produce identical SHA-256.
    """
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    out1.mkdir()
    out2.mkdir()

    artifacts = [
        "OBSERVATION_SNAPSHOT.json",
        "OPEN_PR_LEDGER.csv",
        "PR_TOPOLOGY.json",
        "PR_TOPOLOGY.csv",
        "PAIR_RELATIONSHIPS.json",
        "PAIR_RELATIONSHIPS.csv",
        "CAPABILITY_PREFLIGHT.md",
        "DELTA_REHARVEST_REPORT.md"
    ]

    for out_dir in (out1, out2):
        sums = []
        for art in artifacts:
            fp = out_dir / art
            content = f"deterministic content for {art}\n"
            fp.write_text(content, encoding="utf-8")
            h = sha256_file(fp)
            sums.append(f"{h}  {art}")
        (out_dir / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")

    sha1 = build_normalized_zip(out1, artifacts)
    sha2 = build_normalized_zip(out2, artifacts)

    assert sha1 == sha2


def test_pair_relationships_multi_axis_and_no_independent_from_path(monkeypatch):
    """
    S3: Proves multi-axis pair evidence and no pair classified INDEPENDENT solely from path disjointness.
    """
    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd_bool", lambda cmd: False)

    pr_a = {"number": 100, "headRefOid": "shaA", "headRefName": "feat/a", "baseRefName": "main", "files": ["a.txt"]}
    pr_b = {"number": 101, "headRefOid": "shaB", "headRefName": "feat/b", "baseRefName": "main", "files": ["b.txt"]}
    top_map = {
        100: {"head_tree": "treeA"},
        101: {"head_tree": "treeB"}
    }

    pair = compute_single_pair_topology(pr_a, pr_b, top_map)

    assert pair["path_relation"] == "PATH_DISJOINT"
    assert pair["ancestry_relation"] == "NO_ANCESTRY_RELATION"
    assert pair["stack_relation"] == "NO_STACK_RELATION"
    assert pair["candidate_classification"] == "PATH_DISJOINT_UNSTACKED"
    assert pair["candidate_classification"] != "INDEPENDENT"


def test_pr_topology_non_main_base_resolution(monkeypatch):
    """
    S2: Proves non-main baseRefName resolves predecessor PR and detects drift correctly.
    """
    def fake_run_cmd(cmd):
        if "rev-parse" in cmd and "tree" in cmd:
            return "treeSHA"
        if "rev-parse" in cmd:
            return "dummySHA"
        if "merge-base" in cmd and "--count" not in cmd:
            return "mbSHA"
        if "rev-list" in cmd:
            return "1"
        return ""

    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd", fake_run_cmd)

    # Ancestry check returns False => base_drift_detected = True
    monkeypatch.setattr("scripts.audit.pr_portfolio_delta_reharvest.run_cmd_bool", lambda cmd: False)

    pr_1183 = {"number": 1183, "headRefOid": "sha1183", "headRefName": "feat/1183", "baseRefName": "claude/rte-truth-program"}
    open_prs_map = {
        "claude/rte-truth-program": {"number": 1136, "headRefOid": "sha1136", "headRefName": "claude/rte-truth-program"}
    }

    top = compute_pr_git_topology(pr_1183, open_prs_map)

    assert top["is_non_main_base"] is True
    assert top["predecessor_pr"] == 1136
    assert top["predecessor_head_sha"] == "sha1136"
    assert top["base_drift_detected"] is True
    assert top["topology_class"] == "STACKED_ON_OPEN_PR"
