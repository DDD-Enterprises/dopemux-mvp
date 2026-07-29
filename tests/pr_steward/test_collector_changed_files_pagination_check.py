from __future__ import annotations

import subprocess

from tools.pr_steward.collector import (
    _MAX_CHANGED_FILES_PAGES,
    _fetch_changed_files_with_pagination_check,
)


def _graphql_response(paths: list[str], *, has_next_page: bool, end_cursor: str | None) -> str:
    nodes = ",".join(f'{{"path": "{p}"}}' for p in paths)
    cursor_json = f'"{end_cursor}"' if end_cursor is not None else "null"
    return (
        '{"data": {"repository": {"pullRequest": {"files": {'
        f'"pageInfo": {{"hasNextPage": {"true" if has_next_page else "false"}, "endCursor": {cursor_json}}}, '
        f'"nodes": [{nodes}]'
        "}}}}}"
    )


def test_single_page_under_100_files_no_pagination_error(monkeypatch):
    def fake_run(args):
        assert "cursor=" not in " ".join(args)
        return subprocess.CompletedProcess(
            args, 0, _graphql_response(["a.py", "b.py"], has_next_page=False, end_cursor=None), ""
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"])
    assert errors == []
    assert sorted(paths) == ["a.py", "b.py"]


def test_multi_page_pull_request_paginates_past_first_100(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        if len(calls) == 1:
            assert "cursor=CURSOR1" not in " ".join(args)
            return subprocess.CompletedProcess(
                args, 0, _graphql_response(["a.py"], has_next_page=True, end_cursor="CURSOR1"), ""
            )
        assert any(a == "cursor=CURSOR1" for a in args)
        return subprocess.CompletedProcess(
            args, 0, _graphql_response(["b.py"], has_next_page=False, end_cursor=None), ""
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1152, rest_paths=["a.py", "b.py"]
    )
    assert errors == []
    assert sorted(paths) == ["a.py", "b.py"]
    assert len(calls) == 2


def test_pagination_never_resolving_reports_error_not_silent_truncation(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args, 0, _graphql_response(["x.py"], has_next_page=True, end_cursor="SAME"), ""
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(repo="owner/repo", pr_number=1, rest_paths=["x.py"])
    assert len(errors) == 1
    assert "changedFiles harvest exceeded" in errors[0]
    assert f"{_MAX_CHANGED_FILES_PAGES}" in errors[0]


def test_has_next_page_without_cursor_reports_incomplete_not_silently_done(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args, 0, _graphql_response(["x.py"], has_next_page=True, end_cursor=None), ""
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(repo="owner/repo", pr_number=1, rest_paths=["x.py"])
    assert len(errors) == 1
    assert "changedFiles harvest exceeded" in errors[0]


def test_reconciliation_mismatch_still_reported_after_full_pagination(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args, 0, _graphql_response(["a.py"], has_next_page=False, end_cursor=None), ""
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"]
    )
    assert len(errors) == 1
    assert "content mismatch" in errors[0]


def test_api_failure_on_second_page_blocks_harvest(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        if len(calls) == 1:
            return subprocess.CompletedProcess(
                args, 0, _graphql_response(["a.py"], has_next_page=True, end_cursor="CURSOR1"), ""
            )
        return subprocess.CompletedProcess(args, 1, "", "rate limited")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(repo="owner/repo", pr_number=1, rest_paths=None)
    assert paths == []
    assert len(errors) == 1
    assert "gh api graphql changedFiles failed" in errors[0]
