from pathlib import Path
import os
import subprocess
import pytest
import shutil

# Dynamic path resolution
REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SCRIPT = REPO_ROOT / 'scripts/mobile/dopemux-mobile.sh'
# Corrected config path (moved from configs to config)
CONFIG_FILE = REPO_ROOT / 'config/mobile/tmux.mobile.conf'

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
        subprocess.run(['tmux', '-L', test_socket, 'kill-server'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'Tmux config invalid: {e.stderr}')
