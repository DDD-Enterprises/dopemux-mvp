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


def _graphql_files_response(
    *, has_next_page: bool, paths: list[str], total_count: int | None = None
) -> str:
    return json.dumps(
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "files": {
                            "totalCount": (
                                len(paths) if total_count is None else total_count
                            ),
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
    calls = []

    def fake_run(args):
        calls.append(args)
        return subprocess.CompletedProcess(
            args,
            0,
            _graphql_files_response(
                has_next_page=True,
                paths=["a.py" if len(calls) == 1 else "b.py"],
                total_count=3,
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    assert len(errors) == 1
    assert "cursor" in errors[0]
    assert paths == ["a.py", "b.py"]


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
            _graphql_files_response(has_next_page=True, paths=["a.py"], total_count=1),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["different.py"]
    )
    # Pagination error only; content reconciliation is skipped because the
    # GraphQL side is known-incomplete and would add misleading duplicate noise.
    assert len(errors) == 1
    assert "hasNextPage" in errors[0]
    assert "content mismatch" not in errors[0]


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


def test_changed_files_non_string_path_in_graphql_response_fails_closed(monkeypatch):
    """Verify that malformed paths fail closed instead of being silently filtered."""

    def fake_run(args):
        # Simulate a GraphQL response with mixed types: valid strings, an int, and a dict
        response = json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "files": {
                                "totalCount": 6,
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": "cursor",
                                },
                                "nodes": [
                                    {"path": "a.py"},
                                    {"path": 123},  # Non-string path: integer
                                    {
                                        "path": {"nested": "dict"}
                                    },  # Non-string path: dict
                                    {"path": "b.py"},
                                    {"path": None},  # Also malformed
                                    {"path": ""},  # Empty path is malformed
                                ],
                            }
                        }
                    }
                }
            }
        )
        return subprocess.CompletedProcess(args, 0, response, "")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    # No rest_paths provided; malformed node still fails closed.
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )
    assert len(errors) == 1
    assert "malformed path" in errors[0]
    assert paths == ["a.py"]


def test_changed_files_non_string_path_skips_rest_reconciliation(monkeypatch):
    """Verify that malformed paths fail before set reconciliation."""

    def fake_run(args):
        # Simulate a GraphQL response with non-string path values
        response = json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "files": {
                                "totalCount": 3,
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
    # Malformed node blocks reconciliation even when valid paths otherwise match.
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"]
    )
    assert len(errors) == 1
    assert "malformed path" in errors[0]
    assert "content mismatch" not in errors[0]
    assert paths == ["a.py"]


def test_changed_files_dict_path_fails_closed_without_crashing_sorted(monkeypatch):
    """Verify that an unhashable path fails before set reconciliation."""

    def fake_run(args):
        # Simulate a GraphQL response where one path is a dict (unhashable)
        # The dict-valued path should fail before reconciliation can sort sets.
        response = json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "files": {
                                "totalCount": 3,
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": "cursor",
                                },
                                "nodes": [
                                    {"path": "file1.py"},
                                    {
                                        "path": {"nested": "dict"}
                                    },  # Non-string dict path
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
    assert len(errors) == 1
    assert "malformed path" in errors[0]
    assert "content mismatch" not in errors[0]
    assert paths == ["file1.py"]
