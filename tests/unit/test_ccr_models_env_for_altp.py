import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from dopemux.cli import cli

@patch("dopemux.instance_state.save_instance_state_sync")
@patch("dopemux.instance_state.load_instance_state_sync")
@patch("dopemux.cli.ContextManager")
@patch("dopemux.cli.ClaudeLauncher")
@patch("dopemux.cli.AttentionMonitor")
@patch("dopemux.cli.LiteLLMProxyManager")
@patch("dopemux.cli.DopeBrainzRouterManager")
@patch("dopemux.cli.start_simple_proxy")
@patch("shutil.which")
def test_ccr_models_env_for_altp(
    mock_which,
    mock_start_proxy,
    mock_router_cls,
    mock_litellm_cls,
    mock_monitor_cls,
    mock_launcher_cls,
    mock_ctx_mgr,
    mock_load_state,
    mock_save_state,
    tmp_path,
):
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

    mock_launcher_instance = mock_launcher_cls.return_value
    mock_launcher_instance.launch.return_value = MagicMock()

    mock_monitor_instance = mock_monitor_cls.return_value
    mock_monitor_instance.start_monitoring.return_value = None

    workspace = Path(tmp_path)
    (workspace / ".dopemux").mkdir()
    (workspace / ".repo_id").write_text("project=dopemux-mvp\n", encoding="utf-8")

    litellm_config = workspace / "litellm.config.yaml"
    litellm_config.write_text(
        "model_list:\n"
        "  - model_name: altp-opus\n"
        "  - model_name: altp-sonnet\n"
        "  - model_name: altp-haiku\n",
        encoding="utf-8",
    )

    mock_litellm_info = MagicMock(
        base_url="http://127.0.0.1:4000",
        config_path=litellm_config,
        already_running=False,
        db_enabled=True,
        db_status="ok",
        log_path=workspace / "litellm.log",
    )
    mock_litellm_instance = mock_litellm_cls.return_value
    mock_litellm_instance.ensure_started.return_value = mock_litellm_info
    mock_litellm_instance.build_client_env.return_value = {
        "DOPEMUX_LITELLM_MASTER_KEY": "sk-test",
    }

    runner = CliRunner()
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = "sk-openrouter"
    env["XAI_API_KEY"] = "sk-xai"
    
    with patch("dopemux.cli.Path.cwd", return_value=workspace), \
         patch("dopemux.workspace_utils.get_workspace_root") as mock_get_root, \
         patch("dopemux.auto_configurator.WorktreeAutoConfigurator") as mock_auto_config, \
         patch("dopemux.cli.os.path.isdir") as mock_isdir, \
         patch("subprocess.check_call") as mock_check_call, \
         patch("dopemux.cli.detect_instances_sync", return_value=[]) as mock_detect, \
         patch("dopemux.cli.check_and_protect_main", return_value=False) as mock_protect, \
         patch("dopemux.cli.consume_last_created_worktree", return_value=None) as mock_consume, \
         patch("dopemux.cli.InstanceManager") as mock_instance_mgr, \
         patch("dopemux.worktree_recovery.show_recovery_menu_sync", return_value=None) as mock_recovery, \
         patch("dopemux.cli.RoutingConfig") as mock_routing_config_cls:

        mock_get_root.return_value = workspace
        mock_auto_config.return_value.configure_workspace.return_value = (True, "Mocked AutoConfig")
        mock_isdir.return_value = True
        mock_routing_config_cls.load_default.return_value.get_mode.return_value = "api"
        mock_routing_config_cls.load_default.return_value.get_ports.return_value = {"ccr": 8000, "litellm": 4000}

        # We must NOT use --dry-run because it skips the router logic we want to test.
        # Instead we rely on mocks to prevent side effects.
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["start", "--altp", "--no-mcp"])
            
            print(f"OUTPUT: {result.output}")
            if result.exception:
                print(f"EXCEPTION: {result.exception}")

            assert result.exit_code == 0

            print(f"Router CLS calls: {mock_router_cls.mock_calls}")
            print(f"Router Instance calls: {mock_router_instance.mock_calls}")

            # Check if router class was instantiated
            assert mock_router_cls.called, "DopeBrainzRouterManager was not instantiated"
            
            ensure_call = mock_router_instance.ensure_started.call_args
            assert ensure_call is not None
            _, kwargs = ensure_call
            
            # Verify URL
            provider_url = kwargs.get("provider_url") or kwargs.get("upstream_url")
            assert "127.0.0.1:4000/v1/chat/completions" in provider_url
            
            # Verify MODELS were passed appropriately via environment or args
            provider_models = kwargs.get("provider_models", [])
            assert "altp-opus" in provider_models
            assert "altp-sonnet" in provider_models
            assert "altp-haiku" in provider_models
