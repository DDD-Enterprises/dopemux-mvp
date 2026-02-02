"""Integration tests for the full dashboard."""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from scripts.neon_dashboard.core.state import DashboardState, DashboardStateStore
from scripts.neon_dashboard.config.settings import DopeLayoutSettings


@pytest.fixture(autouse=True)
def clean_state_file():
    """Clean state file before each test."""
    state_paths = [
        os.path.expanduser("~/.cache/dopemux/dope_dashboard_state.json"),
        os.path.join(os.getcwd(), ".dopemux/dope_dashboard_state.json")
    ]
    for path in state_paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    yield
    # Cleanup after test
    for path in state_paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@pytest.mark.asyncio
async def test_state_persistence():
    """Test state is saved and loaded correctly."""
    settings = DopeLayoutSettings.from_dict({})
    store = DashboardStateStore(settings)
    
    # Modify state
    await store.set_mode("pm")
    await store.set_selected_task("task123", "Test Task")
    
    # Load in new instance
    store2 = DashboardStateStore(settings)
    await store2.load()
    
    assert store2.state.mode == "pm"
    assert store2.state.selected_task_id == "task123"
    assert store2.state.selected_task_name == "Test Task"


@pytest.mark.asyncio
async def test_mode_toggle():
    """Test mode switching between PM and Implementation."""
    settings = DopeLayoutSettings.from_dict({})
    state_store = DashboardStateStore(settings)
    await state_store.load()
    
    # Start in implementation mode
    assert state_store.state.mode == "implementation"
    
    # Toggle to PM
    await state_store.toggle_mode()
    assert state_store.state.mode == "pm"
    
    # Toggle back
    await state_store.toggle_mode()
    assert state_store.state.mode == "implementation"


def test_settings_from_dict():
    """Test configuration loading."""
    raw_config = {
        "default_mode": "pm",
        "metrics_bar_enabled": False,
        "transient_messages": {
            "untracked_work": False,
            "context_switches": True,
            "break_reminders": False,
        }
    }
    
    settings = DopeLayoutSettings.from_dict(raw_config)
    
    assert settings.default_mode == "pm"
    assert settings.metrics_bar_enabled is False
    assert settings.transient_messages.untracked_work is False
    assert settings.transient_messages.context_switches is True
