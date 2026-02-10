import os
import pytest
from dopemux.cli import _persist_instance_env_exports
from unittest.mock import patch, MagicMock

def setup_mocks(mock_path_cls):
    mock_file_export = MagicMock()
    mock_file_export.__str__.return_value = "instance_A.sh"
    mock_file_env = MagicMock()
    mock_file_env.__str__.return_value = "instance_A.env"
    mock_file_current = MagicMock()
    mock_file_current.__str__.return_value = "current.sh"
    
    # Mock relative_to to avoid more MagicMock chain issues
    mock_file_export.relative_to.return_value = "relative/instance_A.sh"
    
    mock_instance_dir = MagicMock()
    mock_handle = MagicMock()
    mock_file_export.open.return_value.__enter__.return_value = mock_handle
    mock_file_env.open.return_value.__enter__.return_value = mock_handle
    
    def path_div_side_effect(name):
        name_str = str(name)
        if "instance_" in name_str and ".sh" in name_str:
            return mock_file_export
        if "instance_" in name_str and ".env" in name_str:
            return mock_file_env
        if "current" in name_str:
            return mock_file_current
        return mock_instance_dir
    
    mock_instance_dir.__truediv__.side_effect = path_div_side_effect
    mock_path_cls.return_value.__truediv__.return_value = mock_instance_dir
    return mock_root_setup(mock_instance_dir), mock_handle

def mock_root_setup(mock_instance_dir):
    mock_root = MagicMock()
    mock_root.__truediv__.return_value = mock_instance_dir
    return mock_root

@patch("dopemux.cli.Path")
@patch("dopemux.cli.console")
@patch("dopemux.cli.shutil.copyfile")
def test_env_export_allowlist(mock_copy, mock_console, mock_path_cls):
    """
    Verify that _persist_instance_env_exports filters variables
    against a strict allowlist.
    """
    mock_root, mock_handle = setup_mocks(mock_path_cls)
    
    # Create a mix of allowed/disallowed vars
    input_vars = {
        "DOPEMUX_INSTANCE_ID": "A",
        "DOPEMUX_WORKSPACE_ID": "ws-123",
        "SECRET_KEY": "should-not-persist",
        "PATH": "/usr/bin",
        "CLAUDE_CODE_ROUTER_PROVIDER": "litellm",
        "RANDOM_VAR": "random",
    }
    
    _persist_instance_env_exports(mock_root, "A", input_vars)
    
    content = "".join(call.args[0] for call in mock_handle.write.call_args_list)
    
    assert "DOPEMUX_INSTANCE_ID" in content
    assert "DOPEMUX_WORKSPACE_ID" in content
    assert "CLAUDE_CODE_ROUTER_PROVIDER" in content
    assert "SECRET_KEY" not in content
    assert "PATH" not in content
    assert "RANDOM_VAR" not in content

@patch("dopemux.cli.Path")
@patch("os.environ.get")
@patch("dopemux.cli.console")
@patch("dopemux.cli.shutil.copyfile")
def test_env_export_secrets_opt_in(mock_copy, mock_console, mock_env_get, mock_path_cls):
    """
    Verify that secrets are exported when DOPEMUX_EXPORT_SECRETS=1.
    """
    mock_env_get.side_effect = lambda k, default=None: "1" if k == "DOPEMUX_EXPORT_SECRETS" else None
    mock_root, mock_handle = setup_mocks(mock_path_cls)
    
    input_vars = {
        "ANTHROPIC_API_KEY": "sk-secret-123",
        "LITELLM_MASTER_KEY": "sk-master-456",
        "DOPEMUX_INSTANCE_ID": "A",
    }
    
    _persist_instance_env_exports(mock_root, "A", input_vars)
    
    content = "".join(call.args[0] for call in mock_handle.write.call_args_list)
    
    assert "ANTHROPIC_API_KEY=sk-secret-123" in content
    assert "LITELLM_MASTER_KEY=sk-master-456" in content
    assert "DOPEMUX_INSTANCE_ID=A" in content

@patch("dopemux.cli.Path")
@patch("os.environ.get")
@patch("dopemux.cli.console")
@patch("dopemux.cli.shutil.copyfile")
def test_env_export_secrets_masked_by_default(mock_copy, mock_console, mock_env_get, mock_path_cls):
    """
    Verify that secrets are NOT exported by default.
    """
    mock_env_get.side_effect = lambda k, default=None: "0" if k == "DOPEMUX_EXPORT_SECRETS" else None
    mock_root, mock_handle = setup_mocks(mock_path_cls)
    
    input_vars = {
        "ANTHROPIC_API_KEY": "sk-secret-123",
        "DOPEMUX_INSTANCE_ID": "A",
    }
    
    _persist_instance_env_exports(mock_root, "A", input_vars)
    
    content = "".join(call.args[0] for call in mock_handle.write.call_args_list)
    
    assert "ANTHROPIC_API_KEY" not in content
    assert "DOPEMUX_INSTANCE_ID=A" in content
