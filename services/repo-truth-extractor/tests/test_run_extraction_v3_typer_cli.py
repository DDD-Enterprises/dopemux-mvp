from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _runner_script() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"


def test_cli_help_includes_expected_flags(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--help"],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    assert "--phase" in result.stdout
    assert "--status-json" in result.stdout
    assert "--doctor" in result.stdout


def test_cli_status_json_stable_output(tmp_path: Path) -> None:
    run_id = "test_status_json"
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--status-json", "--run-id", run_id],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_id"] == run_id
    assert "summary" in payload
    assert "phases" in payload
