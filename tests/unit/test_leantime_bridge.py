"""
Unit tests for Leantime MCP Bridge.

Comprehensive test coverage for Leantime integration with ADHD optimizations.
"""

import pytest
pytest.importorskip("aiohttp")
pytest.importorskip("aioresponses")
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

import aiohttp
import aioresponses

from integrations.leantime_bridge import (
    LeantimeMCPClient,
    LeantimeTask,
    LeantimeProject,
    TaskStatus,
    TaskPriority,
    create_leantime_bridge
)
from core.config import Config
from core.exceptions import DopemuxIntegrationError, AuthenticationError


class TestLeantimeTask:
    """Test LeantimeTask dataclass functionality."""

    def test_task_creation_with_defaults(self):
        """Test creating task with default values."""
        task = LeantimeTask()

        assert task.id is None
        assert task.headline == ""
        assert task.description == ""
        assert task.project_id == 0
        assert task.user_id is None
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.FOCUSED
        assert task.dependencies == []
        assert task.tags == []

    def test_task_creation_with_values(self):
        """Test creating task with specific values."""
        now = datetime.now()
        task = LeantimeTask(
            id=123,
            headline="Test Task",
            description="Test description",
            project_id=456,
            user_id=789,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HYPERFOCUS,
            story_points=5,
            dependencies=[1, 2, 3],
            tags=["urgent", "bug"],
            created_at=now
        )

        assert task.id == 123
        assert task.headline == "Test Task"
        assert task.description == "Test description"
        assert task.project_id == 456
        assert task.user_id == 789
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HYPERFOCUS
        assert task.story_points == 5
        assert task.dependencies == [1, 2, 3]
        assert task.tags == ["urgent", "bug"]
        assert task.created_at == now

    def test_task_status_enum_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "0"
        assert TaskStatus.IN_PROGRESS.value == "1"
        assert TaskStatus.COMPLETED.value == "2"
        assert TaskStatus.BLOCKED.value == "3"
        assert TaskStatus.DEFERRED.value == "4"
        assert TaskStatus.CANCELLED.value == "5"
        assert TaskStatus.NEEDS_BREAK.value == "6"
        assert TaskStatus.CONTEXT_SWITCH.value == "7"

    def test_task_priority_enum_values(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.HYPERFOCUS.value == "1"
        assert TaskPriority.FOCUSED.value == "2"
        assert TaskPriority.SCATTERED.value == "3"
        assert TaskPriority.BACKGROUND.value == "4"


class TestLeantimeProject:
    """Test LeantimeProject dataclass functionality."""

    def test_project_creation_with_defaults(self):
        """Test creating project with default values."""
        project = LeantimeProject()

        assert project.id is None
        assert project.name == ""
        assert project.description == ""
        assert project.state == "open"
        assert project.adhd_mode_enabled is True
        assert project.context_preservation is True
        assert project.notification_batching is True

    def test_project_creation_with_values(self):
        """Test creating project with specific values."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)

        project = LeantimeProject(
            id=123,
            name="Test Project",
            description="Test project description",
            state="closed",
            start_date=start_date,
            end_date=end_date,
            adhd_mode_enabled=False
        )

        assert project.id == 123
        assert project.name == "Test Project"
        assert project.description == "Test project description"
        assert project.state == "closed"
        assert project.start_date == start_date
        assert project.end_date == end_date
        assert project.adhd_mode_enabled is False


class TestLeantimeMCPClient:
    """Test LeantimeMCPClient functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config({
            'leantime': {
                'api_url': 'http://localhost:8080',
                'api_token': 'test_token'
            }
        })

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return LeantimeMCPClient(config)

    def test_client_initialization(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.base_url == 'http://localhost:8080'
        assert client.api_token == 'test_token'
        assert client.mcp_endpoint == 'http://localhost:8080/mcp'
        assert client.session is None
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        """Test successful connection."""
        with aioresponses.aioresponses() as m:
            # Mock successful MCP initialization
            m.post(
                'http://localhost:8080/mcp',
                payload={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "sessionId": "test_session_123"
                    }
                }
            )

            success = await client.connect()

            assert success is True
            assert client._connected is True
            assert client._session_id == "test_session_123"
            assert client.session is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure."""
        with aioresponses.aioresponses() as m:
            # Mock connection failure
            m.post(
                'http://localhost:8080/mcp',
                exception=aiohttp.ClientError("Connection failed")
            )

            success = await client.connect()

            assert success is False
            assert client._connected is False
            assert client.session is None

    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test disconnection."""
        # Setup connected state
        client._connected = True
        client.session = AsyncMock()

        with aioresponses.aioresponses() as m:
            m.post('http://localhost:8080/mcp', payload={})

            await client.disconnect()

            assert client._connected is False
            client.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_mcp_request_success(self, client):
        """Test successful MCP request."""
        client.session = AsyncMock()

        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test_method"
        }

        expected_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"success": True}
        }

        # Mock session response
        mock_response = AsyncMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = expected_response
        client.session.post.return_value.__aenter__.return_value = mock_response

        result = await client._send_mcp_request(request_data)

        assert result == expected_response
        client.session.post.assert_called_once_with(
            'http://localhost:8080/mcp',
            json=request_data
        )

    @pytest.mark.asyncio
    async def test_send_mcp_request_not_connected(self, client):
        """Test MCP request when not connected."""
        client.session = None

        request_data = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        with pytest.raises(DopemuxIntegrationError, match="Not connected to Leantime"):
            await client._send_mcp_request(request_data)

    @pytest.mark.asyncio
    async def test_send_mcp_request_http_error(self, client):
        """Test MCP request with HTTP error."""
        client.session = AsyncMock()

        # Mock HTTP error
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=[], status=500
        )
        client.session.post.return_value.__aenter__.return_value = mock_response

        request_data = {"jsonrpc": "2.0", "id": 1, "method": "test"}

        with pytest.raises(DopemuxIntegrationError, match="Leantime API error"):
            await client._send_mcp_request(request_data)

    @pytest.mark.asyncio
    async def test_get_projects_success(self, client):
        """Test successful project retrieval."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps([
                        {
                            "id": 1,
                            "name": "Project 1",
                            "details": "Description 1",
                            "state": "open",
                            "created": "2024-01-01 10:00:00"
                        },
                        {
                            "id": 2,
                            "name": "Project 2",
                            "details": "Description 2",
                            "state": "closed",
                            "created": "2024-01-02 11:00:00"
                        }
                    ])
                }]
            }
        })

        projects = await client.get_projects(limit=10)

        assert len(projects) == 2
        assert projects[0].id == 1
        assert projects[0].name == "Project 1"
        assert projects[0].description == "Description 1"
        assert projects[0].state == "open"
        assert projects[1].id == 2
        assert projects[1].name == "Project 2"

    @pytest.mark.asyncio
    async def test_get_projects_empty_response(self, client):
        """Test project retrieval with empty response."""
        client._send_mcp_request = AsyncMock(return_value={})

        projects = await client.get_projects()

        assert projects == []

    @pytest.mark.asyncio
    async def test_get_project_success(self, client):
        """Test successful single project retrieval."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "id": 1,
                        "name": "Test Project",
                        "details": "Test description",
                        "state": "open",
                        "start": "2024-01-01",
                        "end": "2024-12-31",
                        "created": "2024-01-01 10:00:00"
                    })
                }]
            }
        })

        project = await client.get_project(1)

        assert project is not None
        assert project.id == 1
        assert project.name == "Test Project"
        assert project.description == "Test description"
        assert project.state == "open"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client):
        """Test project retrieval when project not found."""
        client._send_mcp_request = AsyncMock(return_value={})

        project = await client.get_project(999)

        assert project is None

    @pytest.mark.asyncio
    async def test_create_project_success(self, client):
        """Test successful project creation."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "success": True,
                        "projectId": 123
                    })
                }]
            }
        })

        project = LeantimeProject(
            name="New Project",
            description="New description",
            state="open"
        )

        created_project = await client.create_project(project)

        assert created_project is not None
        assert created_project.id == 123
        assert created_project.name == "New Project"

    @pytest.mark.asyncio
    async def test_create_project_failure(self, client):
        """Test project creation failure."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "success": False,
                        "error": "Creation failed"
                    })
                }]
            }
        })

        project = LeantimeProject(name="New Project")

        created_project = await client.create_project(project)

        assert created_project is None

    @pytest.mark.asyncio
    async def test_get_tasks_success(self, client):
        """Test successful task retrieval."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps([
                        {
                            "id": 1,
                            "headline": "Task 1",
                            "description": "Description 1",
                            "projectId": 10,
                            "editorId": 5,
                            "status": "1",
                            "storypoints": 3,
                            "date": "2024-01-01 10:00:00"
                        },
                        {
                            "id": 2,
                            "headline": "Task 2",
                            "description": "Description 2",
                            "projectId": 10,
                            "status": "0",
                            "storypoints": 5
                        }
                    ])
                }]
            }
        })

        # Mock ADHD optimizer
        with patch('integrations.leantime_bridge.ADHDTaskOptimizer') as mock_optimizer:
            mock_optimizer.return_value.optimize_task = AsyncMock(side_effect=lambda x: x)

            tasks = await client.get_tasks(project_id=10)

        assert len(tasks) == 2
        assert tasks[0].id == 1
        assert tasks[0].headline == "Task 1"
        assert tasks[0].status == TaskStatus.IN_PROGRESS
        assert tasks[0].story_points == 3
        assert tasks[1].id == 2
        assert tasks[1].status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_task_success(self, client):
        """Test successful single task retrieval."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "id": 1,
                        "headline": "Test Task",
                        "description": "Test description",
                        "projectId": 10,
                        "status": "1",
                        "storypoints": 3
                    })
                }]
            }
        })

        task = await client.get_task(1)

        assert task is not None
        assert task.id == 1
        assert task.headline == "Test Task"
        assert task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_create_task_success(self, client):
        """Test successful task creation."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "success": True,
                        "ticketId": 123
                    })
                }]
            }
        })

        # Mock ADHD optimizer
        with patch('integrations.leantime_bridge.ADHDTaskOptimizer') as mock_optimizer:
            mock_task = LeantimeTask(
                headline="New Task",
                description="New description",
                project_id=10
            )
            mock_optimizer.return_value.optimize_task = AsyncMock(return_value=mock_task)

            task = LeantimeTask(
                headline="New Task",
                description="New description",
                project_id=10
            )

            created_task = await client.create_task(task)

        assert created_task is not None
        assert created_task.id == 123
        assert created_task.headline == "New Task"

    @pytest.mark.asyncio
    async def test_update_task_success(self, client):
        """Test successful task update."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "success": True
                    })
                }]
            }
        })

        task = LeantimeTask(
            id=123,
            headline="Updated Task",
            description="Updated description"
        )

        success = await client.update_task(task)

        assert success is True

    @pytest.mark.asyncio
    async def test_update_task_no_id(self, client):
        """Test task update without ID."""
        task = LeantimeTask(headline="Task without ID")

        with pytest.raises(ValueError, match="Task ID required for update"):
            await client.update_task(task)

    @pytest.mark.asyncio
    async def test_delete_task_success(self, client):
        """Test successful task deletion."""
        client._send_mcp_request = AsyncMock(return_value={
            "result": {
                "content": [{
                    "text": json.dumps({
                        "success": True
                    })
                }]
            }
        })

        success = await client.delete_task(123)

        assert success is True

    @pytest.mark.asyncio
    async def test_get_adhd_optimized_tasks(self, client):
        """Test ADHD-optimized task retrieval."""
        # Mock get_tasks to return test tasks
        test_tasks = [
            LeantimeTask(
                id=1,
                headline="Quick Task",
                user_id=5,
                priority=TaskPriority.SCATTERED,
                story_points=1
            ),
            LeantimeTask(
                id=2,
                headline="Complex Task",
                user_id=5,
                priority=TaskPriority.HYPERFOCUS,
                story_points=8
            ),
            LeantimeTask(
                id=3,
                headline="Medium Task",
                user_id=6,  # Different user
                priority=TaskPriority.FOCUSED,
                story_points=3
            )
        ]

        with patch.object(client, 'get_tasks', AsyncMock(return_value=test_tasks)):
            # Test scattered attention state
            scattered_tasks = await client.get_adhd_optimized_tasks(
                user_id=5, attention_state="scattered"
            )

            assert len(scattered_tasks) == 1
            assert scattered_tasks[0].id == 1
            assert scattered_tasks[0].priority == TaskPriority.SCATTERED

            # Test hyperfocus attention state
            hyperfocus_tasks = await client.get_adhd_optimized_tasks(
                user_id=5, attention_state="hyperfocus"
            )

            assert len(hyperfocus_tasks) == 1
            assert hyperfocus_tasks[0].id == 2
            assert hyperfocus_tasks[0].priority == TaskPriority.HYPERFOCUS

    @pytest.mark.asyncio
    async def test_update_context_preservation(self, client):
        """Test context preservation update."""
        context_data = {
            "current_task": "task_123",
            "focus_state": "deep_work",
            "recent_decisions": ["decision_1", "decision_2"]
        }

        success = await client.update_context_preservation(user_id=5, context_data=context_data)

        assert success is True

    def test_parse_datetime_valid_formats(self, client):
        """Test datetime parsing with valid formats."""
        # Test various valid formats
        test_cases = [
            ("2024-01-01 10:30:00", datetime(2024, 1, 1, 10, 30, 0)),
            ("2024-01-01", datetime(2024, 1, 1, 0, 0, 0)),
            ("2024-01-01T10:30:00", datetime(2024, 1, 1, 10, 30, 0))
        ]

        for date_str, expected in test_cases:
            result = client._parse_datetime(date_str)
            assert result == expected

    def test_parse_datetime_invalid_formats(self, client):
        """Test datetime parsing with invalid formats."""
        # Test invalid formats
        invalid_dates = [
            None,
            "",
            "invalid_date",
            "2024-13-01",  # Invalid month
            "not_a_date"
        ]

        for date_str in invalid_dates:
            result = client._parse_datetime(date_str)
            assert result is None

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client):
        """Test health check when everything is healthy."""
        client._connected = True
        client._last_heartbeat = datetime.now()
        client._session_id = "test_session"

        with patch.object(client, 'get_projects', AsyncMock(return_value=[MagicMock()])):
            health = await client.health_check()

            assert health["status"] == "healthy"
            assert health["connected"] is True
            assert health["api_responsive"] is True
            assert health["projects_accessible"] is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, client):
        """Test health check when disconnected."""
        client._connected = False

        health = await client.health_check()

        assert health["status"] == "disconnected"
        assert health["connected"] is False
        assert "Not connected to Leantime" in health["error"]

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, client):
        """Test health check when unhealthy."""
        client._connected = True

        with patch.object(client, 'get_projects', AsyncMock(side_effect=Exception("API Error"))):
            health = await client.health_check()

            assert health["status"] == "unhealthy"
            assert health["connected"] is True
            assert "API Error" in health["error"]

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, client):
        """Test client as async context manager."""
        with patch.object(client, 'connect', AsyncMock(return_value=True)):
            with patch.object(client, 'disconnect', AsyncMock()):
                async with client as c:
                    assert c is client

                # Verify connect and disconnect were called
                client.connect.assert_called_once()
                client.disconnect.assert_called_once()

    def test_next_request_id_increments(self, client):
        """Test request ID incrementation."""
        assert client._next_request_id() == 1
        assert client._next_request_id() == 2
        assert client._next_request_id() == 3

    @pytest.mark.asyncio
    async def test_heartbeat_loop(self, client):
        """Test heartbeat loop functionality."""
        client._connected = True
        client.session = AsyncMock()
        client._session_id = "test_session"

        # Mock _send_mcp_request for heartbeat
        client._send_mcp_request = AsyncMock()

        # Start heartbeat loop and stop it quickly
        heartbeat_task = asyncio.create_task(client._heartbeat_loop())
        await asyncio.sleep(0.1)  # Let it run briefly
        client._connected = False  # Stop the loop

        try:
            await asyncio.wait_for(heartbeat_task, timeout=1.0)
        except asyncio.TimeoutError:
            heartbeat_task.cancel()


class TestFactoryFunction:
    """Test factory function."""

    def test_create_leantime_bridge(self):
        """Test factory function."""
        config = Config({'leantime': {'api_url': 'http://test'}})

        bridge = create_leantime_bridge(config)

        assert isinstance(bridge, LeantimeMCPClient)
        assert bridge.config == config
        assert bridge.base_url == 'http://test'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=integrations.leantime_bridge", "--cov-report=term-missing"])
