from __future__ import annotations

import json
import subprocess

from tools.pr_steward.collector import _fetch_changed_files_rest


def _paginate_response(pages: list[list[dict]]) -> str:
    # `gh api ... --paginate` prints one JSON array per page, newline separated.
    return "\n".join(json.dumps(page) for page in pages)


def test_ordinary_files_are_normalized(monkeypatch):
    def fake_run(args):
        assert args[:2] == ["gh", "api"]
        assert "--paginate" in args
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response(
                [[{"filename": "src/foo.py", "status": "modified", "additions": 1, "deletions": 0}]]
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert errors == []
    assert files == [
        {
            "path": "src/foo.py",
            "additions": 1,
            "deletions": 0,
            "status": "modified",
            "previous_path": None,
        }
    ]


def test_renamed_file_carries_previous_path(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response(
                [
                    [
                        {
                            "filename": "docs/deploy.yml",
                            "previous_filename": ".github/workflows/deploy.yml",
                            "status": "renamed",
                            "additions": 0,
                            "deletions": 0,
                        }
                    ]
                ]
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert errors == []
    assert files == [
        {
            "path": "docs/deploy.yml",
            "additions": 0,
            "deletions": 0,
            "status": "renamed",
            "previous_path": ".github/workflows/deploy.yml",
        }
    ]


def test_renamed_file_missing_previous_filename_blocks_harvest(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response(
                [[{"filename": "docs/deploy.yml", "status": "renamed", "additions": 0, "deletions": 0}]]
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert files == []
    assert len(errors) == 1
    assert "renamed" in errors[0] and "previous_filename" in errors[0]


def test_renamed_file_empty_previous_filename_blocks_harvest(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response(
                [
                    [
                        {
                            "filename": "docs/deploy.yml",
                            "previous_filename": "",
                            "status": "renamed",
                            "additions": 0,
                            "deletions": 0,
                        }
                    ]
                ]
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert files == []
    assert len(errors) == 1


def test_multiple_pages_are_concatenated(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response(
                [
                    [{"filename": "a.py", "status": "modified", "additions": 1, "deletions": 0}],
                    [{"filename": "b.py", "status": "added", "additions": 1, "deletions": 0}],
                ]
            ),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert errors == []
    assert [f["path"] for f in files] == ["a.py", "b.py"]


def test_api_failure_blocks_harvest(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(args, 1, "", "rate limited")

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert files == []
    assert len(errors) == 1
    assert "gh api pulls/files failed" in errors[0]


def test_malformed_page_entry_is_reported_and_skipped(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response([[{"filename": "a.py", "status": "modified", "additions": 0, "deletions": 0}, "not-a-mapping"]]),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert [f["path"] for f in files] == ["a.py"]
    assert len(errors) == 1
    assert "not a mapping" in errors[0]


def test_missing_filename_is_reported_and_skipped(monkeypatch):
    def fake_run(args):
        return subprocess.CompletedProcess(
            args,
            0,
            _paginate_response([[{"status": "modified", "additions": 0, "deletions": 0}]]),
            "",
        )

    monkeypatch.setattr("tools.pr_steward.collector._run", fake_run)
    files, errors = _fetch_changed_files_rest(repo="owner/repo", pr_number=1)
    assert files == []
    assert len(errors) == 1
    assert "no filename" in errors[0]
