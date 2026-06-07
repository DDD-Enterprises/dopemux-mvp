"""
Contract tests for CRIT and HIGH coverage gaps from the 2026-06-06 dopemux start audit.

GAP-C1  CRIT  duplicate _activate_dangerous_mode — no-confirm version at line 5914 wins
GAP-C2  CRIT  save_instance_state_sync unguarded crash post-launch
GAP-C3  CRIT  --alt-routing litellm spawns on 0.0.0.0 (network exposure)
NEW-C4  CRIT  claude_hooks + AttentionMonitor post-launch unguarded (PAL review)
GAP-H1  HIGH  api routing mode health check + env setup — completely untested
GAP-H2  HIGH  api repair failure + --routing-fallback-subscription branch
GAP-H3  HIGH  --grok/--codex legacy provider env var setup
GAP-H4  HIGH  --altp silent no-op in subscription mode
GAP-H5  HIGH  tmux kill-server call and TMUX-env skip condition
GAP-H6  HIGH  DOPEMUX_ALLOW_MAIN=1 bypass for check_and_protect_main
GAP-H7  HIGH  wire_conport_project.py check_call invocation

RED tests (bugs that currently fail): GAP-C1, GAP-C2, NEW-C4
Documentation/coverage tests: GAP-C3, GAP-H1–H7
"""

import os
import subprocess
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import MagicMock, call, patch

import pytest
from click.testing import CliRunner

from dopemux.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_project(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".dopemux").mkdir()
    return project_root


@pytest.fixture
def mock_process():
    p = MagicMock()
    p.wait.return_value = None
    return p


@pytest.fixture
def base_mocks(mock_project, mock_process):
    """Common patches for start command — minimal set that gets past preflight."""
    with ExitStack() as stack:
        stack.enter_context(patch("dopemux.cli.Path.cwd", return_value=mock_project))
        stack.enter_context(patch("dopemux.cli.ContextManager"))
        stack.enter_context(patch("dopemux.cli.detect_instances_sync", return_value=[]))
        stack.enter_context(patch("dopemux.cli.check_and_protect_main", return_value=False))
        mock_launcher_cls = stack.enter_context(patch("dopemux.cli.ClaudeLauncher"))
        mock_launcher_cls.return_value.launch.return_value = mock_process
        mock_im = stack.enter_context(patch("dopemux.cli.InstanceManager"))
        mock_im.return_value.get_instance_env_vars.return_value = {}
        # Wire script is best-effort — silence it
        stack.enter_context(patch("subprocess.check_call", side_effect=FileNotFoundError))
        yield {
            "launcher": mock_launcher_cls.return_value,
            "instance_manager": mock_im.return_value,
        }


# ─────────────────────────────────────────────────────────────────────────────
# GAP-C1: Dangerous mode must require interactive confirmation (CRIT)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestDangerousModeConfirmation:
    """GAP-C1: _activate_dangerous_mode at line 5914 shadows the guarded version."""

    def test_dangerous_mode_respects_user_decline(self, runner, base_mocks):
        """Declining the first confirmation prompt must leave env vars unset.

        RED: currently FAILS — the line-5914 definition sets env vars with
        no click.confirm calls, so 'n' input has no effect.
        """
        for var in ("DOPEMUX_DANGEROUS_MODE", "CLAUDE_CODE_SKIP_PERMISSIONS",
                    "METAMCP_ROLE_ENFORCEMENT", "CLAUDE_DANGEROUS"):
            os.environ.pop(var, None)

        result = runner.invoke(
            cli, ["start", "--dangerous", "--no-mcp", "--background"],
            input="n\n",
            catch_exceptions=False,
        )

        assert os.environ.get("DOPEMUX_DANGEROUS_MODE") != "true", (
            "User declined dangerous mode but DOPEMUX_DANGEROUS_MODE is still set. "
            "GAP-C1: _activate_dangerous_mode at line 5914 runs without click.confirm."
        )
        assert os.environ.get("CLAUDE_CODE_SKIP_PERMISSIONS") != "true"

    def test_dangerous_mode_sets_env_vars_after_both_confirmations(self, runner, base_mocks):
        """Accepting both confirmation prompts must set the dangerous mode env vars.

        This is the GREEN contract: after the GAP-C1 fix, the interactive
        version (line 3875) is used and sets vars only after confirmation.
        """
        for var in ("DOPEMUX_DANGEROUS_MODE", "CLAUDE_CODE_SKIP_PERMISSIONS"):
            os.environ.pop(var, None)

        result = runner.invoke(
            cli, ["start", "--dangerous", "--no-mcp", "--background"],
            input="y\ny\n",
            catch_exceptions=False,
        )

        assert os.environ.get("DOPEMUX_DANGEROUS_MODE") == "true"
        assert os.environ.get("CLAUDE_CODE_SKIP_PERMISSIONS") == "true"


