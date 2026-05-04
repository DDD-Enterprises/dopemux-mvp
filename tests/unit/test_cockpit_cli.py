"""Top-level Cockpit CLI guard tests for runtime-render primitives."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from dopemux.commands.cockpit_commands import RUNTIME_RENDER_BLOCKER, cockpit


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = (
    REPO_ROOT
    / "out"
    / "cockpit-pack-remediation"
    / "TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA"
)


def _joined(*parts: str) -> str:
    return "".join(parts)


def _invoke(*args: str) -> "tuple[int, str]":
    result = CliRunner().invoke(cockpit, list(args))
    return result.exit_code, result.output


def test_top_level_cockpit_fails_closed_without_runtime_render_flag():
    code, output = _invoke("--package-dir", str(PACKAGE_DIR), "--snapshot", "120x40")
    assert code == 2
    assert RUNTIME_RENDER_BLOCKER in output
    assert "safe_for_claude_design: NO" not in output


def test_runtime_render_requires_package_dir():
    code, output = _invoke("--runtime-render", "--snapshot", "120x40")
    assert code == 2
    assert RUNTIME_RENDER_BLOCKER in output


def test_runtime_render_text_snapshot_preserves_blocked_governance_state():
    code, output = _invoke(
        "--runtime-render",
        "--package-dir",
        str(PACKAGE_DIR),
        "--snapshot",
        "120x40",
    )
    assert code == 0
    assert "safe_for_claude_design: NO" in output
    assert "READY_FOR_CLAUDE_DESIGN: not approved" in output
    assert "top_level_modes: PM | Implementer | Overview | Services | Events" in output
    assert "Command Palette broker-only" in output
    assert "T4 blocked until remote mutation policy exists" in output
    assert "TX/TU never executable" in output


def test_runtime_render_json_snapshot_preserves_modes_and_surfaces():
    code, output = _invoke(
        "--runtime-render",
        "--package-dir",
        str(PACKAGE_DIR),
        "--snapshot",
        "120x40",
        "--json",
    )
    assert code == 0
    payload = json.loads(output)
    assert payload["top_level_modes"] == [
        "PM",
        "Implementer",
        "Overview",
        "Services",
        "Events",
    ]
    assert len(payload["top_level_modes"]) == 5
    assert payload["global_surfaces"] == [
        "Command Palette",
        "Settings/Admin/Runtime",
        "Safe Actions / Proof Gate",
        "Unknown / Drift Queue",
    ]
    assert len(payload["artifact_provenance"]) >= 13
    assert payload["artifact_provenance"][0]["actual_sha256"]
    assert payload["safe_for_claude_design"] == "NO"
    assert payload["READY_FOR_CLAUDE_DESIGN"] == "not approved"


def test_runtime_render_output_has_no_forbidden_positive_claims():
    code, output = _invoke(
        "--runtime-render",
        "--package-dir",
        str(PACKAGE_DIR),
        "--snapshot",
        "120x40",
    )
    assert code == 0
    forbidden = (
        _joined("READY_FOR_CLAUDE_DESIGN: ", "approved"),
        _joined("safe_for_claude_design: ", "YES"),
        _joined("Claude Design upload ", "allowed"),
        _joined("T4 ", "authorized"),
        _joined("runtime execution ", "implemented"),
    )
    for phrase in forbidden:
        assert phrase not in output
