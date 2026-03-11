from pathlib import Path

from dopemux.commands.extractor_commands import _extractor_runner_path


def test_extractor_runner_path_routes_v5() -> None:
    repo_root = Path("/tmp/repo")
    runner = _extractor_runner_path(repo_root, "v5")
    assert runner.name == "run_extraction_v5.py"


def test_extractor_runner_path_routes_v4() -> None:
    repo_root = Path("/tmp/repo")
    runner = _extractor_runner_path(repo_root, "v4")
    assert runner.name == "run_extraction_v4.py"


def test_extractor_runner_path_falls_back_to_v3() -> None:
    repo_root = Path("/tmp/repo")
    runner = _extractor_runner_path(repo_root, "v3")
    assert runner.name == "run_extraction_v3.py"
