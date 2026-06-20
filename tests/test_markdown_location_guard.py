import subprocess
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def _markdown_location_guard_script() -> str:
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text())
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if hook.get("id") == "markdown-location-guard":
                return hook["args"][0]
    raise AssertionError("markdown-location-guard hook not found")


def _run_guard(*paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", _markdown_location_guard_script(), "--", *paths],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_openclaw_dcp_contract_markdown_is_allowed():
    result = _run_guard(
        "contracts/openclaw-dcp-routing/runner_adapter_contract.md",
        "contracts/openclaw-dcp-routing/nested/provider_availability_probe_spec.md",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_unrelated_contract_markdown_is_still_rejected():
    result = _run_guard("contracts/other-routing/custom_contract.md")

    assert result.returncode == 1
    assert "contracts/other-routing/custom_contract.md" in result.stdout


def test_docs_markdown_behavior_is_unchanged():
    result = _run_guard("docs/03-reference/example.md")

    assert result.returncode == 0, result.stdout + result.stderr
