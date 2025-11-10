"""Unit tests for the base agent functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from genetic_agent.core.agent import BaseAgent
from genetic_agent.core.config import AgentConfig
from genetic_agent.core.state import AgentState


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""

    def __init__(self, config):
        super().__init__(config)
        self.execute_call_count = 0

    async def _execute_repair(self, task):
        self.execute_call_count += 1
        if task.get("should_fail"):
            raise Exception("Test failure")
        return {"success": True, "result": "test"}


@pytest.fixture
def agent_config():
    """Fixture for agent configuration."""
    return AgentConfig()


@pytest.fixture
def test_agent(agent_config):
    """Fixture for test agent."""
    return TestAgent(agent_config)


@pytest.mark.asyncio
async def test_agent_process_task_success(test_agent):
    """Test successful task processing."""
    task = {"bug_description": "test bug", "file_path": "test.py"}

    result = await test_agent.process_task(task)

    assert result["success"] is True
    assert result["result"] == "test"
    assert test_agent.status.state == AgentState.IDLE
    assert test_agent.execute_call_count == 1


@pytest.mark.asyncio
async def test_agent_process_task_failure(test_agent):
    """Test task processing with failure."""
    task = {"should_fail": True}

    result = await test_agent.process_task(task)

    assert result["success"] is False
    assert "error" in result
    assert test_agent.status.state == AgentState.ERROR


@pytest.mark.asyncio
async def test_agent_circuit_breaker(test_agent):
    """Test circuit breaker functionality."""
    # Simulate token overuse
    test_agent._circuit_breaker_tokens = test_agent.config.max_tokens

    task = {"bug_description": "test"}
    result = await test_agent.process_task(task)

    assert result["success"] is False
    assert "Circuit breaker" in result["error"]
    assert test_agent.execute_call_count == 0  # Should not execute


def test_agent_status(test_agent):
    """Test agent status reporting."""
    status = test_agent.get_status()

    assert "state" in status
    assert "current_task" in status
    assert "uptime_seconds" in status
    assert status["state"] == AgentState.IDLE.value


def test_agent_circuit_breaker_reset(test_agent):
    """Test circuit breaker reset."""
    test_agent._circuit_breaker_tokens = test_agent.config.max_tokens
    test_agent.reset_circuit_breaker()

    assert test_agent._circuit_breaker_tokens == 0