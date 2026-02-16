import os
from pathlib import Path
from unittest.mock import patch

from dopemux.conport.wire_project import detect_project_root

def test_detect_project_root_explicit_path():
    """Verify explicit path is returned as resolved path."""
    path_str = "/tmp/explicit/path"
    result = detect_project_root(path_str)
    assert result == Path(path_str).resolve()

def test_detect_project_root_explicit_tilde_expansion():
    """Verify tilde in path is expanded."""
    result = detect_project_root("~")
    assert result.is_absolute()
    # It should resolve to the user's home directory
    assert result == Path("~").expanduser().resolve()

@patch("dopemux.conport.wire_project._run_git")
@patch("pathlib.Path.cwd")
def test_detect_project_root_git_repo(mock_cwd, mock_run_git):
    """Verify git root is returned if found."""
    mock_cwd.return_value = Path("/mock/cwd")
    # _run_git returns a string
    mock_run_git.return_value = "/mock/git/root"

    result = detect_project_root()

    assert result == Path("/mock/git/root")
    mock_run_git.assert_called_once_with(["rev-parse", "--show-toplevel"], Path("/mock/cwd"))

@patch("dopemux.conport.wire_project._run_git")
@patch("pathlib.Path.cwd")
def test_detect_project_root_fallback_cwd(mock_cwd, mock_run_git):
    """Verify fallback to CWD if not a git repo."""
    mock_cwd.return_value = Path("/mock/cwd")
    mock_run_git.return_value = None

    result = detect_project_root()

    assert result == Path("/mock/cwd")
    mock_run_git.assert_called_once()
