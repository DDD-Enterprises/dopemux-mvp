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


def test_v3_read_only_phase_does_not_require_consent(tmp_path: Path) -> None:
    proc = _run_v3(tmp_path, "--phase", "A", "--print-run-order")

    assert "Legacy v3 live execution requires explicit consent" not in proc.stderr


def test_v3_preflight_providers_requires_consent(tmp_path: Path) -> None:
    proc = _run_v3(tmp_path, "--preflight-providers")

    assert proc.returncode != 0
    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()


def test_v3_preflight_providers_with_dry_run_still_requires_consent(tmp_path: Path) -> None:
    """--dry-run must not bypass consent for always-live provider-call flags."""
    proc = _run_v3(tmp_path, "--preflight-providers", "--dry-run")

    assert proc.returncode != 0
    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()


def test_v3_gemini_list_models_with_dry_run_still_requires_consent(tmp_path: Path) -> None:
    proc = _run_v3(tmp_path, "--gemini-list-models", "--dry-run")

    assert proc.returncode != 0
    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()


def test_v3_gemini_list_models_requires_consent(tmp_path: Path) -> None:
    proc = _run_v3(tmp_path, "--gemini-list-models")

    assert proc.returncode != 0
    assert "Legacy v3 live execution requires explicit consent" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()


def test_v3_phase_with_dry_run_does_not_require_consent(tmp_path: Path) -> None:
    """Phase execution honors --dry-run, so consent should not apply."""
    proc = _run_v3(tmp_path, "--phase", "A", "--run-id", "preview", "--dry-run")

    assert "Legacy v3 live execution requires explicit consent" not in proc.stderr


def test_v3_dry_run_and_execute_conflict_is_rejected(tmp_path: Path) -> None:
    proc = _run_v3(
        tmp_path,
        "--phase",
        "A",
        "--run-id",
        "conflict",
        "--dry-run",
        "--execute",
    )

    assert proc.returncode != 0
    assert "--execute and --dry-run are mutually exclusive" in proc.stderr
    assert not (tmp_path / "extraction" / "repo-truth-extractor" / "v3").exists()
