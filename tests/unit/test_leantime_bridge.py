"""
Unit tests for Leantime MCP Bridge.

Comprehensive test coverage for Leantime integration with ADHD optimizations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from core.config import Config
from core.exceptions import DopemuxIntegrationError
from integrations.leantime_bridge import (
    LeantimeBridge,
    LeantimeProject,
    LeantimeTask,
    TaskPriority,
    TaskStatus,
    create_leantime_bridge,
)


# Helper for mocking JSON-RPC responses
class MockRPCResponse:
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error


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
            created_at=now,
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


class TestLeantimeProject:
    """Test LeantimeProject dataclass functionality."""

    def test_project_creation_with_defaults(self):
        """Test creating project with default values."""
        project = LeantimeProject()

        assert project.id is None
        assert project.name == ""
        assert project.description == ""
        assert project.state == "open"

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
            adhd_mode_enabled=False,
        )

        assert project.id == 123
        assert project.name == "Test Project"
        assert project.description == "Test project description"
        assert project.state == "closed"
        assert project.start_date == start_date
        assert project.end_date == end_date


class TestLeantimeBridge:
    """Test LeantimeBridge functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            {
                "leantime": {
                    "api_url": "http://localhost:8080",
                    "api_token": "test_token",
                }
            }
        )

    @pytest.fixture
    def mock_rpc_client(self):
        """Create a mock JSON-RPC client."""
        client = AsyncMock()
        client.connect = AsyncMock(return_value=True)
        return client

    @pytest.fixture
    def client(self, config, mock_rpc_client):
        """Create test bridge instance with mocked client factory."""
        with patch("integrations.leantime_bridge.create_leantime_client", return_value=mock_rpc_client):
            bridge = LeantimeBridge(config)
            yield bridge

    def test_client_initialization(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client._connected is False
        assert client.api_client is None

    @pytest.mark.asyncio
    async def test_connect_success(self, client, mock_rpc_client):
        """Test successful connection."""
        mock_rpc_client.connect.return_value = True
        
        # We need to simulate the create_leantime_client call inside connect()
        with patch("integrations.leantime_bridge.create_leantime_client", return_value=mock_rpc_client) as mock_create:
            success = await client.connect()

            assert success is True
            assert client._connected is True
            assert client.api_client == mock_rpc_client
            mock_create.assert_called_once_with(client.config)
            mock_rpc_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, client, mock_rpc_client):
        """Test connection failure."""
        mock_rpc_client.connect.return_value = False
        
        with patch("integrations.leantime_bridge.create_leantime_client", return_value=mock_rpc_client):
            success = await client.connect()

            assert success is False
            assert client._connected is False
            # API client is set but connection failed
            assert client.api_client == mock_rpc_client

    @pytest.mark.asyncio
    async def test_disconnect(self, client, mock_rpc_client):
        """Test disconnection."""
        # Setup connected state
        client.api_client = mock_rpc_client
        client._connected = True

        await client.disconnect()

        assert client._connected is False
        mock_rpc_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_projects_success(self, client, mock_rpc_client):
        """Test successful project retrieval."""
        client.api_client = mock_rpc_client
        client._connected = True
        
        mock_projects_data = [
            {
                "id": 1,
                "name": "Project 1",
                "details": "Description 1",
                "state": "open",
                "created": "2024-01-01 10:00:00",
            },
            {
                "id": 2,
                "name": "Project 2",
                "state": "closed",
            }
        ]
        
        mock_rpc_client.get_projects.return_value = MockRPCResponse(
            success=True, data=mock_projects_data
        )

        projects = await client.get_projects(limit=10)

        assert len(projects) == 2
        assert projects[0].id == 1
        assert projects[0].name == "Project 1"
        assert projects[1].id == 2
        assert projects[1].name == "Project 2"
        
        mock_rpc_client.get_projects.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_projects_not_connected(self, client):
        """Test get_projects when not connected."""
        client._connected = False
        client.api_client = None
        
        with pytest.raises(DopemuxIntegrationError, match="Not connected to Leantime"):
            await client.get_projects()

    @pytest.mark.asyncio
    async def test_get_task_success(self, client, mock_rpc_client):
        """Test successful single task retrieval."""
        client.api_client = mock_rpc_client
        client._connected = True
        
        mock_task_data = {
            "id": 1,
            "headline": "Test Task",
            "description": "Test description",
            "projectId": 10,
            "status": "1",  # IN_PROGRESS
            "storypoints": 3,
        }
        
        mock_rpc_client.get_ticket.return_value = MockRPCResponse(
            success=True, data=mock_task_data
        )

        task = await client.get_task(1)

        assert task is not None
        assert task.id == 1
        assert task.headline == "Test Task"
        assert task.status == TaskStatus.IN_PROGRESS
        
        mock_rpc_client.get_ticket.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_create_task_success(self, client, mock_rpc_client):
        """Test successful task creation."""
        client.api_client = mock_rpc_client
        client._connected = True
        
        # Mock creation response
        mock_rpc_client.create_ticket.return_value = MockRPCResponse(
            success=True, data={"success": True, "ticketId": 123}
        )

        # Mock ADHD optimizer to return task as-is
        with patch("integrations.leantime_bridge.ADHDTaskOptimizer") as mock_optimizer:
            mock_task = LeantimeTask(headline="New Task", project_id=10)
            mock_optimizer.return_value.optimize_task = AsyncMock(return_value=mock_task)

            task = LeantimeTask(headline="New Task", project_id=10)
            created_task = await client.create_task(task)

        assert created_task is not None
        assert created_task.id == 123
        assert created_task.headline == "New Task"
        
        mock_rpc_client.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_success(self, client, mock_rpc_client):
        """Test successful task update."""
        client.api_client = mock_rpc_client
        client._connected = True
        
        mock_rpc_client.update_ticket.return_value = MockRPCResponse(success=True)

        task = LeantimeTask(id=123, headline="Updated Task")
        success = await client.update_task(task)

        assert success is True
        mock_rpc_client.update_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_no_id(self, client):
        """Test task update without ID."""
        client._connected = True
        client.api_client = AsyncMock()
        
        task = LeantimeTask(headline="Task without ID")

        with pytest.raises(ValueError, match="Task ID required for update"):
            await client.update_task(task)

    @pytest.mark.asyncio
    async def test_delete_task_success(self, client, mock_rpc_client):
        """Test successful task deletion."""
        client.api_client = mock_rpc_client
        client._connected = True
        
        mock_rpc_client.delete_ticket.return_value = MockRPCResponse(success=True)

        success = await client.delete_task(123)

        assert success is True
        mock_rpc_client.delete_ticket.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client, mock_rpc_client):
        """Test health check when everything is healthy."""
        client.api_client = mock_rpc_client
        client._connected = True
        client._last_heartbeat = datetime.now()
        client._session_id = "test_session"

        # Mock successful project fetch as liveness check
        mock_rpc_client.get_projects.return_value = MockRPCResponse(
            success=True, data=[]
        )

        with patch.object(client, "get_projects", AsyncMock(return_value=[])):
            health = await client.health_check()

            assert health["status"] == "healthy"
            assert health["connected"] is True

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, client, mock_rpc_client):
        """Test client as async context manager."""
        mock_rpc_client.connect.return_value = True
        
        with patch("integrations.leantime_bridge.create_leantime_client", return_value=mock_rpc_client):
            async with client as c:
                assert c is client
                assert c._connected is True

            assert c._connected is False
            mock_rpc_client.disconnect.assert_called_once()


class TestFactoryFunction:
    """Test factory function."""

    def test_create_leantime_bridge(self):
        """Test factory function."""
        config = Config({"leantime": {"api_url": "http://test"}})

        bridge = create_leantime_bridge(config)

        assert isinstance(bridge, LeantimeBridge)
        assert bridge.config == config
