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
    assert result["approver_association"] == "COLLABORATOR"
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
    # This mock ignores the cursor and always reports hasNextPage=True, simulating
    # a GraphQL response that never resolves to a final page (a genuine large PR
    # terminates after ceil(changedFiles/100) real pages; see
    # test_collector_changed_files_pagination_check.py for the realistic
    # multi-page-then-terminates case). The pagination loop now follows cursors
    # up to _MAX_CHANGED_FILES_PAGES before giving up and reporting incompleteness,
    # rather than bailing out after the first page as before.
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
    assert len(errors) == 1
    assert "changedFiles harvest exceeded" in errors[0]
    assert paths  # some paths were collected across pages, even though incomplete


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
    assert len(errors) == 1
    assert "changedFiles harvest exceeded" in errors[0]


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


def test_changed_files_non_string_path_in_graphql_response_is_safely_filtered(monkeypatch):
    """Verify that non-string path values (e.g., int, dict) are safely filtered out."""
    def fake_run(args):
        # Simulate a GraphQL response with mixed types: valid strings, an int, and a dict
        response = json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "files": {
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": "cursor",
                                },
                                "nodes": [
                                    {"path": "a.py"},
                                    {"path": 123},  # Non-string path: integer
                                    {"path": {"nested": "dict"}},  # Non-string path: dict
                                    {"path": "b.py"},
                                    {"path": None},  # None should also be filtered
                                    {"path": ""},  # Empty string passes type check but is falsy
                                ],
                            }
                        }
                    }
                }
            }
        )
        return subprocess.CompletedProcess(args, 0, response, "")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    # No rest_paths provided, so reconciliation is skipped
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    # Only the valid string paths should be returned; non-string values filtered out
    # Empty string is technically a string so it passes isinstance check
    assert errors == []
    assert paths == ["a.py", "b.py", ""]


def test_changed_files_non_string_path_with_rest_reconciliation(monkeypatch):
    """Verify that non-string paths don't crash the reconciliation logic."""
    def fake_run(args):
        # Simulate a GraphQL response with non-string path values
        response = json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "files": {
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": "cursor",
                                },
                                "nodes": [
                                    {"path": "a.py"},
                                    {"path": 42},  # Non-string integer
                                    {"path": "b.py"},
                                ],
                            }
                        }
                    }
                }
            }
        )
        return subprocess.CompletedProcess(args, 0, response, "")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    # Provide rest_paths that match the valid string paths; reconciliation should work
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"]
    )
    # No TypeError should be raised during set operations
    assert errors == []
    assert set(paths) == {"a.py", "b.py"}


def test_changed_files_non_string_dict_path_does_not_crash_sorted(monkeypatch):
    """Verify that a dict path value doesn't crash sorted() during reconciliation.

    Simulate a GraphQL response where one path is a dict (unhashable).
    This would crash sorted() if not properly filtered by the isinstance(path, str) guard.
    """
    def fake_run(args):
        # Simulate a GraphQL response where one path is a dict (unhashable)
        # The dict-valued path should be filtered out, not crash the reconciliation
        response = json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "files": {
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": "cursor",
                                },
                                "nodes": [
                                    {"path": "file1.py"},
                                    {"path": {"nested": "dict"}},  # Non-string dict path
                                    {"path": "file2.py"},
                                ],
                            }
                        }
                    }
                }
            }
        )
        return subprocess.CompletedProcess(args, 0, response, "")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    # Provide rest_paths that match only the valid string paths
    rest_paths = ["file1.py", "file2.py"]
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=rest_paths
    )
    # Should not raise TypeError when trying to add dict to set or sort
    # Dict-valued path should be filtered out, and reconciliation should succeed
    assert errors == []
    assert set(paths) == {"file1.py", "file2.py"}
    assert len(paths) == 2
    # Verify the dict path is NOT in the result
    assert all(isinstance(p, str) for p in paths)
