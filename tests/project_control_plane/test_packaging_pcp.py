"""Verify dopemux.pcp is packaged and importable from an installed wheel."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.slow
def test_installed_wheel_imports_pcp_modules():
    if shutil.which("pip") is None:
        pytest.skip("pip not available")
    try:
        import build  # noqa: F401
    except ImportError:
        pytest.skip("python build package not installed")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path / "dist")],
            cwd=_REPO_ROOT,
            check=True,
        )
        wheels = list((tmp_path / "dist").glob("*.whl"))
        assert wheels, "wheel build produced no artifacts"
        venv = tmp_path / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        pip = venv / "bin" / "pip"
        py = venv / "bin" / "python"
        subprocess.run([str(pip), "install", "--force-reinstall", str(wheels[0])], check=True)
        subprocess.run(
            [
                str(py),
                "-c",
                "import dopemux.pcp; import dopemux.pcp.bridge.fastapi_bridge",
            ],
            check=True,
        )
        help_result = subprocess.run(
            [str(py), "-m", "dopemux.pcp.cli", "export", "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert help_result.returncode == 0
        assert "export" in help_result.stdout.lower() or "usage" in help_result.stdout.lower()


def test_source_tree_imports_pcp_modules():
    import dopemux.pcp  # noqa: F401
    import dopemux.pcp.bridge.fastapi_bridge  # noqa: F401
    import dopemux.pcp.cli  # noqa: F401