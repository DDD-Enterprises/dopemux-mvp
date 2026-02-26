import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import click
from dopemux.cli import (
    _resolve_mcp_dir,
    _start_mcp_servers_with_progress,
    _trigger_dope_context_autoindex_startup,
)

# Fixture for creating a mock MCP stack
@pytest.fixture
def mock_mcp_stack(tmp_path):
    docker_dir = tmp_path / "docker" / "mcp-servers"
    docker_dir.mkdir(parents=True)
    (docker_dir / "start-all-mcp-servers.sh").touch()
    return docker_dir

def test_resolve_mcp_dir_env_override(mock_mcp_stack):
    """Strategy 1: DOPEMUX_MCP_DIR takes precedence."""
    with patch.dict(os.environ, {"DOPEMUX_MCP_DIR": str(mock_mcp_stack)}):
        # Project path doesn't matter
        resolved = _resolve_mcp_dir(Path("/tmp/whatever"))
        assert resolved == mock_mcp_stack
        assert resolved.exists()

def test_resolve_mcp_dir_project_local(mock_mcp_stack, tmp_path):
    """Strategy 2: Resolves from project_path/docker/mcp-servers."""
    # Ensure no env var
    with patch.dict(os.environ, {}, clear=True):
        # tmp_path has the 'docker/mcp-servers' created by fixture
        resolved = _resolve_mcp_dir(tmp_path)
        assert resolved == mock_mcp_stack

def test_resolve_mcp_dir_from_package_root_editable(tmp_path):
    """Strategy 3: Fallback to package root (simulated for running in this repo)."""
    project_path = tmp_path / "empty_project"
    project_path.mkdir()
    
    with patch.dict(os.environ, {}, clear=True):
        resolved = _resolve_mcp_dir(project_path)
        
        # Should find the real one in the repo we are currently working in
        assert resolved is not None
        assert resolved.name == "mcp-servers"
        assert (resolved / "start-all-mcp-servers.sh").exists()
        assert "docker/mcp-servers" in str(resolved)

def test_start_requires_mcp_raises_when_missing():
    """Verify hard failure when resolution returns None."""
    project_path = Path("/tmp/mock_project")
    
    # Mock resolution to fail
    with patch("dopemux.cli._resolve_mcp_dir", return_value=None):
        # Ensure we don't have the skip flag set
        with patch.dict(os.environ, {"DOPEMUX_SKIP_MCP_START": "0"}):
            with pytest.raises(click.ClickException) as exc:
                 _start_mcp_servers_with_progress(project_path)
            
            msg = str(exc.value)
            assert "MCP stack required but not found" in msg

def test_start_skips_when_flag_set():
    """Verify we can skip the check explicitly."""
    project_path = Path("/tmp/mock_project")
    
    with patch.dict(os.environ, {"DOPEMUX_SKIP_MCP_START": "1"}):
        # Should not raise
        _start_mcp_servers_with_progress(project_path)

def test_start_uses_resolved_dir(mock_mcp_stack):
    """Verify that the start script execution uses the resolved directory."""
    resolved_path = mock_mcp_stack
    script_path = resolved_path / "start-all-mcp-servers.sh"
    project_path = Path("/tmp/mock_project")
    
    # Ensure environment is clean
    with patch.dict(os.environ, {"DOPEMUX_SKIP_MCP_START": "0"}):
        with patch("dopemux.cli._resolve_mcp_dir", return_value=resolved_path):
            with patch("dopemux.cli.subprocess.Popen") as mock_popen:
                # Mock process behavior
                process_mock = Mock()
                process_mock.stdout.readline.side_effect = ["Starting...", ""]
                process_mock.poll.return_value = 0
                process_mock.wait.return_value = 0
                mock_popen.return_value = process_mock
                
                # Mock requests to avoid real network calls
                with patch("requests.get") as mock_get:
                    mock_get.return_value.status_code = 200
                    
                    # Call the function. If it fails, we want to SEE why.
                    try:
                        _start_mcp_servers_with_progress(project_path)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        raise e
                
                # Verify subprocess called with correct script path
                assert mock_popen.called, "subprocess.Popen was not called"
                args, _ = mock_popen.call_args
                cmd = args[0]
                assert str(script_path) == cmd[1]


def test_trigger_dope_context_autoindex_startup_calls_endpoint(tmp_path):
    """Startup autoindex helper should post to dope-context bootstrap endpoint."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    response = Mock()
    response.status_code = 200
    response.json.return_value = {"status": "started"}

    with patch("requests.post", return_value=response) as mock_post:
        with patch.dict(os.environ, {"DOPEMUX_AUTO_INDEX_ON_STARTUP": "1"}, clear=False):
            result = _trigger_dope_context_autoindex_startup(workspace)

    assert result["status"] == "started"
    mock_post.assert_called_once()
    called_endpoint = mock_post.call_args.args[0]
    assert called_endpoint.endswith("/autoindex/bootstrap")


def test_trigger_dope_context_autoindex_startup_can_be_disabled(tmp_path):
    """Autoindex helper should no-op when startup autoindex is disabled."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with patch("requests.post") as mock_post:
        with patch.dict(os.environ, {"DOPEMUX_AUTO_INDEX_ON_STARTUP": "0"}, clear=False):
            result = _trigger_dope_context_autoindex_startup(workspace)

    assert result is None
    mock_post.assert_not_called()
