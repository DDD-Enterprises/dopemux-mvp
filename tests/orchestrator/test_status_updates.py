import pytest
from unittest.mock import MagicMock, patch
import sys
# Mock questionary before importing modules that use it
sys.modules["questionary"] = MagicMock()

from dopemux.orchestrator.adhd_orchestrator import ADHDOrchestrator, AttentionState

class TestADHDOrchestratorStatusUpdates:
    @pytest.fixture
    def orchestrator(self):
        with patch('dopemux.orchestrator.adhd_orchestrator.AttentionMonitor'):
            orch = ADHDOrchestrator()
            orch.tmux_controller = MagicMock()
            return orch

    def test_publish_attention_state(self, orchestrator):
        # Test publishing FOCUSED state
        orchestrator._publish_attention_state("test_session", AttentionState.FOCUSED)
        
        # Verify controller calls
        orchestrator.tmux_controller.set_session_option.assert_any_call("test_session", "@adhd_state", "focused")
        orchestrator.tmux_controller.set_session_option.assert_any_call("test_session", "@adhd_icon", "🧠")

    def test_publish_attention_state_scattered(self, orchestrator):
        # Test publishing SCATTERED state
        orchestrator._publish_attention_state("test_session", AttentionState.SCATTERED)
        
        # Verify controller calls
        orchestrator.tmux_controller.set_session_option.assert_any_call("test_session", "@adhd_state", "scattered")
        orchestrator.tmux_controller.set_session_option.assert_any_call("test_session", "@adhd_icon", "🌫️")

    def test_enter_break_mode(self, orchestrator):
        orchestrator.enter_break_mode(5)
        # Verify popup called with expected command
        # We can't match exact command string easily due to string formatting, but we can check if called
        args, kwargs = orchestrator.tmux_controller.display_popup.call_args
        assert "BREAK TIME" in args[0]
        assert "sleep 300" in args[0]
        assert kwargs.get("width") == "100%"

    def test_publish_handles_exception(self, orchestrator):
        # Simulate controller failure
        orchestrator.tmux_controller.set_session_option.side_effect = Exception("Tmux Connection Error")
        
        # Should not raise
        orchestrator._publish_attention_state("test_session", AttentionState.FOCUSED)
