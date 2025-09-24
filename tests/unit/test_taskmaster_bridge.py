"""
Unit tests for Task-Master AI MCP Bridge.

Comprehensive test coverage for Task-Master AI integration.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from core.config import Config
from core.exceptions import AIServiceError, DopemuxIntegrationError
from integrations.taskmaster_bridge import (
    ComplexityLevel,
    PRDAnalysis,
    TaskMasterMCPClient,
    TaskMasterProvider,
    TaskMasterTask,
    create_taskmaster_bridge,
)


class TestTaskMasterTask:
    """Test TaskMasterTask dataclass functionality."""

    def test_task_creation_with_defaults(self):
        """Test creating task with default values."""
        task = TaskMasterTask(
            id="test_id",
            title="Test Task",
            description="Test description",
            status="pending",
        )

        assert task.id == "test_id"
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.status == "pending"
        assert task.priority == 1
        assert task.complexity_score is None
        assert task.estimated_hours is None
        assert task.dependencies == []
        assert task.subtasks == []
        assert task.tags == []

    def test_task_creation_with_values(self):
        """Test creating task with specific values."""
        now = datetime.now()
        subtask = TaskMasterTask(
            id="subtask_1",
            title="Subtask",
            description="Subtask description",
            status="pending",
        )

        task = TaskMasterTask(
            id="main_task",
            title="Main Task",
            description="Main description",
            status="in_progress",
            priority=3,
            complexity_score=4.5,
            estimated_hours=2.5,
            dependencies=["dep1", "dep2"],
            subtasks=[subtask],
            tags=["feature", "high-priority"],
            created_at=now,
        )

        assert task.id == "main_task"
        assert task.title == "Main Task"
        assert task.priority == 3
        assert task.complexity_score == 4.5
        assert task.estimated_hours == 2.5
        assert task.dependencies == ["dep1", "dep2"]
        assert task.subtasks == [subtask]
        assert task.tags == ["feature", "high-priority"]
        assert task.created_at == now


class TestPRDAnalysis:
    """Test PRDAnalysis dataclass functionality."""

    def test_prd_analysis_creation(self):
        """Test creating PRD analysis."""
        task1 = TaskMasterTask(
            id="1", title="Task 1", description="Desc 1", status="pending"
        )
        task2 = TaskMasterTask(
            id="2", title="Task 2", description="Desc 2", status="pending"
        )

        analysis = PRDAnalysis(
            project_name="Test Project",
            version="1.0",
            requirements=["Req 1", "Req 2"],
            tasks=[task1, task2],
            complexity_summary={"total_complexity": 7.5},
            estimated_timeline="4 weeks",
            key_dependencies=["Database", "API"],
            risk_factors=["Technical debt", "Resource constraints"],
        )

        assert analysis.project_name == "Test Project"
        assert analysis.version == "1.0"
        assert len(analysis.requirements) == 2
        assert len(analysis.tasks) == 2
        assert analysis.complexity_summary == {"total_complexity": 7.5}
        assert analysis.estimated_timeline == "4 weeks"
        assert analysis.key_dependencies == ["Database", "API"]
        assert analysis.risk_factors == ["Technical debt", "Resource constraints"]


class TestTaskMasterProvider:
    """Test TaskMasterProvider enum."""

    def test_provider_enum_values(self):
        """Test provider enum values."""
        assert TaskMasterProvider.ANTHROPIC.value == "anthropic"
        assert TaskMasterProvider.OPENAI.value == "openai"
        assert TaskMasterProvider.GOOGLE.value == "google"
        assert TaskMasterProvider.PERPLEXITY.value == "perplexity"
        assert TaskMasterProvider.MISTRAL.value == "mistral"
        assert TaskMasterProvider.GROQ.value == "groq"
        assert TaskMasterProvider.OLLAMA.value == "ollama"
        assert TaskMasterProvider.AZURE.value == "azure"


class TestComplexityLevel:
    """Test ComplexityLevel enum."""

    def test_complexity_enum_values(self):
        """Test complexity enum values."""
        assert ComplexityLevel.TRIVIAL.value == 1
        assert ComplexityLevel.SIMPLE.value == 2
        assert ComplexityLevel.MODERATE.value == 3
        assert ComplexityLevel.COMPLEX.value == 4
        assert ComplexityLevel.EPIC.value == 5


class TestTaskMasterMCPClient:
    """Test TaskMasterMCPClient functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            {
                "taskmaster": {"path": ".taskmaster", "default_provider": "anthropic"},
                "api_keys": {
                    "anthropic": "test_anthropic_key",
                    "openai": "test_openai_key",
                    "perplexity": "test_perplexity_key",
                },
            }
        )

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    return TaskMasterMCPClient(config)

    def test_client_initialization(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.task_master_path == ".taskmaster"
        assert client.default_provider == TaskMasterProvider.ANTHROPIC
        assert client.api_keys[TaskMasterProvider.ANTHROPIC] == "test_anthropic_key"
        assert client.api_keys[TaskMasterProvider.OPENAI] == "test_openai_key"
        assert client._process is None
        assert client._connected is False

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_init_taskmaster_directory(
        self, mock_json_dump, mock_file, mock_exists, mock_mkdir, config
    ):
        """Test TaskMaster directory initialization."""
        mock_exists.return_value = False

        TaskMasterMCPClient(config)

        # Verify directories were created
        mock_mkdir.assert_called()

        # Verify config file was written
        mock_json_dump.assert_called()

        # Verify API keys were configured
        call_args = mock_json_dump.call_args[0][0]
        assert call_args["providers"]["anthropic"]["apiKey"] == "test_anthropic_key"
        assert call_args["defaultProvider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        """Test successful connection."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {"protocolVersion": "2024-11-05", "capabilities": {}},
                }
            )
            + "\n"
        )

        with patch("subprocess.Popen", return_value=mock_process):
            success = await client.connect()

            assert success is True
            assert client._connected is True
            assert client._process == mock_process

    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure."""
        with patch("subprocess.Popen", side_effect=Exception("Process failed")):
            success = await client.connect()

            assert success is False
            assert client._connected is False
            assert client._process is None

    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test disconnection."""
        # Setup connected state
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.wait = MagicMock()

        client._process = mock_process
        client._connected = True

        await client.disconnect()

        assert client._connected is False
        assert client._process is None
        mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_mcp_request_success(self, client):
        """Test successful MCP request."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()

        request_data = {"jsonrpc": "2.0", "id": 1, "method": "test_method"}

        response_data = {"jsonrpc": "2.0", "id": 1, "result": {"success": True}}

        mock_process.stdout.readline.return_value = json.dumps(response_data) + "\n"

        client._process = mock_process
        client._connected = True

        result = await client._send_mcp_request(request_data)

        assert result == response_data
        mock_process.stdin.write.assert_called_once()
        mock_process.stdin.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_mcp_request_not_connected(self, client):
        """Test MCP request when not connected."""
        request_data = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        with pytest.raises(
            DopemuxIntegrationError, match="Not connected to Task-Master"
        ):
            await client._send_mcp_request(request_data)

    @pytest.mark.asyncio
    async def test_send_mcp_request_no_response(self, client):
        """Test MCP request with no response."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = ""  # Empty response

        client._process = mock_process
        client._connected = True

        request_data = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        with pytest.raises(AIServiceError, match="No response from Task-Master"):
            await client._send_mcp_request(request_data)

    @pytest.mark.asyncio
    async def test_send_mcp_request_invalid_json(self, client):
        """Test MCP request with invalid JSON response."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = "invalid json"

        client._process = mock_process
        client._connected = True

        request_data = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        with pytest.raises(AIServiceError, match="Invalid JSON response"):
            await client._send_mcp_request(request_data)

    @pytest.mark.asyncio
    async def test_parse_prd_success(self, client):
        """Test successful PRD parsing."""
        prd_content = "# Test PRD\n\nThis is a test product requirements document."

        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "version": "1.0",
                                "requirements": ["Requirement 1", "Requirement 2"],
                                "tasks": [
                                    {
                                        "id": "task_1",
                                        "title": "Task 1",
                                        "description": "Description 1",
                                        "status": "pending",
                                        "priority": 1,
                                        "complexity": 3.0,
                                        "estimatedHours": 2.0,
                                        "dependencies": [],
                                        "tags": ["feature"],
                                        "subtasks": [],
                                    }
                                ],
                                "complexitySummary": {"total": 3.0},
                                "estimatedTimeline": "2 weeks",
                                "keyDependencies": ["Database"],
                                "riskFactors": ["Time constraints"],
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        analysis = await client.parse_prd(prd_content, "Test Project")

        assert analysis.project_name == "Test Project"
        assert analysis.version == "1.0"
        assert len(analysis.requirements) == 2
        assert len(analysis.tasks) == 1
        assert analysis.tasks[0].id == "task_1"
        assert analysis.tasks[0].title == "Task 1"
        assert analysis.complexity_summary == {"total": 3.0}

    @pytest.mark.asyncio
    async def test_parse_prd_with_subtasks(self, client):
        """Test PRD parsing with subtasks."""
        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "version": "1.0",
                                "requirements": [],
                                "tasks": [
                                    {
                                        "id": "task_1",
                                        "title": "Main Task",
                                        "description": "Main description",
                                        "status": "pending",
                                        "priority": 1,
                                        "subtasks": [
                                            {
                                                "id": "subtask_1",
                                                "title": "Subtask 1",
                                                "description": "Subtask description",
                                                "status": "pending",
                                                "priority": 1,
                                                "subtasks": [],
                                            }
                                        ],
                                    }
                                ],
                                "complexitySummary": {},
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        analysis = await client.parse_prd("test content", "Test Project")

        assert len(analysis.tasks) == 1
        assert len(analysis.tasks[0].subtasks) == 1
        assert analysis.tasks[0].subtasks[0].id == "subtask_1"

    @pytest.mark.asyncio
    async def test_parse_prd_failure(self, client):
        """Test PRD parsing failure."""
        client._send_mcp_request = AsyncMock(return_value={})

        with pytest.raises(AIServiceError, match="Failed to parse PRD"):
            await client.parse_prd("test content", "Test Project")

    @pytest.mark.asyncio
    async def test_get_tasks_success(self, client):
        """Test successful task retrieval."""
        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "tasks": [
                                    {
                                        "id": "task_1",
                                        "title": "Task 1",
                                        "description": "Description 1",
                                        "status": "pending",
                                        "priority": 1,
                                    },
                                    {
                                        "id": "task_2",
                                        "title": "Task 2",
                                        "description": "Description 2",
                                        "status": "in_progress",
                                        "priority": 2,
                                    },
                                ]
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        tasks = await client.get_tasks()

        assert len(tasks) == 2
        assert tasks[0].id == "task_1"
        assert tasks[0].title == "Task 1"
        assert tasks[0].status == "pending"
        assert tasks[1].id == "task_2"
        assert tasks[1].status == "in_progress"

    @pytest.mark.asyncio
    async def test_get_tasks_with_tag_filter(self, client):
        """Test task retrieval with tag filter."""
        client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": '{"tasks": []}'}]}}
        )

        await client.get_tasks(tag="feature")

        # Verify request was made with tag parameter
        call_args = client._send_mcp_request.call_args[0][0]
        assert call_args["params"]["arguments"]["tag"] == "feature"

    @pytest.mark.asyncio
    async def test_get_next_task_success(self, client):
        """Test successful next task retrieval."""
        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "id": "next_task",
                                "title": "Next Task",
                                "description": "Next description",
                                "status": "pending",
                                "priority": 1,
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        task = await client.get_next_task(preference="priority")

        assert task is not None
        assert task.id == "next_task"
        assert task.title == "Next Task"

    @pytest.mark.asyncio
    async def test_get_next_task_none_available(self, client):
        """Test next task retrieval when none available."""
        client._send_mcp_request = AsyncMock(
            return_value={"result": {"content": [{"text": "null"}]}}
        )

        task = await client.get_next_task()

        assert task is None

    @pytest.mark.asyncio
    async def test_expand_task_success(self, client):
        """Test successful task expansion."""
        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "id": "expanded_task",
                                "title": "Expanded Task",
                                "description": "Expanded description",
                                "status": "pending",
                                "priority": 1,
                                "subtasks": [
                                    {
                                        "id": "subtask_1",
                                        "title": "Subtask 1",
                                        "description": "Subtask description",
                                        "status": "pending",
                                        "priority": 1,
                                    }
                                ],
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        task = await client.expand_task("task_123")

        assert task is not None
        assert task.id == "expanded_task"
        assert len(task.subtasks) == 1
        assert task.subtasks[0].id == "subtask_1"

    @pytest.mark.asyncio
    async def test_analyze_complexity_success(self, client):
        """Test successful complexity analysis."""
        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "complexity_score": 4.5,
                                "estimated_hours": 8.0,
                                "difficulty_factors": [
                                    "algorithm_design",
                                    "integration",
                                ],
                                "recommendations": ["Break into smaller tasks"],
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        analysis = await client.analyze_complexity("Complex algorithm implementation")

        assert analysis["complexity_score"] == 4.5
        assert analysis["estimated_hours"] == 8.0
        assert "algorithm_design" in analysis["difficulty_factors"]

    @pytest.mark.asyncio
    async def test_update_task_status_success(self, client):
        """Test successful task status update."""
        mock_response = {
            "result": {"content": [{"text": json.dumps({"success": True})}]}
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        success = await client.update_task_status("task_123", "done")

        assert success is True

    @pytest.mark.asyncio
    async def test_update_task_status_failure(self, client):
        """Test task status update failure."""
        mock_response = {
            "result": {
                "content": [
                    {"text": json.dumps({"success": False, "error": "Task not found"})}
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        success = await client.update_task_status("nonexistent_task", "done")

        assert success is False

    @pytest.mark.asyncio
    async def test_research_task_success(self, client):
        """Test successful task research."""
        mock_response = {
            "result": {
                "content": [
                    {
                        "text": json.dumps(
                            {
                                "research_results": ["Result 1", "Result 2"],
                                "sources": ["Source 1", "Source 2"],
                                "summary": "Research summary",
                            }
                        )
                    }
                ]
            }
        }

        client._send_mcp_request = AsyncMock(return_value=mock_response)

        research = await client.research_task(
            "Implement authentication", "Best practices for JWT implementation"
        )

        assert "research_results" in research
        assert len(research["research_results"]) == 2
        assert research["summary"] == "Research summary"

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client):
        """Test health check when healthy."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running

        client._connected = True
        client._process = mock_process

        with patch.object(
            client, "get_tasks", AsyncMock(return_value=[MagicMock(), MagicMock()])
        ):
            health = await client.health_check()

            assert health["status"] == "healthy"
            assert health["connected"] is True
            assert health["process_running"] is True
            assert health["api_responsive"] is True
            assert health["tasks_count"] == 2

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, client):
        """Test health check when disconnected."""
        client._connected = False
        client._process = None

        health = await client.health_check()

        assert health["status"] == "disconnected"
        assert health["connected"] is False
        assert health["process_running"] is False

    @pytest.mark.asyncio
    async def test_health_check_process_terminated(self, client):
        """Test health check when process terminated."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process terminated

        client._connected = True
        client._process = mock_process

        health = await client.health_check()

        assert health["status"] == "process_terminated"
        assert health["connected"] is False
        assert health["process_running"] is False

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, client):
        """Test health check when unhealthy."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        client._connected = True
        client._process = mock_process

        with patch.object(
            client, "get_tasks", AsyncMock(side_effect=Exception("API Error"))
        ):
            health = await client.health_check()

            assert health["status"] == "unhealthy"
            assert "API Error" in health["error"]

    def test_get_available_providers(self, client):
        """Test getting available providers."""
        providers = client.get_available_providers()

        assert "anthropic" in providers
        assert "openai" in providers
        assert "perplexity" in providers
        assert len(providers) == 3  # Only providers with API keys

    def test_next_request_id_increments(self, client):
        """Test request ID incrementation."""
        assert client._next_request_id() == 1
        assert client._next_request_id() == 2
        assert client._next_request_id() == 3

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, client):
        """Test client as async context manager."""
        with patch.object(client, "connect", AsyncMock(return_value=True)):
            with patch.object(client, "disconnect", AsyncMock()):
                async with client as c:
                    assert c is client

                # Verify connect and disconnect were called
                client.connect.assert_called_once()
                client.disconnect.assert_called_once()

    def test_parse_subtasks_recursive(self, client):
        """Test recursive subtask parsing."""
        subtasks_data = [
            {
                "id": "subtask_1",
                "title": "Subtask 1",
                "description": "Description 1",
                "status": "pending",
                "priority": 1,
                "subtasks": [
                    {
                        "id": "sub_subtask_1",
                        "title": "Sub Subtask 1",
                        "description": "Sub description",
                        "status": "pending",
                        "priority": 1,
                    }
                ],
            }
        ]

        subtasks = client._parse_subtasks(subtasks_data)

        assert len(subtasks) == 1
        assert subtasks[0].id == "subtask_1"
        assert len(subtasks[0].subtasks) == 1
        assert subtasks[0].subtasks[0].id == "sub_subtask_1"

    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_parse_prd_file_cleanup(self, mock_unlink, mock_temp_file, client):
        """Test PRD parsing cleans up temporary files."""
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_prd.md"

        client._send_mcp_request = AsyncMock(side_effect=Exception("Test error"))

        with pytest.raises(AIServiceError):
            asyncio.run(client.parse_prd("test content", "test project"))

        # Verify temporary file cleanup was attempted
        mock_unlink.assert_called_once_with("/tmp/test_prd.md")


class TestFactoryFunction:
    """Test factory function."""

    def test_create_taskmaster_bridge(self):
        """Test factory function."""
        config = Config({"taskmaster": {"path": ".test_taskmaster"}})

        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    bridge = create_taskmaster_bridge(config)

        assert isinstance(bridge, TaskMasterMCPClient)
        assert bridge.config == config


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=integrations.taskmaster_bridge",
            "--cov-report=term-missing",
        ]
    )
