import subprocess
import sys
from pathlib import Path


def test_cli_run_creates_artifacts(tmp_path: Path):
    cmd = [
        sys.executable, "-m", "dopemux_github_specialist.cli",
        "run",
        "--scope", "pr",
        "--target", "PR#123",
        "--out-dir", str(tmp_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0

    base = tmp_path / "github_specialist"
    assert base.exists()
    # at least one run dir created
    assert any(p.is_dir() for p in base.iterdir())
    
    # Check for REPORT.json and REPORT.md
    run_dir = next(base.iterdir())
    assert (run_dir / "REPORT.json").exists()
    assert (run_dir / "REPORT.md").exists()
