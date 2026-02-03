import pytest
from unittest.mock import MagicMock, patch
import sys
# Mock questionary before importing modules that use it
sys.modules["questionary"] = MagicMock()

from dopemux.orchestrator.adhd_orchestrator import ADHDOrchestrator, AttentionState, AttentionMetrics
from datetime import datetime

class TestADHDOrchestratorDynamicLayouts:
    @pytest.fixture
    def orchestrator(self):
        with patch('dopemux.orchestrator.adhd_orchestrator.AttentionMonitor') as MockMonitor:
            orch = ADHDOrchestrator()
            orch.tmux_controller = MagicMock()
            orch.apply_energy_layout = MagicMock()
            return orch

    def test_on_attention_update_triggers_layout(self, orchestrator):
        # Mock active session
        orchestrator.tmux_controller.get_active_session_name.return_value = "dev_session"
        
        # Test FOCUSED -> High Energy
        metrics = AttentionMetrics(
            timestamp=datetime.now(),
            keystroke_rate=50,
            error_rate=0,
            context_switches=0,
            pause_duration=0,
            focus_score=0.9,
            attention_state=AttentionState.FOCUSED
        )
        
        orchestrator._on_attention_update(metrics)
        
        orchestrator.apply_energy_layout.assert_called_with("dev_session", "high")

    def test_on_attention_update_scattered_low_energy(self, orchestrator):
        # Mock active session
        orchestrator.tmux_controller.get_active_session_name.return_value = "dev_session"
        
        # Test SCATTERED -> Low Energy
        metrics = AttentionMetrics(
            timestamp=datetime.now(),
            keystroke_rate=10,
            error_rate=5,
            context_switches=10,
            pause_duration=0,
            focus_score=0.3,
            attention_state=AttentionState.SCATTERED
        )
        
        orchestrator._on_attention_update(metrics)
        
        orchestrator.apply_energy_layout.assert_called_with("dev_session", "low")

    def test_on_attention_update_no_active_session(self, orchestrator):
        # Mock NO active session
        orchestrator.tmux_controller.get_active_session_name.return_value = None
        
        metrics = AttentionMetrics(
            timestamp=datetime.now(),
            keystroke_rate=50,
            error_rate=0,
            context_switches=0,
            pause_duration=0,
            focus_score=0.9,
            attention_state=AttentionState.FOCUSED
        )
        
        orchestrator._on_attention_update(metrics)
        
        # Should NOT call apply_energy_layout
        orchestrator.apply_energy_layout.assert_not_called()
