import os
import time

from file_activity_checker import FileActivityChecker


def test_recent_file_activity_detected(tmp_path):
    checker = FileActivityChecker(recency_threshold=60, file_patterns=[".py"])
    active_file = tmp_path / "recent.py"
    active_file.write_text("print('hi')\n")
    os.utime(active_file, (time.time(), time.time()))

    result = checker.check_recent_activity(str(tmp_path))

    assert result["has_recent_activity"] is True
    assert result["files_modified"] == 1
    assert result["most_recent_file"] == "recent.py"
    assert result["seconds_since_last_save"] is not None


def test_invalid_workspace_returns_empty_metrics():
    checker = FileActivityChecker()

    result = checker.check_recent_activity("/definitely/not/here")

    assert result == {
        "has_recent_activity": False,
        "files_modified": 0,
        "most_recent_file": None,
        "seconds_since_last_save": None,
    }