# ─────────────────────────────────────────────────────────────────────────────
# GAP-C2: save_instance_state_sync must not crash dopemux (CRIT)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestSaveInstanceStateCrash:
    """GAP-C2: save_instance_state_sync at cli.py:2518 has no try/except."""

    def test_conport_failure_after_claude_launch_is_graceful(self, runner, base_mocks):
        """ConPort unreachable after Claude spawns must not crash dopemux.

        RED: currently FAILS — the unguarded call propagates ConnectionError,
        crashing dopemux after Claude is already running.
        """
        with patch(
            "dopemux.instance_state.save_instance_state_sync",
            side_effect=ConnectionError("ConPort not running on port 3004"),
        ):
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, (
            "dopemux must survive ConPort unavailability after launching Claude. "
            f"exit_code={result.exit_code}. GAP-C2: no try/except at cli.py:2518."
        )

    def test_conport_failure_logs_warning_not_crash(self, runner, base_mocks, capsys):
        """ConPort failure should produce a warning, not a traceback."""
        with patch(
            "dopemux.instance_state.save_instance_state_sync",
            side_effect=OSError("socket timeout"),
        ):
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0
        # Should NOT contain Python traceback markers
        assert "Traceback" not in (result.output or "")


# ─────────────────────────────────────────────────────────────────────────────
# NEW-C4: Post-launch monitoring hooks must not crash dopemux (CRIT, PAL-found)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestMonitoringHooksCrash:
    """NEW-C4: claude_hooks and AttentionMonitor at cli.py:2471-2475 are unguarded."""

    def test_attention_monitor_failure_is_graceful(self, runner, base_mocks):
        """AttentionMonitor.start_monitoring raising must not crash dopemux.

        RED: currently FAILS — exception propagates out of start() after Claude
        has already been launched.
        """
        with patch("dopemux.cli.AttentionMonitor") as mock_am:
            mock_am.return_value.start_monitoring.side_effect = RuntimeError(
                "attention monitor init failed"
            )
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, (
            "AttentionMonitor.start_monitoring failure must be best-effort, not fatal. "
            f"exit_code={result.exit_code}. NEW-C4: no try/except at cli.py:2475."
        )

    def test_claude_hooks_failure_is_graceful(self, runner, base_mocks):
        """claude_hooks.start_monitoring raising must not crash dopemux.

        RED: currently FAILS — exception propagates after Claude is running.
        """
        with patch("dopemux.cli.AttentionMonitor"):
            with patch("dopemux.hooks.claude_code_hooks.claude_hooks") as mock_hooks:
                mock_hooks.start_monitoring.side_effect = RuntimeError(
                    "hooks service unavailable"
                )
                result = runner.invoke(
                    cli, ["start", "--no-mcp", "--background"],
                    catch_exceptions=False,
                )

        assert result.exit_code == 0, (
            "claude_hooks.start_monitoring failure must be best-effort, not fatal. "
            f"exit_code={result.exit_code}. NEW-C4: no try/except at cli.py:2472."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GAP-C3: --alt-routing litellm bind address (CRIT)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestAltRoutingBindAddress:
    """GAP-C3: --alt-routing starts litellm with hardcoded 0.0.0.0 at cli.py:1612."""

    def test_alt_routing_litellm_bind_is_not_all_interfaces(
        self, runner, base_mocks, tmp_path
    ):
        """The litellm subprocess started by --alt-routing must NOT bind to 0.0.0.0.

        RED: currently FAILS — '0.0.0.0' is hardcoded at cli.py:1612.
        After fix: change to '127.0.0.1'.
        """
        popen_calls = []

        def capture_popen(args, **kwargs):
            popen_calls.append(args)
            return MagicMock()

        litellm_log = tmp_path / "litellm.log"
        litellm_log.parent.mkdir(parents=True, exist_ok=True)

        with ExitStack() as stack:
            stack.enter_context(
                patch.dict(
                    os.environ,
                    {"DOPEMUX_LITELLM_DB_URL": "postgresql://localhost/test"},
                )
            )
            stack.enter_context(
                patch(
                    "dopemux.cli.sync_litellm_database",
                    return_value=("DB synced", True),  # (status_msg, db_enabled)
                )
            )
            stack.enter_context(
                patch("subprocess.run", return_value=MagicMock(returncode=0))
            )
            stack.enter_context(patch("subprocess.Popen", side_effect=capture_popen))
            stack.enter_context(patch("time.sleep"))
            stack.enter_context(
                patch(
                    "httpx.get",  # httpx is imported locally inside the function
                    return_value=MagicMock(status_code=200),
                )
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli,
                ["start", "--alt-routing", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        litellm_calls = [
            args for args in popen_calls if args and "litellm" in str(args[0])
        ]
        for args in litellm_calls:
            assert "0.0.0.0" not in args, (
                f"litellm subprocess must not bind to 0.0.0.0. Found: {args}. GAP-C3."
            )
            assert "127.0.0.1" in args, (
                f"litellm subprocess must bind to 127.0.0.1 (loopback). Found: {args}. GAP-C3."
            )


# ─────────────────────────────────────────────────────────────────────────────
# GAP-H5: tmux kill-server call and TMUX-env skip (HIGH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestTmuxKillServer:
    """GAP-H5: tmux kill-server destroys all sessions at startup (cli.py:1875)."""

    def test_tmux_kill_server_called_when_not_in_tmux(self, runner, base_mocks):
        """tmux kill-server must be called when TMUX env var is not set."""
        subprocess_run_calls = []

        def capture_run(args, **kwargs):
            subprocess_run_calls.append(args)
            return MagicMock(returncode=0)

        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=False))
            os.environ.pop("TMUX", None)
            stack.enter_context(patch("shutil.which", return_value="/usr/bin/tmux"))
            stack.enter_context(patch("subprocess.run", side_effect=capture_run))
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        tmux_kill_calls = [
            args for args in subprocess_run_calls
            if args and "tmux" in str(args[0]) and "kill-server" in str(args)
        ]
        assert len(tmux_kill_calls) >= 1, (
            "tmux kill-server must be called when TMUX env is not set and tmux is on PATH. "
            "GAP-H5: no test currently verifies this call."
        )

    def test_tmux_kill_server_skipped_when_inside_tmux(self, runner, base_mocks):
        """tmux kill-server must be skipped when TMUX env var is set."""
        subprocess_run_calls = []

        def capture_run(args, **kwargs):
            subprocess_run_calls.append(args)
            return MagicMock(returncode=0)

        with ExitStack() as stack:
            stack.enter_context(
                patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,123,0"})
            )
            stack.enter_context(patch("shutil.which", return_value="/usr/bin/tmux"))
            stack.enter_context(patch("subprocess.run", side_effect=capture_run))
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        tmux_kill_calls = [
            args for args in subprocess_run_calls
            if args and "tmux" in str(args[0]) and "kill-server" in str(args)
        ]
        assert len(tmux_kill_calls) == 0, (
            "tmux kill-server must NOT be called when running inside tmux (TMUX env set). "
            "GAP-H5: guard is correct in code but never tested."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GAP-H6: DOPEMUX_ALLOW_MAIN=1 bypasses check_and_protect_main (HIGH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestAllowMainBypass:
    """GAP-H6: DOPEMUX_ALLOW_MAIN=1 must skip check_and_protect_main (cli.py:1952)."""

    def test_allow_main_env_bypasses_protection(self, runner, base_mocks):
        """With DOPEMUX_ALLOW_MAIN=1 set, check_and_protect_main must not be called."""
        with ExitStack() as stack:
            stack.enter_context(
                patch.dict(os.environ, {"DOPEMUX_ALLOW_MAIN": "1"})
            )
            mock_protect = stack.enter_context(
                patch("dopemux.cli.check_and_protect_main", return_value=False)
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        mock_protect.assert_not_called(), (
            "check_and_protect_main must be skipped when DOPEMUX_ALLOW_MAIN=1. "
            "GAP-H6: env-var bypass is untested."
        )

    def test_without_allow_main_protection_is_called(self, runner, base_mocks):
        """Without DOPEMUX_ALLOW_MAIN=1, check_and_protect_main must be called."""
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=False))
            os.environ.pop("DOPEMUX_ALLOW_MAIN", None)
            mock_protect = stack.enter_context(
                patch("dopemux.cli.check_and_protect_main", return_value=False)
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        mock_protect.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# GAP-H7: wire_conport_project.py check_call invocation (HIGH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestWireConportProject:
    """GAP-H7: wire_conport_project.py is called via check_call (cli.py:1919)."""

    def test_wire_conport_project_is_called(self, runner, mock_project, mock_process):
        """check_call must be invoked with the wire_conport_project.py script path."""
        wire_calls = []

        def capture_check_call(args, **kw):
            wire_calls.append(args)

        with ExitStack() as stack:
            stack.enter_context(patch("dopemux.cli.Path.cwd", return_value=mock_project))
            stack.enter_context(patch("dopemux.cli.ContextManager"))
            stack.enter_context(patch("dopemux.cli.detect_instances_sync", return_value=[]))
            stack.enter_context(patch("dopemux.cli.check_and_protect_main", return_value=False))
            mock_launcher_cls = stack.enter_context(patch("dopemux.cli.ClaudeLauncher"))
            mock_launcher_cls.return_value.launch.return_value = mock_process
            mock_im = stack.enter_context(patch("dopemux.cli.InstanceManager"))
            mock_im.return_value.get_instance_env_vars.return_value = {}
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            stack.enter_context(
                patch("subprocess.check_call", side_effect=capture_check_call)
            )
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        wire_script_calls = [
            args for args in wire_calls
            if args and "wire_conport_project" in " ".join(str(a) for a in args)
        ]
        assert len(wire_script_calls) >= 1, (
            "check_call must be invoked with wire_conport_project.py. "
            "GAP-H7: call correctness is currently untested."
        )
        # Verify it uses the current Python interpreter
        first_call = wire_script_calls[0]
        import sys
        assert str(sys.executable) in str(first_call[0]), (
            f"wire_conport_project.py must be run via sys.executable. Got: {first_call}"
        )

    def test_wire_conport_project_failure_does_not_abort_start(
        self, runner, base_mocks
    ):
        """check_call failure must be silently caught — start continues."""
        with patch("subprocess.check_call", side_effect=RuntimeError("script missing")):
            with patch("dopemux.cli.AttentionMonitor"):
                result = runner.invoke(
                    cli, ["start", "--no-mcp", "--background"],
                    catch_exceptions=False,
                )

        assert result.exit_code == 0, (
            "Wire script failure must not abort startup (best-effort). "
            "GAP-H7: exception is caught but not logged — consider a warning."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GAP-H1: api routing mode health check + env setup (HIGH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestApiRoutingMode:
    """GAP-H1: routing_mode == 'api' path — default for new-config API-key users."""

    def test_api_routing_healthy_sets_anthropic_base_url(self, runner, base_mocks):
        """When routing is 'api' and services are healthy, ANTHROPIC_BASE_URL is set."""
        mock_health = {"litellm": {"status": "healthy"}, "ccr": {"status": "healthy"}}
        mock_service_mgr = MagicMock()
        mock_service_mgr.check_health.return_value = mock_health

        mock_routing_config = MagicMock()
        mock_routing_config.get_mode.return_value = "api"
        mock_routing_config.get_ports.return_value = {"ccr": 3456, "litellm": 4000}

        # RoutingConfig is a module-level global in cli.py; mock the class directly.
        mock_routing_cls = MagicMock()
        mock_routing_cls.load_default.return_value = mock_routing_config

        with ExitStack() as stack:
            stack.enter_context(patch("dopemux.cli.RoutingConfig", mock_routing_cls))
            # LaunchdServiceManager is imported locally inside the api block.
            stack.enter_context(
                patch(
                    "dopemux.launchd_services.LaunchdServiceManager.get_instance",
                    return_value=mock_service_mgr,
                )
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            os.environ.pop("ANTHROPIC_BASE_URL", None)
            result = runner.invoke(
                cli, ["start", "--no-mcp", "--background"],
                catch_exceptions=False,
            )

        assert os.environ.get("ANTHROPIC_BASE_URL") == "http://127.0.0.1:3456", (
            "In api routing mode with healthy services, ANTHROPIC_BASE_URL must point "
            "to the CCR. GAP-H1."
        )

    def test_api_routing_repair_failure_fallback_clears_base_url(
        self, runner, base_mocks
    ):
        """When repair fails and --routing-fallback-subscription is set,
        ANTHROPIC_BASE_URL must be cleaned up (not left pointing at CCR)."""
        mock_health_unhealthy = {
            "litellm": {"status": "unhealthy", "error": "port closed"},
            "ccr": {"status": "unhealthy", "error": "process not found"},
        }
        mock_repair_failed = {
            "healthy": False,
            "attempts": [{"pass": 1, "action": "restart"}],
            "health": mock_health_unhealthy,
        }
        mock_service_mgr = MagicMock()
        mock_service_mgr.check_health.return_value = mock_health_unhealthy
        mock_service_mgr.repair.return_value = mock_repair_failed
        mock_service_mgr._get_log_paths.return_value = {
            "litellm_launchd": "/dev/null",
            "ccr_launchd": "/dev/null",
            "litellm_latest": "/dev/null",
        }

        mock_routing_config = MagicMock()
        mock_routing_config.get_mode.return_value = "api"
        mock_routing_config.get_ports.return_value = {"ccr": 3456, "litellm": 4000}

        mock_routing_cls = MagicMock()
        mock_routing_cls.load_default.return_value = mock_routing_config

        with ExitStack() as stack:
            stack.enter_context(patch("dopemux.cli.RoutingConfig", mock_routing_cls))
            stack.enter_context(
                patch(
                    "dopemux.launchd_services.LaunchdServiceManager.get_instance",
                    return_value=mock_service_mgr,
                )
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:3456"  # stale value
            result = runner.invoke(
                cli,
                ["start", "--no-mcp", "--background", "--routing-fallback-subscription"],
                catch_exceptions=False,
            )

        assert os.environ.get("ANTHROPIC_BASE_URL") is None or \
               os.environ.get("ANTHROPIC_BASE_URL") == "", (
            "After repair failure + fallback-subscription, ANTHROPIC_BASE_URL must be "
            "cleared. Stale URL would route Claude to a non-functional CCR. GAP-H2."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GAP-H4: --altp silent no-op in subscription mode (HIGH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestAltpSubscriptionNoop:
    """GAP-H4: --altp silently disables itself when routing mode is subscription."""

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "Pre-existing bug: when use_altp is set to False at cli.py:1288 "
            "(subscription mode), cli.py:1328 still references `config_data` which "
            "was never assigned → UnboundLocalError. Fix is out of scope for this TP."
        ),
    )
    def test_altp_noop_in_subscription_mode_no_proxy_started(
        self, runner, base_mocks
    ):
        """When routing mode is subscription, --altp must not start a proxy.

        XFAIL: pre-existing UnboundLocalError at cli.py:1328 (`config_data` unset
        when use_altp=False). When that bug is fixed, remove the xfail mark and
        the test should pass.
        """
        mock_routing_config = MagicMock()
        mock_routing_config.get_mode.return_value = "subscription"
        mock_routing_config.get_ports.return_value = {}

        mock_routing_cls = MagicMock()
        mock_routing_cls.load_default.return_value = mock_routing_config

        with ExitStack() as stack:
            stack.enter_context(patch("dopemux.cli.RoutingConfig", mock_routing_cls))
            stack.enter_context(patch("dopemux.cli._LITELLM_IMPORT_ERROR", None))
            mock_proxy = stack.enter_context(
                patch("dopemux.cli.start_simple_proxy")
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--altp", "--no-mcp", "--background"],
            )

        assert mock_proxy.call_count == 0, (
            "--altp in subscription mode must not start a proxy. GAP-H4."
        )

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "Pre-existing bug: UnboundLocalError at cli.py:1328 when "
            "use_altp is set to False mid-execution (subscription mode). "
            "Fix is out of scope for this TP."
        ),
    )
    def test_altp_noop_in_subscription_mode_exit_ok(self, runner, base_mocks):
        """--altp in subscription mode must exit cleanly (no crash, no error).

        XFAIL: pre-existing UnboundLocalError at cli.py:1328. When fixed,
        remove the xfail mark.
        """
        mock_routing_config = MagicMock()
        mock_routing_config.get_mode.return_value = "subscription"
        mock_routing_config.get_ports.return_value = {}

        mock_routing_cls = MagicMock()
        mock_routing_cls.load_default.return_value = mock_routing_config

        with ExitStack() as stack:
            stack.enter_context(patch("dopemux.cli.RoutingConfig", mock_routing_cls))
            stack.enter_context(patch("dopemux.cli._LITELLM_IMPORT_ERROR", None))
            stack.enter_context(patch("dopemux.cli.start_simple_proxy"))
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--altp", "--no-mcp", "--background"],
            )

        assert result.exit_code == 0, (
            "--altp in subscription mode must not raise ClickException. "
            f"Got exit_code={result.exit_code}. GAP-H4."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GAP-H3: --grok / --codex legacy provider env var setup (HIGH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestProviderFlagEnvSetup:
    """GAP-H3: --grok/--codex env var wiring via start_simple_proxy."""

    def test_grok_flag_sets_anthropic_base_url(self, runner, base_mocks):
        """--grok must set ANTHROPIC_BASE_URL to the local proxy."""
        # When litellm is not importable, GROK_PROVIDER is stubbed as {} and
        # generate_single_target_config / start_simple_proxy are stubs too.
        # Patch all three so the grok code path can run without real litellm.
        grok_provider_stub = {
            "name": "grok-code-fast",
            "model": "xai/grok-code-fast",
            "api_key_env": "XAI_API_KEY",
            "max_tokens": 131072,
            "label": "xAI Grok Code Fast",
        }
        with ExitStack() as stack:
            stack.enter_context(
                patch.dict(os.environ, {"XAI_API_KEY": "xai-test-key"})
            )
            stack.enter_context(patch("dopemux.cli._LITELLM_IMPORT_ERROR", None))
            stack.enter_context(patch("dopemux.cli.GROK_PROVIDER", grok_provider_stub))
            stack.enter_context(
                patch("dopemux.cli.generate_single_target_config", return_value={"models": []})
            )
            mock_proxy = stack.enter_context(
                patch("dopemux.cli.start_simple_proxy", return_value=(4000, "sk-test-grok"))
            )
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            os.environ.pop("ANTHROPIC_BASE_URL", None)
            result = runner.invoke(
                cli, ["start", "--grok", "--no-mcp", "--background"],
                catch_exceptions=False,
            )
            # Capture env var inside the stack — patch.dict restores on exit,
            # so the value would be gone outside the with block.
            anthropic_base_url = os.environ.get("ANTHROPIC_BASE_URL")

        assert anthropic_base_url is not None, (
            "--grok must set ANTHROPIC_BASE_URL to the local LiteLLM proxy URL. "
            "GAP-H3: this env var setup is untested."
        )
        assert "127.0.0.1" in anthropic_base_url, (
            "ANTHROPIC_BASE_URL must point to loopback proxy, not an external service."
        )
        mock_proxy.assert_called_once()

    def test_grok_missing_api_key_raises_click_exception(self, runner, base_mocks):
        """--grok without XAI_API_KEY must fail with a clear ClickException."""
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=False))
            os.environ.pop("XAI_API_KEY", None)
            stack.enter_context(patch("dopemux.cli.AttentionMonitor"))
            result = runner.invoke(
                cli, ["start", "--grok", "--no-mcp", "--background"],
            )

        assert result.exit_code != 0, (
            "--grok without XAI_API_KEY must fail, not silently proceed."
        )
