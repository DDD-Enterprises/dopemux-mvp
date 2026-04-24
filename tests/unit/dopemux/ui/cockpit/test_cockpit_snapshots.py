import os
import sys
from subprocess import run

from dopemux.ui.cockpit.render import render_snapshot


def test_snapshot_outputs_have_exact_dimensions() -> None:
    for size in ("120x40", "100x32", "80x24"):
        output = render_snapshot(size)
        width_text, height_text = size.split("x")
        width = int(width_text)
        height = int(height_text)
        lines = output.splitlines()
        assert len(lines) == height
        assert all(len(line) == width for line in lines)
        assert "..." not in output
        assert "…" not in output


def test_too_small_snapshot_returns_full_screen_blocker() -> None:
    output = render_snapshot("79x23")
    assert "[BLOCKER] terminal too small." in output
    assert "NEXT: rerun with --snapshot 80x24." in output


def test_snapshot_module_commands_succeed() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    for size in ("120x40", "100x32", "80x24"):
        result = run(
            [sys.executable, "-m", "dopemux.ui.cockpit", "--snapshot", size],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        assert f"mode Services" in result.stdout
