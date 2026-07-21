from __future__ import annotations

import json
import subprocess

from tools.pr_steward.collector import (
    _fetch_changed_files_with_pagination_check,
    _select_security_release_approval,
)


def _review(**overrides):
    base = {
        "id": "R_1",
        "state": "APPROVED",
        "author": {"login": "trusted-approver"},
        "authorAssociation": "COLLABORATOR",
        "submittedAt": "2026-07-20T10:00:00Z",
        "commit": {"oid": "a" * 40},
    }
    base.update(overrides)
    return base


def test_no_reviews_returns_none():
    assert _select_security_release_approval([], repo="o/r", pr_number=1) is None


def test_single_approved_review_is_selected():
    result = _select_security_release_approval(
        [_review()], repo="owner/repo", pr_number=42
    )
    assert result is not None
    assert result["state"] == "APPROVED"
    assert result["approver"] == "trusted-approver"
    assert result["head_sha"] == "a" * 40
    assert result["approval_ref"] == "R_1"
    assert result["repository"] == "owner/repo"
    assert result["pr_number"] == 42
    assert result["approved_at"] == "2026-07-20T10:00:00Z"


def test_most_recent_approved_review_wins():
    older = _review(id="R_1", submittedAt="2026-07-20T09:00:00Z")
    newer = _review(id="R_2", submittedAt="2026-07-20T11:00:00Z")
    result = _select_security_release_approval([older, newer], repo="o/r", pr_number=1)
    assert result["approval_ref"] == "R_2"


def test_changes_requested_after_approval_is_not_selected_as_approved():
    approved = _review(id="R_1", state="APPROVED", submittedAt="2026-07-20T09:00:00Z")
    later_changes = _review(
        id="R_2", state="CHANGES_REQUESTED", author={"login": "trusted-approver"},
        submittedAt="2026-07-20T11:00:00Z",
    )
    result = _select_security_release_approval([approved, later_changes], repo="o/r", pr_number=1)
    assert result is None


def test_review_without_commit_oid_is_skipped():
    result = _select_security_release_approval(
        [_review(commit=None)], repo="o/r", pr_number=1
    )
    assert result is None


def _graphql_files_response(*, has_next_page: bool, paths: list[str]) -> str:
    return json.dumps(
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "files": {
                            "pageInfo": {
                                "hasNextPage": has_next_page,
                                "endCursor": "cursor",
                            },
                            "nodes": [{"path": path} for path in paths],
                        }
                    }
                }
            }
        }
    )


def test_changed_files_pagination_check_no_next_page_produces_no_error(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(has_next_page=False, paths=["a.py", "b.py"]),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    assert errors == []
    assert paths == ["a.py", "b.py"]


def test_changed_files_pagination_check_has_next_page_produces_harvest_error(
    monkeypatch,
):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(has_next_page=True, paths=["a.py"] * 100),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    assert errors == ["changedFiles harvest exceeded first 100 files"]
    assert len(paths) == 100


def test_changed_files_pagination_check_command_failure_produces_error(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(args, 1, "", "boom")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    assert paths == []
    assert errors == ["gh api graphql changedFiles failed: boom"]


def test_changed_files_reconciliation_matching_sets_produces_no_error(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(has_next_page=False, paths=["a.py", "b.py"]),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"]
    )
    assert errors == []
    assert paths == ["a.py", "b.py"]


def test_changed_files_reconciliation_diverging_sets_produces_harvest_error(
    monkeypatch,
):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(
                has_next_page=False, paths=["a.py", "b.py", "secret_workflow.yml"]
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"]
    )
    assert len(errors) == 1
    assert "changed_files harvest content mismatch" in errors[0]
    assert "REST reported 2 paths" in errors[0]
    assert "GraphQL reported 3 paths" in errors[0]
    assert "secret_workflow.yml" in errors[0]
    assert paths == ["a.py", "b.py", "secret_workflow.yml"]


def test_changed_files_reconciliation_skipped_when_graphql_has_next_page(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(has_next_page=True, paths=["a.py"] * 100),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py"]
    )
    # Pagination-overflow error only; content reconciliation is skipped because
    # the GraphQL side is known-incomplete and would trivially "differ".
    assert errors == ["changedFiles harvest exceeded first 100 files"]


def test_changed_files_reconciliation_not_run_when_rest_paths_omitted(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(has_next_page=False, paths=["a.py", "b.py"]),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    assert errors == []
    assert paths == ["a.py", "b.py"]
