"""
Unit tests for Claude-Code-Tools agent communication system.

Tests agent-to-agent messaging and collaborative workflows.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock

from dopemux.claude_tools.agent_communication import (
    AgentCommunicator, AgentMessage, CommunicationMode
)
from dopemux.claude_tools.tmux_cli import TmuxCli


class TestAgentCommunicator:
    """Test AgentCommunicator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_tmux = Mock(spec=TmuxCli)
        self.communicator = AgentCommunicator(self.mock_tmux)

    def test_send_message_sync(self):
        """Test synchronous message sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = "Response received"
        self.mock_tmux.capture.return_value = f"AGENT_MSG: {json.dumps({'sender': 'target', 'recipient': 'test', 'message_type': 'response', 'content': 'Response received'})}"

        message = AgentMessage(
            sender="test",
            recipient="target",
            message_type="request",
            content="Test message"
        )

        response = self.communicator.send_message(
            "session:0.0",
            message,
            mode=CommunicationMode.SYNCHRONOUS
        )

        assert response.content == "Response received"
        self.mock_tmux.send.assert_called_once()

    def test_send_message_async(self):
        """Test asynchronous message sending."""
        message = AgentMessage(
            sender="test",
            recipient="target",
            message_type="request",
            content="Test message"
        )

        response = self.communicator.send_message(
            "session:0.0",
            message,
            mode=CommunicationMode.ASYNCHRONOUS
        )

        assert response is None
        self.mock_tmux.send.assert_called_once()

    def test_receive_message(self):
        """Test message reception."""
        self.mock_tmux.capture.return_value = "AGENT_MSG: {\"sender\":\"target\",\"recipient\":\"test\",\"message_type\":\"response\",\"content\":\"Hello\"}"

        message = self.communicator.receive_message("session:0.0")

        assert message.sender == "target"
        assert message.content == "Hello"

    def test_collaborate_on_task(self):
        """Test agent collaboration."""
        # Mock successful collaboration
        # This test is complex due to timing - simplified version
        self.mock_tmux.capture.return_value = "AGENT_MSG: {\"sender\":\"secondary\",\"recipient\":\"primary\",\"message_type\":\"response\",\"content\":\"Collaboration response\"}"

        # Mock the method to return a successful result
        self.communicator._wait_for_response = Mock(return_value=AgentMessage(
            sender="secondary",
            recipient="primary",
            message_type="response",
            content="Collaboration response"
        ))

        result = self.communicator.collaborate_on_task(
            "primary_pane",
            "secondary_pane",
            "Test collaboration task"
        )

        assert result['success'] is True
        assert "Collaboration response" in result['primary_response'].content

    def test_process_ping_pong(self):
        """Test ping/pong message handling."""
        ping_msg = AgentMessage(
            sender="test",
            recipient="target",
            message_type="ping",
            content="ping"
        )

        pong_msg = self.communicator.process_message(ping_msg)

        assert pong_msg.message_type == "pong"
        assert pong_msg.content == "pong"