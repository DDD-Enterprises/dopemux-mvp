"""E9 legacy --routing-policy deprecation coverage."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402


@pytest.mark.parametrize(
    ("legacy_policy", "expected_profile"),
    sorted(runner.LEGACY_ROUTING_POLICY_TO_COST_PROFILE.items()),
)
def test_every_legacy_routing_policy_resolves_to_expected_cost_profile(
    legacy_policy: str,
    expected_profile: str,
) -> None:
    name, profile = runner.resolve_cost_profile(legacy_policy)

    assert name == expected_profile
    assert profile is runner.COST_PROFILES[expected_profile]


def _run_print_config(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "RTE_DISABLE_LIVE_LLM_IN_TESTS": "1"}
    return subprocess.run(
        [
            sys.executable,
            str(SERVICE_ROOT / "run_extraction_v5.py"),
            "--phase",
            "A",
            "--run-id",
            "e9_legacy",
            "--output-root",
            str(tmp_path),
            *args,
            "--print-config",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _stdout_json(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout[result.stdout.find("{"):])


def test_cli_legacy_cost_policy_emits_deprecation_warning(tmp_path: Path) -> None:
    result = _run_print_config(tmp_path, "--routing-policy", "cost")

    assert result.returncode == 0
    assert "DEPRECATION: --routing-policy=cost is deprecated" in result.stderr
    assert "Migrate to --cost-profile=economy" in result.stderr
    assert _stdout_json(result)["cli"]["routing_policy"] == "cost"


def test_cli_legacy_balanced_openrouter_recommends_value_default(tmp_path: Path) -> None:
    result = _run_print_config(tmp_path, "--routing-policy", "balanced_openrouter")

    assert result.returncode == 0
    assert "Migrate to --cost-profile=value-default" in result.stderr
    assert _stdout_json(result)["cli"]["routing_policy"] == "balanced_openrouter"


def test_cli_legacy_optimal_recommends_quality(tmp_path: Path) -> None:
    result = _run_print_config(tmp_path, "--routing-policy", "optimal")

    assert result.returncode == 0
    assert "Migrate to --cost-profile=quality" in result.stderr
    assert _stdout_json(result)["cli"]["routing_policy"] == "quality"


def test_cost_profile_wins_when_both_new_and_legacy_flags_are_present(
    tmp_path: Path,
) -> None:
    result = _run_print_config(
        tmp_path,
        "--cost-profile",
        "economy",
        "--routing-policy",
        "quality",
    )

    assert result.returncode == 0
    assert "preferring --cost-profile and ignoring --routing-policy" in result.stderr
    assert _stdout_json(result)["cli"]["routing_policy"] == "cost"


def test_warning_message_names_the_recommended_new_flag(tmp_path: Path) -> None:
    result = _run_print_config(tmp_path, "--routing-policy", "gemini_primary")

    assert result.returncode == 0
    assert "--cost-profile=value-default" in result.stderr
    assert "--routing-policy=gemini_primary is deprecated" in result.stderr
