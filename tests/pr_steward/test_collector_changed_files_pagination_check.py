from __future__ import annotations

import json
import math
import subprocess

import pytest

from tools.pr_steward.collector import _fetch_changed_files_with_pagination_check


def _graphql_response(
    paths: list[object],
    *,
    total_count: object,
    has_next_page: object,
    end_cursor: object,
) -> str:
    return json.dumps(
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "files": {
                            "totalCount": total_count,
                            "pageInfo": {
                                "hasNextPage": has_next_page,
                                "endCursor": end_cursor,
                            },
                            "nodes": [{"path": path} for path in paths],
                        }
                    }
                }
            }
        }
    )


def _completed(args: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args, 0, stdout, "")


@pytest.mark.parametrize("file_count", [0, 99, 100, 101, 20_000, 20_001])
def test_valid_file_count_boundaries_complete_without_size_ceiling(
    monkeypatch, file_count
):
    expected_paths = [f"path-{index:05d}.py" for index in range(file_count)]
    calls: list[list[str]] = []

    def fake_run(args):
        page_index = len(calls)
        calls.append(args)
        expected_request_cursor = None if page_index == 0 else f"CURSOR-{page_index}"
        cursor_args = [arg for arg in args if arg.startswith("cursor=")]
        assert cursor_args == (
            []
            if expected_request_cursor is None
            else [f"cursor={expected_request_cursor}"]
        )
        start = page_index * 100
        end = min(start + 100, file_count)
        has_next_page = end < file_count
        end_cursor = f"CURSOR-{page_index + 1}" if has_next_page else None
        return _completed(
            args,
            _graphql_response(
                expected_paths[start:end],
                total_count=file_count,
                has_next_page=has_next_page,
                end_cursor=end_cursor,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=expected_paths
    )

    assert errors == []
    assert paths == expected_paths
    assert len(calls) == max(1, math.ceil(file_count / 100))
    assert "totalCount" in next(
        arg.removeprefix("query=") for arg in calls[0] if arg.startswith("query=")
    )


@pytest.mark.parametrize("end_cursor", [None, "", "   "])
def test_has_next_page_requires_non_empty_cursor(monkeypatch, end_cursor):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                ["a.py"],
                total_count=2,
                has_next_page=True,
                end_cursor=end_cursor,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == ["a.py"]
    assert len(errors) == 1
    assert "cursor" in errors[0]


def test_repeated_cursor_fails_before_third_request(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        path = "a.py" if len(calls) == 1 else "b.py"
        return _completed(
            args,
            _graphql_response(
                [path],
                total_count=3,
                has_next_page=True,
                end_cursor="SAME",
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == ["a.py", "b.py"]
    assert len(calls) == 2
    assert len(errors) == 1
    assert "cursor" in errors[0]


def test_empty_progress_page_fails_closed(monkeypatch):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                [],
                total_count=1,
                has_next_page=True,
                end_cursor="CURSOR-1",
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == []
    assert len(errors) == 1
    assert "no paths" in errors[0]


def test_total_count_change_between_pages_fails_closed(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        if len(calls) == 1:
            return _completed(
                args,
                _graphql_response(
                    ["a.py"],
                    total_count=2,
                    has_next_page=True,
                    end_cursor="CURSOR-1",
                ),
            )
        return _completed(
            args,
            _graphql_response(
                ["b.py"],
                total_count=3,
                has_next_page=False,
                end_cursor=None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == ["a.py"]
    assert len(errors) == 1
    assert "totalCount changed" in errors[0]


@pytest.mark.parametrize("total_count", [None, -1, True, 1.5, "1"])
def test_malformed_total_count_fails_closed(monkeypatch, total_count):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                [],
                total_count=total_count,
                has_next_page=False,
                end_cursor=None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == []
    assert len(errors) == 1
    assert "totalCount" in errors[0]


def test_duplicate_path_across_pages_fails_closed(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        return _completed(
            args,
            _graphql_response(
                ["duplicate.py"],
                total_count=2,
                has_next_page=len(calls) == 1,
                end_cursor="CURSOR-1" if len(calls) == 1 else None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == ["duplicate.py"]
    assert len(errors) == 1
    assert "duplicate path" in errors[0]


def test_collected_count_exceeding_total_count_fails_closed(monkeypatch):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                ["a.py", "b.py"],
                total_count=1,
                has_next_page=False,
                end_cursor=None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == ["a.py", "b.py"]
    assert len(errors) == 1
    assert "exceeded totalCount" in errors[0]


def test_final_collected_count_must_equal_total_count(monkeypatch):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                ["a.py"],
                total_count=2,
                has_next_page=False,
                end_cursor=None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == ["a.py"]
    assert len(errors) == 1
    assert "differed from totalCount" in errors[0]


def test_graphql_errors_fail_closed(monkeypatch):
    def fake_run(args):
        return _completed(
            args,
            json.dumps(
                {
                    "errors": [{"message": "resolver failed"}],
                    "data": {"repository": None},
                }
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == []
    assert len(errors) == 1
    assert "GraphQL errors" in errors[0]


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"data": []},
        {"data": {"repository": None}},
        {"data": {"repository": {"pullRequest": None}}},
        {"data": {"repository": {"pullRequest": {"files": None}}}},
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "files": {
                            "totalCount": 0,
                            "pageInfo": None,
                            "nodes": [],
                        }
                    }
                }
            }
        },
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "files": {
                            "totalCount": 0,
                            "pageInfo": {
                                "hasNextPage": False,
                                "endCursor": None,
                            },
                            "nodes": None,
                        }
                    }
                }
            }
        },
    ],
)
def test_malformed_graphql_container_shapes_fail_closed(monkeypatch, payload):
    def fake_run(args):
        return _completed(args, json.dumps(payload))

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == []
    assert len(errors) == 1
    assert "malformed" in errors[0]


@pytest.mark.parametrize(
    "path",
    [None, "", 123, {"nested": "mapping"}],
)
def test_malformed_node_path_fails_closed(monkeypatch, path):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                [path],
                total_count=1,
                has_next_page=False,
                end_cursor=None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == []
    assert len(errors) == 1
    assert "node" in errors[0]


def test_second_page_api_failure_blocks_harvest(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        if len(calls) == 1:
            return _completed(
                args,
                _graphql_response(
                    ["a.py"],
                    total_count=2,
                    has_next_page=True,
                    end_cursor="CURSOR-1",
                ),
            )
        return subprocess.CompletedProcess(args, 1, "", "rate limited")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1
    )

    assert paths == []
    assert len(errors) == 1
    assert "gh api graphql changedFiles failed" in errors[0]


def test_rest_graphql_path_set_mismatch_fails_closed(monkeypatch):
    def fake_run(args):
        return _completed(
            args,
            _graphql_response(
                ["a.py"],
                total_count=1,
                has_next_page=False,
                end_cursor=None,
            ),
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    paths, errors = _fetch_changed_files_with_pagination_check(
        repo="owner/repo", pr_number=1, rest_paths=["a.py", "b.py"]
    )

    assert paths == ["a.py"]
    assert len(errors) == 1
    assert "content mismatch" in errors[0]
