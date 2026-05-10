from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "services" / "repo-truth-extractor" / "run_extraction_v3.py"


def _run_v3(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("DPMX_LIVE_OK", None)
    env["RTE_DISABLE_LIVE_LLM_IN_TESTS"] = "1"
    return subprocess.run(
        [sys.executable, str(RUNNER_PATH), *args],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )


def test_v3_without_execute_refuses_before_artifacts(tmp_path: Path) -> None:
    proc = _run_v3(tmp_path, "--phase", "A", "--run-id", "no_execute")

    assert proc.returncode != 0
    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()


def test_v3_execute_without_live_env_refuses_before_artifacts(tmp_path: Path) -> None:
    proc = _run_v3(tmp_path, "--phase", "A", "--run-id", "no_env", "--execute")

    assert proc.returncode != 0
    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
    assert "DPMX_LIVE_OK=1" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
