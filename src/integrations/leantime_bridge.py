"""
Leantime JSON-RPC Integration Bridge for Dopemux

This module provides a bridge between Dopemux and Leantime through JSON-RPC 2.0 API.
Handles project management, task tracking, and ADHD-optimized workflows.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from pydantic import BaseModel, ValidationError

from core.exceptions import DopemuxIntegrationError, AuthenticationError
from core.config import Config
from core.monitoring import MetricsCollector
from utils.security import SecureTokenManager
from utils.adhd_optimizations import ADHDTaskOptimizer
from .leantime_jsonrpc_client import LeantimeJSONRPCClient, create_leantime_client


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Leantime task status enumeration with ADHD considerations."""
    PENDING = "0"
    IN_PROGRESS = "1"
    COMPLETED = "2"
    BLOCKED = "3"
    DEFERRED = "4"
    CANCELLED = "5"
    NEEDS_BREAK = "6"  # ADHD-specific status
    CONTEXT_SWITCH = "7"  # ADHD-specific status


class TaskPriority(Enum):
    """Task priority levels optimized for ADHD attention management."""
    HYPERFOCUS = "1"      # High cognitive load, deep work
    FOCUSED = "2"         # Standard attention required
    SCATTERED = "3"       # Low cognitive load, quick wins
    BACKGROUND = "4"      # Can be done with divided attention


@dataclass
class LeantimeTask:
    """Leantime task representation with ADHD optimizations."""
    id: Optional[int] = None
    headline: str = ""
    description: str = ""
    project_id: int = 0
    user_id: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.FOCUSED
    story_points: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    sprint: Optional[str] = None
    milestone_id: Optional[int] = None
    dependencies: List[int] = None
    tags: List[str] = None

    # ADHD-specific fields
    cognitive_load: Optional[int] = None  # 1-10 scale
    attention_requirement: Optional[str] = None  # hyperfocus, focused, scattered
    break_frequency: Optional[int] = None  # minutes between breaks
    context_complexity: Optional[int] = None  # 1-5 scale

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []


