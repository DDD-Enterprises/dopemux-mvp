"""
Agent Communication System for Claude-Code-Tools

Enables AI agents to communicate with each other through tmux panes,
supporting collaborative workflows and multi-agent scenarios.

Based on Claude-Code-Tools tmux-cli agent-to-agent patterns.
"""

import time
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from .tmux_cli import TmuxCli, PaneInfo
from .safety_hooks import SafetyHooks


class CommunicationMode(Enum):
    """Communication modes between agents."""
    SYNCHRONOUS = "sync"      # Wait for response
    ASYNCHRONOUS = "async"    # Fire and forget
    INTERACTIVE = "interactive"  # Real-time interaction


class AgentRole(Enum):
    """Agent roles in communication."""
    PRIMARY = "primary"       # Initiating agent
    SECONDARY = "secondary"   # Responding agent
    COORDINATOR = "coordinator"  # Orchestrating agent


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    sender: str
    recipient: str
    message_type: str
    content: str
    metadata: Dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'message_type': self.message_type,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        return cls(
            sender=data['sender'],
            recipient=data['recipient'],
            message_type=data['message_type'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=data.get('timestamp', time.time())
        )


class AgentCommunicationError(Exception):
    """Raised when agent communication fails."""
    pass


class AgentCommunicator:
    """
    Manages communication between AI agents through tmux panes.

    Enables collaborative workflows where agents can:
    - Send messages to other agents
    - Receive responses
    - Coordinate complex tasks
    - Share context and results
    """

    def __init__(self, tmux_cli: TmuxCli, safety_hooks: Optional[SafetyHooks] = None):
        """
        Initialize agent communicator.

        Args:
            tmux_cli: TmuxCli instance for pane operations
            safety_hooks: SafetyHooks instance for command validation
        """
        self.tmux_cli = tmux_cli
        self.safety_hooks = safety_hooks or SafetyHooks()
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}

        # Register default message handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self.message_handlers.update({
            'ping': self._handle_ping,
            'pong': self._handle_pong,
            'request': self._handle_request,
            'response': self._handle_response,
            'error': self._handle_error,
        })

    def send_message(self, pane_id: str, message: AgentMessage,
                    mode: CommunicationMode = CommunicationMode.SYNCHRONOUS,
                    timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        Send a message to an agent in a tmux pane.

        Args:
            pane_id: Target pane identifier
            message: Message to send
            mode: Communication mode
            timeout: Timeout for synchronous responses

        Returns:
            Response message if synchronous, None otherwise
        """
        try:
            # Format message for sending
            message_text = f"AGENT_MSG: {message.to_json()}"

            # Send message to pane
            self.tmux_cli.send(message_text, pane_id, enter=True)

            if mode == CommunicationMode.SYNCHRONOUS:
                return self._wait_for_response(pane_id, message, timeout)
            elif mode == CommunicationMode.ASYNCHRONOUS:
                return None
            else:  # INTERACTIVE
                return self._start_interactive_session(pane_id, message)

        except Exception as e:
            raise AgentCommunicationError(f"Failed to send message to {pane_id}: {e}")

            logger.error(f"Error: {e}")
    def receive_message(self, pane_id: str, timeout: float = 5.0) -> Optional[AgentMessage]:
        """
        Receive a message from an agent in a tmux pane.

        Args:
            pane_id: Source pane identifier
            timeout: Timeout for message reception

        Returns:
            Received message or None if timeout
        """
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                # Capture recent output
                output = self.tmux_cli.capture(pane_id, lines=10)

                # Look for agent messages
                lines = output.split('\n')
                for line in reversed(lines):  # Check recent lines first
                    if line.startswith('AGENT_MSG: '):
                        try:
                            json_part = line[11:]  # Remove 'AGENT_MSG: ' prefix
                            return AgentMessage.from_json(json_part)
                        except json.JSONDecodeError:
                            continue  # Not a valid message, continue

                time.sleep(0.1)  # Brief pause before checking again

            return None  # Timeout

        except Exception as e:
            raise AgentCommunicationError(f"Failed to receive message from {pane_id}: {e}")

            logger.error(f"Error: {e}")
    def _wait_for_response(self, pane_id: str, original_message: AgentMessage,
                          timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        Wait for a response message from a pane.

        Args:
            pane_id: Pane to monitor
            original_message: Original message sent
            timeout: Maximum wait time

        Returns:
            Response message or None if timeout
        """
        start_time = time.time()
        expected_sender = original_message.recipient

        while time.time() - start_time < timeout:
            response = self.receive_message(pane_id, timeout=1.0)

            if response and response.sender == expected_sender:
                # Check if this is a response to our message
                if (response.message_type == 'response' and
                    response.metadata.get('request_id') == original_message.metadata.get('request_id')):
                    return response

            time.sleep(0.1)

        return None  # Timeout

    def _start_interactive_session(self, pane_id: str, initial_message: AgentMessage) -> AgentMessage:
        """
        Start an interactive communication session.

        Args:
            initial_message: Initial message
            pane_id: Target pane

        Returns:
            First response message
        """
        # For interactive mode, just wait for first response
        return self._wait_for_response(pane_id, initial_message, timeout=60.0) or AgentMessage(
            sender="system",
            recipient=initial_message.sender,
            message_type="error",
            content="Interactive session timeout",
            metadata={"original_message": initial_message.to_json()}
        )

    def collaborate_on_task(self, primary_pane: str, secondary_pane: str,
                           task_description: str, timeout: float = 300.0) -> Dict[str, Any]:
        """
        Enable two agents to collaborate on a task.

        Args:
            primary_pane: Primary agent pane
            secondary_pane: Secondary agent pane
            task_description: Task to collaborate on
            timeout: Maximum collaboration time

        Returns:
            Collaboration results
        """
        try:
            # Send task to secondary agent
            task_message = AgentMessage(
                sender="primary",
                recipient="secondary",
                message_type="request",
                content=f"Please help with this task: {task_description}",
                metadata={"task_type": "collaboration", "request_id": f"task_{int(time.time())}"}
            )

            response = self.send_message(secondary_pane, task_message,
                                       mode=CommunicationMode.SYNCHRONOUS,
                                       timeout=timeout)

            if response:
                # Send secondary's response back to primary for coordination
                coordination_message = AgentMessage(
                    sender="coordinator",
                    recipient="primary",
                    message_type="info",
                    content=f"Secondary agent response: {response.content}",
                    metadata={"secondary_response": response.to_json()}
                )

                self.send_message(primary_pane, coordination_message,
                                mode=CommunicationMode.ASYNCHRONOUS)

                return {
                    "success": True,
                    "primary_response": response,
                    "collaboration_time": time.time() - task_message.timestamp
                }
            else:
                return {
                    "success": False,
                    "error": "No response from secondary agent"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

            logger.error(f"Error: {e}")
    def debug_collaboratively(self, debugger_pane: str, assistant_pane: str,
                            error_description: str) -> Dict[str, Any]:
        """
        Enable collaborative debugging between agents.

        Args:
            debugger_pane: Pane with debugging agent
            assistant_pane: Pane with assistant agent
            error_description: Error to debug

        Returns:
            Debugging results
        """
        try:
            # Ask assistant for debugging strategy
            strategy_message = AgentMessage(
                sender="debugger",
                recipient="assistant",
                message_type="request",
                content=f"Help debug this error: {error_description}. Suggest debugging steps.",
                metadata={"task_type": "debugging", "request_id": f"debug_{int(time.time())}"}
            )

            strategy_response = self.send_message(assistant_pane, strategy_message,
                                                mode=CommunicationMode.SYNCHRONOUS)

            if strategy_response:
                # Send strategy to debugger
                execute_message = AgentMessage(
                    sender="coordinator",
                    recipient="debugger",
                    message_type="instruction",
                    content=f"Assistant suggests: {strategy_response.content}",
                    metadata={"debug_strategy": strategy_response.to_json()}
                )

                self.send_message(debugger_pane, execute_message,
                                mode=CommunicationMode.ASYNCHRONOUS)

                return {
                    "success": True,
                    "strategy": strategy_response.content,
                    "debug_session_started": True
                }
            else:
                return {
                    "success": False,
                    "error": "No debugging strategy received from assistant"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

            logger.error(f"Error: {e}")
    # Message handlers
    def _handle_ping(self, message: AgentMessage) -> AgentMessage:
        """Handle ping messages."""
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="pong",
            content="pong",
            metadata={"original_ping": message.to_json()}
        )

    def _handle_pong(self, message: AgentMessage) -> AgentMessage:
        """Handle pong messages."""
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="ack",
            content="pong received",
            metadata={"original_pong": message.to_json()}
        )

    def _handle_request(self, message: AgentMessage) -> AgentMessage:
        """Handle request messages."""
        # This would be overridden by specific agent implementations
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="response",
            content="Request acknowledged",
            metadata={"request_handled": True, "request_id": message.metadata.get("request_id")}
        )

    def _handle_response(self, message: AgentMessage) -> AgentMessage:
        """Handle response messages."""
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="ack",
            content="Response received",
            metadata={"response_acknowledged": True}
        )

    def _handle_error(self, message: AgentMessage) -> AgentMessage:
        """Handle error messages."""
        return AgentMessage(
            sender=message.recipient,
            recipient=message.sender,
            message_type="error_ack",
            content="Error acknowledged",
            metadata={"error_handled": True}
        )

    def register_handler(self, message_type: str, handler: Callable[[AgentMessage], AgentMessage]) -> None:
        """
        Register a custom message handler.

        Args:
            message_type: Message type to handle
            handler: Handler function
        """
        self.message_handlers[message_type] = handler

    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process an incoming message with appropriate handler.

        Args:
            message: Incoming message

        Returns:
            Response message or None
        """
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                return AgentMessage(
                    sender="system",
                    recipient=message.sender,
                    message_type="error",
                    content=f"Handler error: {e}",
                    metadata={"original_message": message.to_json()}
                )
                logger.error(f"Error: {e}")
        else:
            return AgentMessage(
                sender="system",
                recipient=message.sender,
                message_type="error",
                content=f"Unknown message type: {message.message_type}",
                metadata={"original_message": message.to_json()}
            )