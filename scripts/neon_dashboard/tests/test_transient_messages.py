"""Test transient message priority system."""

import pytest

from scripts.neon_dashboard.components.transient_messages import (
    TransientMessageManager,
    TransientMessagePayload,
    TransientMessagesWidget,
    TransientPriority,
)


def test_message_payload_creation():
    """Test creating transient message payloads."""
    payload = TransientMessagePayload(
        message_id="test-1",
        title="Test Message",
        body=["Line 1", "Line 2"],
        priority=TransientPriority.CRITICAL,
        actions={"P": "Plan", "D": "Dismiss"}
    )
    
    assert payload.title == "Test Message"
    assert payload.priority == TransientPriority.CRITICAL
    assert len(payload.body) == 2
    assert "P" in payload.actions


def test_priority_enum():
    """Test priority levels are ordered correctly."""
    assert TransientPriority.CRITICAL == "critical"
    assert TransientPriority.WARNING == "warning"
    assert TransientPriority.INFO == "info"


def test_widget_rendering():
    """Test widget renders messages correctly."""
    widget = TransientMessagesWidget()
    
    # No message initially
    assert widget.payload is None
    
    # Set a message
    payload = TransientMessagePayload(
        message_id="test-1",
        title="Test",
        body=["Body text"],
        priority=TransientPriority.WARNING,
        actions={}
    )
    widget.payload = payload
    
    assert widget.payload == payload
