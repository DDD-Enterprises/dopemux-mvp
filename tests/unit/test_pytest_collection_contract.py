"""Default collection includes script tests without basename import collisions."""
from pathlib import Path
import subprocess
import sys


def test_default_config_collects_scripts_and_unit_with_same_basename(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    (tmp_path / "pytest.ini").write_bytes((repo / "pytest.ini").read_bytes())
    # The repo supplies this compatibility ini option in tests/conftest.py when
    # plugin autoload is disabled. This miniature tree needs the same registration.
    (tmp_path / "conftest.py").write_text(
        'def pytest_addoption(parser):\n'
        '    parser.addini("asyncio_mode", "collection compatibility")\n'
    )
    for directory, name in [("scripts", "test_script_hook"), ("unit", "test_unit_hook")]:
        target = tmp_path / "tests" / directory
        target.mkdir(parents=True)
        (target / "test_hooks.py").write_text(f"def {name}():\n    assert False\n")
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q",
         "-p", "no:cacheprovider", "--rootdir", str(tmp_path),
         "--confcutdir", str(tmp_path), "tests"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    (tmp_path / "COLLECTION_STDOUT.txt").write_text(result.stdout)
    (tmp_path / "COLLECTION_STDERR.txt").write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests/scripts/test_hooks.py::test_script_hook" in result.stdout
    assert "tests/unit/test_hooks.py::test_unit_hook" in result.stdout
    assert "2 tests collected" in result.stdout
