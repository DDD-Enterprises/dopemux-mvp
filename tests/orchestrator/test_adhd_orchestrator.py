
import sys
from unittest.mock import MagicMock
sys.modules["questionary"] = MagicMock()

import pytest
from unittest.mock import MagicMock, patch
from dopemux.orchestrator.adhd_orchestrator import ADHDOrchestrator
from dopemux.tmux.layouts import EnergyLayoutManager

@pytest.fixture
def adhd_orchestrator():
    with patch('dopemux.orchestrator.adhd_orchestrator.AttentionMonitor'), \
         patch('dopemux.orchestrator.adhd_orchestrator.TmuxController'), \
         patch('dopemux.orchestrator.adhd_orchestrator.ConfigManager'):
        return ADHDOrchestrator()

def test_adhd_orchestrator_initialization(adhd_orchestrator):
    assert adhd_orchestrator.tmux_controller is not None
    assert isinstance(adhd_orchestrator.layout_manager, EnergyLayoutManager)

def test_apply_energy_layout(adhd_orchestrator):
    adhd_orchestrator.layout_manager.apply_layout = MagicMock()
    
    adhd_orchestrator.apply_energy_layout("daily_grind", "high")
    
    adhd_orchestrator.layout_manager.apply_layout.assert_called_once_with("daily_grind", "high")
