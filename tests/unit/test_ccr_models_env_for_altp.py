import os
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dopemux.cli import cli

@patch("dopemux.cli.LiteLLMProxyManager")
@patch("dopemux.cli.DopeBrainzRouterManager")
@patch("dopemux.cli.start_simple_proxy")
@patch("shutil.which")
def test_ccr_models_env_for_altp(mock_which, mock_start_proxy, mock_router_cls, mock_litellm_cls):
    """
    Verify that --altp sets CLAUDE_CODE_ROUTER_MODELS to "altp-opus,altp-sonnet,altp-haiku".
    """
    mock_which.return_value = "/bin/claude"
    mock_start_proxy.return_value = (4000, "sk-test")

    # Mock Router manager
    mock_router_instance = mock_router_cls.return_value
    mock_router_instance.ensure_started.return_value = MagicMock(
        base_url="http://127.0.0.1:8000",
        already_running=False
    )
    mock_router_instance.build_client_env.return_value = {}

    runner = CliRunner()
    env = os.environ.copy()
    env["ALTP_OPUS_KEY"] = "sk-opus"
    env["ALTP_SONNET_KEY"] = "sk-sonnet"
    env["ALTP_HAIKU_KEY"] = "sk-haiku"
    
    with patch("dopemux.cli.Path") as mock_path, \
         patch("dopemux.workspace_utils.get_workspace_root") as mock_get_root:
        
        mock_path.cwd.return_value = MagicMock()
        mock_path.exists.return_value = True
        mock_path.return_value.exists.return_value = True
        mock_get_root.return_value = MagicMock()

        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["start", "--altp", "--dry-run"])
            
            print(f"OUTPUT: {result.output}")
            if result.exception:
                print(f"EXCEPTION: {result.exception}")

            assert result.exit_code == 0

            print(f"Router CLS calls: {mock_router_cls.mock_calls}")
            print(f"Router Instance calls: {mock_router_instance.mock_calls}")

            # Check if router class was instantiated
            assert mock_router_cls.called, "DopeBrainzRouterManager was not instantiated"
            
            # Check mock_router_instance.ensure_started call args
            args, kwargs = mock_router_instance.ensure_started.call_args
            provider_models = kwargs.get("provider_models")
            assert provider_models is not None
            assert "altp-opus" in provider_models
            assert "altp-sonnet" in provider_models
            assert "altp-haiku" in provider_models
