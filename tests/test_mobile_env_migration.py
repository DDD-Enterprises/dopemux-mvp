import os
import subprocess
import pytest

# Paths
REPO_ROOT = '/Users/hue/code/dopemux-mvp'
BOOTSTRAP_SCRIPT = os.path.join(REPO_ROOT, 'scripts/mobile/dopemux-mobile.sh')
CONFIG_FILE = os.path.join(REPO_ROOT, 'configs/mobile/tmux.mobile.conf')

def test_files_exist():
    assert os.path.isfile(BOOTSTRAP_SCRIPT)
    assert os.path.isfile(CONFIG_FILE)

def test_tmux_config_validity():
    test_socket = 'dopemux-test-syntax'
    subprocess.run(['tmux', '-L', test_socket, 'kill-server'], stderr=subprocess.DEVNULL)
    cmd = ['tmux', '-L', test_socket, '-f', CONFIG_FILE, 'new-session', '-d']
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        subprocess.run(['tmux', '-L', test_socket, 'kill-server'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'Tmux config invalid: {e.stderr}')
