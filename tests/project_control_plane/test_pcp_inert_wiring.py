"""Prove top-level dopemux CLI remains inert for live-write surfaces."""

from __future__ import annotations

import subprocess
import sys


def test_top_level_cli_has_no_live_write_commands():
    result = subprocess.run(
        [sys.executable, "-m", "dopemux.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    help_text = (result.stdout + result.stderr).lower()
    assert "bridge mutate" not in help_text
    assert "live-write" not in help_text
    assert "pcp bridge" not in help_text


def test_pcp_cli_export_help_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "dopemux.pcp.cli", "export", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0