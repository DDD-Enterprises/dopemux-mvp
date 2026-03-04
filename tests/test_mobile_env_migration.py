from pathlib import Path
import subprocess
import pytest
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SCRIPT = REPO_ROOT / "scripts/mobile/dopemux-mobile.sh"
CONFIG_FILE = next(
    candidate
    for candidate in (
        REPO_ROOT / "configs/mobile/tmux.mobile.conf",
        REPO_ROOT / "config/mobile/tmux.mobile.conf",
    )
    if candidate.is_file()
)

def test_files_exist():
    assert BOOTSTRAP_SCRIPT.is_file()
    assert CONFIG_FILE.is_file()

@pytest.mark.skipif(not shutil.which("tmux"), reason="tmux not installed")
def test_tmux_config_validity():
    test_socket = 'dopemux-test-syntax'
    subprocess.run(['tmux', '-L', test_socket, 'kill-server'], stderr=subprocess.DEVNULL)
    cmd = ['tmux', '-L', test_socket, '-f', str(CONFIG_FILE), 'new-session', '-d']
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        if "Operation not permitted" in (e.stderr or ""):
            pytest.skip("tmux socket access is not permitted in this environment")
        pytest.fail(f'Tmux config invalid: {e.stderr}')
    finally:
        subprocess.run(['tmux', '-L', test_socket, 'kill-server'], stderr=subprocess.DEVNULL)
