
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from dopemux.cli import _start_mcp_servers_with_progress

def test_start_mcp_servers_missing_assets():
    project_path = Path("/tmp/mock_project")
    
    # Mock Path properties
    # We need to handle mcp_dir.exists() and script_path.exists()
    # Since we are mocking Path objects created inside the function, 
    # it is easier to patch pathlib.Path.exists
    
    with patch("pathlib.Path.exists", return_value=False):
        with patch("dopemux.cli.console") as mock_console:
            # We also need to mock os.getenv to ensure we don't skip
            with patch("os.getenv", return_value="0"):
                _start_mcp_servers_with_progress(project_path)
            
            # Verify warning was printed
            mock_console.logger.warning.assert_called_with(
                f"[yellow]⚠️  MCP startup assets missing in {project_path}[/yellow]"
            )
            
            # Verify remedies were printed
            # console.print is called multiple times
            args_list = mock_console.print.call_args_list
            # Check for key phrases
            output_text = " ".join([str(call.args[0]) for call in args_list if call.args])
            assert "Running in reduced functionality mode" in output_text
            assert "Remedies:" in output_text
            assert "dopemux start --no-mcp" in output_text
            assert "cd dopemux-mvp && dopemux start" in output_text

def test_start_mcp_servers_existing_assets():
    # Verify that if assets exist, we proceed (until further mocking is needed or exception hits)
    project_path = Path("/tmp/mock_project")
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("dopemux.cli.console") as mock_console:
            with patch("os.getenv", return_value="0"):
                # We expect it to try to run subprocess or something further,
                # which might fail if not mocked.
                # The function imports requests and uses subprocess.
                # We stop strictly at the preflight check.
                
                # To avoid running the rest of the function, we can mock subprocess
                with patch("subprocess.Popen") as mock_popen:
                    mock_popen.return_value.stdout = []
                    mock_popen.return_value.poll.return_value = 0
                    
                    # We also need to mock requests for health check or connection
                    # But the function uses 'socket' and 'requests' later.
                    
                    try:
                        _start_mcp_servers_with_progress(project_path)
                    except Exception:
                        # We don't care about failures later in the function,
                        # just that it didn't return early due to missing assets.
                        pass
                    
                    # If it passed the check, it didn't print the warning
                    assert mock_console.logger.warning.call_count == 0
