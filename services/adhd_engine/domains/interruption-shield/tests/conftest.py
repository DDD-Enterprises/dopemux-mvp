"""Pytest configuration and shared fixtures for interruption shield tests."""

import pytest
from datetime import datetime
from typing import Dict, Any

from interruption_shield.core.models import ShieldConfig, ShieldMode, AttentionState
from interruption_shield.triage.models import SlackMessage, UrgencyLevel


@pytest.fixture
def default_config() -> ShieldConfig:
    """Default shield configuration for testing."""
    return ShieldConfig(
        auto_activate=True,
        default_duration=25,
        mode=ShieldMode.ASSIST,
        allow_manual_override=True,
        enable_ai_summarization=False,  # Disable for tests
        store_message_content=False
    )


@pytest.fixture
def mock_slack_message() -> SlackMessage:
    """Mock Slack message for testing."""
    return SlackMessage(
        id="1234567890.123456",
        user="U123ABC",
        channel="C456DEF",
        channel_type="channel",
        text="Test message",
        timestamp=datetime.now()
    )


@pytest.fixture
def critical_slack_message() -> SlackMessage:
    """Mock critical Slack message."""
    return SlackMessage(
        id="1234567890.123457",
        user="U123ABC",
        channel="C456DEF",
        channel_type="im",
        text="URGENT: Production down!",
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_adhd_engine():
    """Mock ADHD Engine client."""
    class MockADHDEngine:
        def __init__(self):
            self.callbacks = []

        async def subscribe_attention_state(self, callback):
            self.callbacks.append(callback)

        async def trigger_state_change(self, state: AttentionState, user_id: str):
            for cb in self.callbacks:
                await cb(state, user_id)

    return MockADHDEngine()


@pytest.fixture
def mock_dnd_manager():
    """Mock DND Manager."""
    class MockDNDManager:
        def __init__(self):
            self.focus_mode_enabled = False
            self.slack_status_set = False

        async def enable_macos_focus_mode(self):
            self.focus_mode_enabled = True

        async def disable_macos_focus_mode(self):
            self.focus_mode_enabled = False

        async def set_slack_status(self, status: str, until: datetime):
            self.slack_status_set = True

        async def clear_slack_status(self):
            self.slack_status_set = False

    return MockDNDManager()
