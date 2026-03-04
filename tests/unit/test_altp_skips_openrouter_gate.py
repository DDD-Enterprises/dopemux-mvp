import os
import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from dopemux.cli import cli
from dopemux.litellm_proxy import LiteLLMProxyInfo

@patch("dopemux.cli.LiteLLMProxyManager")
@patch("dopemux.cli.DopeBrainzRouterManager")
@patch("dopemux.cli.start_simple_proxy")
@patch("dopemux.cli.RoutingConfig")
@patch("shutil.which")
def test_altp_skips_openrouter_gate(mock_which, mock_routing_config_cls, mock_start_proxy, mock_router_cls, mock_litellm_cls):
    """
    Verify that ALTP routing works correctly when provider-based API keys
    (OPENROUTER_API_KEY and XAI_API_KEY) are configured.
    """
    mock_which.return_value = "/bin/claude"
    mock_routing_config_cls.load_default.return_value.get_mode.return_value = "api"
    mock_start_proxy.return_value = (4000, "sk-test")
    
    # Mock LiteLLM manager
    mock_litellm_instance = mock_litellm_cls.return_value
    mock_litellm_instance.ensure_started.return_value = LiteLLMProxyInfo(
        host="127.0.0.1",
        port=4000,
        config_path=MagicMock(),
        master_key="sk-test",
        log_path=MagicMock(),
        already_running=False,
        db_enabled=True,
    )
    mock_litellm_instance.build_client_env.return_value = {}

    # Mock Router manager
    mock_router_instance = mock_router_cls.return_value
    mock_router_instance.ensure_started.return_value = MagicMock(
        base_url="http://127.0.0.1:8000",
        already_running=False
    )
    mock_router_instance.build_client_env.return_value = {
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:8000"
    }

    # Setup environment
    env = os.environ.copy()
    env.pop("DOPEMUX_AGENT_ROLE", None)
    
    env["OPENROUTER_API_KEY"] = "sk-openrouter"
    env["XAI_API_KEY"] = "sk-xai"

    runner = CliRunner(env=env)
    
    # Patch at the source of import
    with patch("dopemux.workspace_utils.get_workspace_root") as mock_get_root, \
         patch("dopemux.cli._ensure_role_profile") as mock_ensure_role_profile, \
         patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("pathlib.Path.cwd") as mock_cwd:
        
        mock_get_root.return_value = MagicMock()
        mock_ensure_role_profile.return_value = MagicMock()
        mock_exists.return_value = True
        mock_cwd.return_value = MagicMock()
        mock_mkdir.return_value = None
        
        # Mock suffix for config loading
        mock_cwd.return_value.__truediv__.return_value.__truediv__.return_value.suffix = ".yaml"

        result = runner.invoke(cli, ["start", "--altp", "--dry-run"])

        if result.exit_code != 0:
            print(f"EXIT CODE: {result.exit_code}")
            print(f"OUTPUT: {result.output}")
            if result.exception:
                 import traceback
                 traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0
        assert "OPENROUTER_API_KEY is not set" not in result.output
        assert "Enabling Claude Code Router" in result.output