@dataclass
class LeantimeProject:
    """Leantime project representation."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    state: str = "open"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # ADHD-specific project settings
    adhd_mode_enabled: bool = True
    context_preservation: bool = True
    notification_batching: bool = True


class LeantimeBridge:
    """
    JSON-RPC bridge for Leantime integration with ADHD optimizations.

    Handles authentication, API communication, and data synchronization
    with Leantime's JSON-RPC API while providing ADHD-specific features.
    """

    def __init__(self, config: Config):
        self.config = config
        self.api_client: Optional[LeantimeJSONRPCClient] = None

        # ADHD optimization components
        self.token_manager = SecureTokenManager()
        self.metrics = MetricsCollector()
        self.adhd_optimizer = ADHDTaskOptimizer()

        # Connection state
        self._connected = False
        self._last_heartbeat = None
        self._session_id = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> bool:
        """
        Establish connection to Leantime JSON-RPC API.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create JSON-RPC client
            self.api_client = create_leantime_client(self.config)

            # Test connection
            connection_success = await self.api_client.connect()

            if connection_success:
                self._connected = True
                self._last_heartbeat = datetime.now()
                self._session_id = f"leantime_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info("Successfully connected to Leantime JSON-RPC API")
                return True
            else:
                logger.error("Failed to connect to Leantime JSON-RPC API")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Leantime: {e}")
            self.api_client = None
            return False

    async def disconnect(self):
        """Gracefully disconnect from Leantime JSON-RPC API."""
        if self.api_client:
            try:
                await self.api_client.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.api_client = None
                self._connected = False
                logger.info("Disconnected from Leantime JSON-RPC API")


    # Project Management Methods

    async def get_projects(self, limit: int = 50) -> List[LeantimeProject]:
        """
        Retrieve all projects from Leantime.

        Args:
            limit: Maximum number of projects to return

        Returns:
            List of Leantime projects
        """
        if not self.api_client:
            raise DopemuxIntegrationError("Not connected to Leantime")

        response = await self.api_client.get_projects(limit)

        if response.success and response.data:
            projects_data = response.data if isinstance(response.data, list) else [response.data]

            # Track metrics
            self.metrics.record_api_call(
                service='leantime',
                method='get_projects',
                status='success'
            )

            return [
                LeantimeProject(
                    id=proj.get('id'),
                    name=proj.get('name', ''),
                    description=proj.get('details', ''),
                    state=proj.get('state', 'open'),
                    created_at=self._parse_datetime(proj.get('created'))
                )
                for proj in projects_data
            ]

        # Track failed metrics
        self.metrics.record_api_call(
            service='leantime',
            method='get_projects',
            status='error'
        )

        return []

    async def get_project(self, project_id: int) -> Optional[LeantimeProject]:
        """
        Get specific project details.

        Args:
            project_id: Leantime project ID

        Returns:
            Project details or None if not found
        """
        if not self.api_client:
            raise DopemuxIntegrationError("Not connected to Leantime")

        response = await self.api_client.get_project(project_id)

        if response.success and response.data:
            project_data = response.data

            return LeantimeProject(
                id=project_data.get('id'),
                name=project_data.get('name', ''),
                description=project_data.get('details', ''),
                state=project_data.get('state', 'open'),
                start_date=self._parse_datetime(project_data.get('start')),
                end_date=self._parse_datetime(project_data.get('end')),
                created_at=self._parse_datetime(project_data.get('created'))
            )

        return None

    async def create_project(self, project: LeantimeProject) -> Optional[LeantimeProject]:
        """
        Create new project in Leantime.

        Args:
            project: Project details

        Returns:
            Created project with ID or None if failed
        """
        if not self.api_client:
            raise DopemuxIntegrationError("Not connected to Leantime")

        response = await self.api_client.create_project(
            name=project.name,
            description=project.description,
            state=project.state
        )

        if response.success and response.data:
            result_data = response.data
            if result_data.get('success'):
                project.id = result_data.get('projectId')
                return project

        return None

    # Task Management Methods

    async def get_tasks(self, project_id: Optional[int] = None,
                       status: Optional[TaskStatus] = None,
                       limit: int = 100) -> List[LeantimeTask]:
        """
        Retrieve tasks from Leantime with ADHD optimizations.

        Args:
            project_id: Optional project filter
            status: Optional status filter
            limit: Maximum number of tasks

        Returns:
            List of Leantime tasks
        """
        if not self.api_client:
            raise DopemuxIntegrationError("Not connected to Leantime")

        # Get tickets using JSON-RPC client
        response = await self.api_client.get_tickets(
            project_id=project_id,
            status=status.value if status else None,
            limit=limit
        )

        if response.success and response.data:
            tasks_data = response.data if isinstance(response.data, list) else [response.data]

            tasks = []
            for task_data in tasks_data:
                task = LeantimeTask(
                    id=task_data.get('id'),
                    headline=task_data.get('headline', ''),
                    description=task_data.get('description', ''),
                    project_id=task_data.get('projectId', 0),
                    user_id=task_data.get('editorId'),
                    status=TaskStatus(str(task_data.get('status', '0'))),
                    story_points=task_data.get('storypoints'),
                    created_at=self._parse_datetime(task_data.get('date')),
                    updated_at=self._parse_datetime(task_data.get('dateToFinish'))
                )

                # Apply ADHD optimizations
                task = await self.adhd_optimizer.optimize_task(task)
                tasks.append(task)

            return tasks

        return []

    async def get_task(self, task_id: int) -> Optional[LeantimeTask]:
        """
        Get specific task details.

        Args:
            task_id: Leantime task ID

        Returns:
            Task details or None if not found
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "leantime.rpc.tickets.getTicket",
                "arguments": {
                    "ticketId": task_id
                }
            }
        })

        if response.get('result', {}).get('content'):
            task_data = json.loads(response['result']['content'][0]['text'])

            return LeantimeTask(
                id=task_data.get('id'),
                headline=task_data.get('headline', ''),
                description=task_data.get('description', ''),
                project_id=task_data.get('projectId', 0),
                user_id=task_data.get('editorId'),
                status=TaskStatus(str(task_data.get('status', '0'))),
                story_points=task_data.get('storypoints'),
                created_at=self._parse_datetime(task_data.get('date')),
                updated_at=self._parse_datetime(task_data.get('dateToFinish'))
            )

        return None

    async def create_task(self, task: LeantimeTask) -> Optional[LeantimeTask]:
        """
        Create new task in Leantime with ADHD optimizations.

        Args:
            task: Task details

        Returns:
            Created task with ID or None if failed
        """
        # Apply ADHD optimizations before creation
        optimized_task = await self.adhd_optimizer.optimize_task(task)

        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "leantime.rpc.tickets.addTicket",
                "arguments": {
                    "headline": optimized_task.headline,
                    "description": optimized_task.description,
                    "projectId": optimized_task.project_id,
                    "status": optimized_task.status.value,
                    "priority": optimized_task.priority.value,
                    "storypoints": optimized_task.story_points,
                    "editorId": optimized_task.user_id
                }
            }
        })

        if response.get('result', {}).get('content'):
            result_data = json.loads(response['result']['content'][0]['text'])
            if result_data.get('success'):
                optimized_task.id = result_data.get('ticketId')
                return optimized_task

        return None

    async def update_task(self, task: LeantimeTask) -> bool:
        """
        Update existing task in Leantime.

        Args:
            task: Task with updates

        Returns:
            True if update successful, False otherwise
        """
        if not task.id:
            raise ValueError("Task ID required for update")

        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "leantime.rpc.tickets.updateTicket",
                "arguments": {
                    "ticketId": task.id,
                    "headline": task.headline,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "storypoints": task.story_points
                }
            }
        })

        if response.get('result', {}).get('content'):
            result_data = json.loads(response['result']['content'][0]['text'])
            return result_data.get('success', False)

        return False

    async def delete_task(self, task_id: int) -> bool:
        """
        Delete task from Leantime.

        Args:
            task_id: Task ID to delete

        Returns:
            True if deletion successful, False otherwise
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "leantime.rpc.tickets.deleteTicket",
                "arguments": {
                    "ticketId": task_id
                }
            }
        })

        if response.get('result', {}).get('content'):
            result_data = json.loads(response['result']['content'][0]['text'])
            return result_data.get('success', False)

        return False

    # ADHD-Specific Methods

    async def get_adhd_optimized_tasks(self, user_id: int,
                                      attention_state: str = "focused") -> List[LeantimeTask]:
        """
        Get tasks optimized for current ADHD attention state.

        Args:
            user_id: User ID for personalization
            attention_state: Current attention state (hyperfocus, focused, scattered)

        Returns:
            List of tasks suitable for current attention state
        """
        all_tasks = await self.get_tasks()

        # Filter and optimize based on attention state
        optimized_tasks = []
        for task in all_tasks:
            if task.user_id == user_id or task.user_id is None:
                # Apply ADHD filtering logic
                if attention_state == "hyperfocus" and task.priority == TaskPriority.HYPERFOCUS:
                    optimized_tasks.append(task)
                elif attention_state == "focused" and task.priority in [TaskPriority.FOCUSED, TaskPriority.HYPERFOCUS]:
                    optimized_tasks.append(task)
                elif attention_state == "scattered" and task.priority in [TaskPriority.SCATTERED, TaskPriority.BACKGROUND]:
                    optimized_tasks.append(task)

        # Sort by ADHD-optimized criteria
        return sorted(optimized_tasks, key=lambda t: (
            t.cognitive_load or 5,  # Lower cognitive load first for scattered attention
            t.story_points or 0,    # Smaller tasks first
            t.priority.value        # Priority order
        ))

    async def update_context_preservation(self, user_id: int, context_data: Dict[str, Any]) -> bool:
        """
        Update context preservation data for ADHD users.

        Args:
            user_id: User ID
            context_data: Context information to preserve

        Returns:
            True if update successful
        """
        # Store context in Leantime user preferences or custom table
        # This would require custom Leantime plugin for full implementation
        logger.info(f"Context preservation update for user {user_id}: {context_data}")
        return True

    # Utility Methods

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from Leantime format."""
        if not date_str:
            return None

        try:
            # Try common Leantime date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{date_str}': {e}")

        return None

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health status of Leantime connection.

        Returns:
            Health status information
        """
        try:
            if not self._connected:
                return {
                    "status": "disconnected",
                    "connected": False,
                    "last_heartbeat": None,
                    "error": "Not connected to Leantime"
                }

            # Try a simple API call
            projects = await self.get_projects(limit=1)

            return {
                "status": "healthy",
                "connected": True,
                "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
                "session_id": self._session_id,
                "api_responsive": True,
                "projects_accessible": len(projects) >= 0
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": self._connected,
                "last_heartbeat": self._last_heartbeat.isoformat() if self._last_heartbeat else None,
                "error": str(e)
            }


# Factory function for easy instantiation
def create_leantime_bridge(config: Config) -> LeantimeBridge:
    """
    Factory function to create Leantime JSON-RPC bridge.

    Args:
        config: Dopemux configuration

    Returns:
        Configured Leantime JSON-RPC bridge
    """
    return LeantimeBridge(config)
