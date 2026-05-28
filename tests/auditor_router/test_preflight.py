from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "auditor_router"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_preflight_help_documents_fixture_and_fallback_modes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.auditor_router.preflight", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--fixture-dir" in result.stdout
    assert "--allow-fallback" in result.stdout
    assert "--packet-id" in result.stdout


def test_preflight_selects_direct_route_when_available(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.auditor_router.preflight",
            "--fixture-dir",
            str(FIXTURES / "pal_clink_not_chosen_when_direct_available"),
            "--out",
            str(tmp_path),
            "--packet-id",
            "TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    route = load_json(tmp_path / "AUDITOR_ROUTE.json")
    assert route["tool"] == "claude-code-cli"
    assert route["status"] == "AVAILABLE"


def test_preflight_selects_pal_clink_for_fresh_sandbox_not_installed(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.auditor_router.preflight",
            "--fixture-dir",
            str(FIXTURES / "pal_clink_selected_when_all_tier1_not_installed"),
            "--out",
            str(tmp_path),
            "--packet-id",
            "TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    route = load_json(tmp_path / "AUDITOR_ROUTE.json")
    probes = load_json(tmp_path / "ROUTE_PROBE_OUTPUTS.json")
    assert route["tool"] == "pal-mcp-clink"
    assert route["status"] == "AVAILABLE"
    assert {item["status"] for item in probes["direct_routes"]} == {"NOT_INSTALLED"}


def test_preflight_does_not_execute_pal_mcp(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.auditor_router.preflight",
            "--fixture-dir",
            str(FIXTURES / "pal_clink_chosen_when_direct_auth_required"),
            "--out",
            str(tmp_path),
            "--packet-id",
            "TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    probes = load_json(tmp_path / "ROUTE_PROBE_OUTPUTS.json")
    assert probes["pal_mcp_called"] is False
    assert probes["repo_context_sent"] is False
    assert probes["external_cli_called_for_pal_clink"] is False
