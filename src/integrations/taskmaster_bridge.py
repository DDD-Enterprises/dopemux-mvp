"""
Task-Master AI MCP Integration Bridge for Dopemux

This module provides integration with Claude-Task-Master AI for intelligent
task decomposition, complexity analysis, and AI-powered project management.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ValidationError

from core.exceptions import DopemuxIntegrationError, AIServiceError
from core.config import Config
from core.monitoring import MetricsCollector
from utils.security import SecureTokenManager


logger = logging.getLogger(__name__)


class TaskMasterProvider(Enum):
    """AI provider options for Task-Master."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    MISTRAL = "mistral"
    GROQ = "groq"
    OLLAMA = "ollama"
    AZURE = "azure"


class ComplexityLevel(Enum):
    """Task complexity levels from Task-Master analysis."""
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EPIC = 5


@dataclass
class TaskMasterTask:
    """Task representation from Task-Master AI."""
    id: str
    title: str
    description: str
    status: str  # pending, in_progress, done, deferred, cancelled
    priority: int = 1
    complexity_score: Optional[float] = None
    estimated_hours: Optional[float] = None
    dependencies: List[str] = None
    subtasks: List['TaskMasterTask'] = None
    tags: List[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.subtasks is None:
            self.subtasks = []
        if self.tags is None:
            self.tags = []


@dataclass
class PRDAnalysis:
    """Product Requirements Document analysis result."""
    project_name: str
    version: str
    requirements: List[str]
    tasks: List[TaskMasterTask]
    complexity_summary: Dict[str, Any]
    estimated_timeline: Optional[str] = None
    key_dependencies: List[str] = None
    risk_factors: List[str] = None

    def __post_init__(self):
        if self.key_dependencies is None:
            self.key_dependencies = []
        if self.risk_factors is None:
            self.risk_factors = []


class TaskMasterMCPClient:
    """
    MCP client for Task-Master AI integration.

    Handles intelligent task decomposition, complexity analysis, and AI-powered
    project management through the Task-Master AI MCP server.
    """

    def __init__(self, config: Config):
        self.config = config
        self.metrics = MetricsCollector()

        # Task-Master configuration
        self.task_master_path = config.get('taskmaster.path', '.taskmaster')
        self.default_provider = TaskMasterProvider(
            config.get('taskmaster.default_provider', 'anthropic')
        )

        # API Keys for different providers
        self.api_keys = {
            TaskMasterProvider.ANTHROPIC: config.get('api_keys.anthropic'),
            TaskMasterProvider.OPENAI: config.get('api_keys.openai'),
            TaskMasterProvider.GOOGLE: config.get('api_keys.google'),
            TaskMasterProvider.PERPLEXITY: config.get('api_keys.perplexity'),
            TaskMasterProvider.MISTRAL: config.get('api_keys.mistral'),
            TaskMasterProvider.GROQ: config.get('api_keys.groq'),
            TaskMasterProvider.OLLAMA: config.get('api_keys.ollama'),
            TaskMasterProvider.AZURE: config.get('api_keys.azure'),
        }

        # MCP connection state
        self._process: Optional[subprocess.Popen] = None
        self._connected = False
        self._request_id = 0

        # Initialize Task-Master directory structure
        self._init_taskmaster_directory()

    def _init_taskmaster_directory(self):
        """Initialize Task-Master directory structure."""
        task_master_dir = Path(self.task_master_path)
        task_master_dir.mkdir(exist_ok=True)

        # Create config.json
        config_file = task_master_dir / 'config.json'
        if not config_file.exists():
            config_data = {
                "providers": {
                    "anthropic": {
                        "model": "claude-3-sonnet-20240229",
                        "apiKey": self.api_keys.get(TaskMasterProvider.ANTHROPIC, "")
                    },
                    "openai": {
                        "model": "gpt-4",
                        "apiKey": self.api_keys.get(TaskMasterProvider.OPENAI, "")
                    },
                    "perplexity": {
                        "model": "llama-3.1-sonar-small-128k-online",
                        "apiKey": self.api_keys.get(TaskMasterProvider.PERPLEXITY, "")
                    }
                },
                "defaultProvider": self.default_provider.value,
                "researchProvider": "perplexity",
                "fallbackProvider": "openai"
            }

            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

        # Create tasks directory
        tasks_dir = task_master_dir / 'tasks'
        tasks_dir.mkdir(exist_ok=True)

        # Create empty tasks.json if it doesn't exist
        tasks_file = tasks_dir / 'tasks.json'
        if not tasks_file.exists():
            with open(tasks_file, 'w') as f:
                json.dump({"tasks": [], "metadata": {}}, f, indent=2)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> bool:
        """
        Start Task-Master MCP server process.

        Returns:
            bool: True if connection successful
        """
        try:
            # Prepare environment variables
            env = os.environ.copy()
            for provider, api_key in self.api_keys.items():
                if api_key:
                    env_key = f"{provider.value.upper()}_API_KEY"
                    env[env_key] = api_key

            # Start Task-Master MCP server
            self._process = subprocess.Popen(
                ['npx', '-y', '--package=task-master-ai', 'task-master-ai'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=self.task_master_path
            )

            # Send MCP initialization
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "Dopemux-TaskMaster-Bridge",
                        "version": "1.0.0"
                    }
                }
            }

            response = await self._send_mcp_request(init_request)

            if response.get('result'):
                self._connected = True
                logger.info("Successfully connected to Task-Master MCP server")
                return True
            else:
                logger.error(f"Failed to initialize Task-Master MCP: {response}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Task-Master: {e}")
            if self._process:
                self._process.terminate()
                self._process = None
            return False

    async def disconnect(self):
        """Gracefully disconnect from Task-Master MCP server."""
        if self._process:
            try:
                # Send shutdown notification
                shutdown_request = {
                    "jsonrpc": "2.0",
                    "method": "notifications/shutdown"
                }
                await self._send_mcp_request(shutdown_request)

                # Terminate process
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()

            except Exception as e:
                logger.warning(f"Error during Task-Master shutdown: {e}")
            finally:
                self._process = None
                self._connected = False
                logger.info("Disconnected from Task-Master MCP server")

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send MCP request to Task-Master server.

        Args:
            request: MCP request payload

        Returns:
            MCP response
        """
        if not self._process or not self._connected:
            raise DopemuxIntegrationError("Not connected to Task-Master")

        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            self._process.stdin.write(request_json)
            self._process.stdin.flush()

            # Read response
            response_line = self._process.stdout.readline()
            if not response_line:
                raise AIServiceError("No response from Task-Master")

            response = json.loads(response_line.strip())

            # Track metrics
            self.metrics.record_api_call(
                service='taskmaster',
                method=request.get('method', 'unknown'),
                status='success'
            )

            return response

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in Task-Master response: {e}")
            raise AIServiceError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Error in Task-Master MCP request: {e}")
            self.metrics.record_api_call(
                service='taskmaster',
                method=request.get('method', 'unknown'),
                status='error'
            )
            raise AIServiceError(f"Task-Master error: {e}")

    # Core Task-Master Methods

    async def parse_prd(self, prd_content: str, project_name: str = "Untitled") -> PRDAnalysis:
        """
        Parse Product Requirements Document using Task-Master AI.

        Args:
            prd_content: PRD text content
            project_name: Name for the project

        Returns:
            PRD analysis with tasks and complexity
        """
        # Create temporary PRD file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(prd_content)
            temp_file_path = temp_file.name

        try:
            response = await self._send_mcp_request({
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "tools/call",
                "params": {
                    "name": "parse_prd",
                    "arguments": {
                        "prdFile": temp_file_path,
                        "projectName": project_name
                    }
                }
            })

            if response.get('result', {}).get('content'):
                result_data = json.loads(response['result']['content'][0]['text'])

                # Parse tasks from result
                tasks = []
                for task_data in result_data.get('tasks', []):
                    task = TaskMasterTask(
                        id=task_data.get('id', ''),
                        title=task_data.get('title', ''),
                        description=task_data.get('description', ''),
                        status=task_data.get('status', 'pending'),
                        priority=task_data.get('priority', 1),
                        complexity_score=task_data.get('complexity'),
                        estimated_hours=task_data.get('estimatedHours'),
                        dependencies=task_data.get('dependencies', []),
                        tags=task_data.get('tags', []),
                        ai_analysis=task_data.get('aiAnalysis')
                    )

                    # Parse subtasks recursively
                    if task_data.get('subtasks'):
                        task.subtasks = self._parse_subtasks(task_data['subtasks'])

                    tasks.append(task)

                return PRDAnalysis(
                    project_name=project_name,
                    version=result_data.get('version', '1.0'),
                    requirements=result_data.get('requirements', []),
                    tasks=tasks,
                    complexity_summary=result_data.get('complexitySummary', {}),
                    estimated_timeline=result_data.get('estimatedTimeline'),
                    key_dependencies=result_data.get('keyDependencies', []),
                    risk_factors=result_data.get('riskFactors', [])
                )

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

        raise AIServiceError("Failed to parse PRD")

    def _parse_subtasks(self, subtasks_data: List[Dict]) -> List[TaskMasterTask]:
        """Parse subtasks recursively."""
        subtasks = []
        for subtask_data in subtasks_data:
            subtask = TaskMasterTask(
                id=subtask_data.get('id', ''),
                title=subtask_data.get('title', ''),
                description=subtask_data.get('description', ''),
                status=subtask_data.get('status', 'pending'),
                priority=subtask_data.get('priority', 1),
                complexity_score=subtask_data.get('complexity'),
                estimated_hours=subtask_data.get('estimatedHours'),
                dependencies=subtask_data.get('dependencies', []),
                tags=subtask_data.get('tags', [])
            )

            # Recursive subtask parsing
            if subtask_data.get('subtasks'):
                subtask.subtasks = self._parse_subtasks(subtask_data['subtasks'])

            subtasks.append(subtask)

        return subtasks

    async def get_tasks(self, tag: Optional[str] = None) -> List[TaskMasterTask]:
        """
        Get all tasks from Task-Master.

        Args:
            tag: Optional tag filter

        Returns:
            List of tasks
        """
        params = {}
        if tag:
            params["tag"] = tag

        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "get_tasks",
                "arguments": params
            }
        })

        if response.get('result', {}).get('content'):
            tasks_data = json.loads(response['result']['content'][0]['text'])

            tasks = []
            for task_data in tasks_data.get('tasks', []):
                task = TaskMasterTask(
                    id=task_data.get('id', ''),
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    status=task_data.get('status', 'pending'),
                    priority=task_data.get('priority', 1),
                    complexity_score=task_data.get('complexity'),
                    estimated_hours=task_data.get('estimatedHours'),
                    dependencies=task_data.get('dependencies', []),
                    tags=task_data.get('tags', [])
                )

                if task_data.get('subtasks'):
                    task.subtasks = self._parse_subtasks(task_data['subtasks'])

                tasks.append(task)

            return tasks

        return []

    async def get_next_task(self, preference: str = "priority") -> Optional[TaskMasterTask]:
        """
        Get the next recommended task to work on.

        Args:
            preference: Selection preference (priority, complexity, random)

        Returns:
            Next recommended task or None
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "next_task",
                "arguments": {
                    "preference": preference
                }
            }
        })

        if response.get('result', {}).get('content'):
            task_data = json.loads(response['result']['content'][0]['text'])

            if task_data:
                return TaskMasterTask(
                    id=task_data.get('id', ''),
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    status=task_data.get('status', 'pending'),
                    priority=task_data.get('priority', 1),
                    complexity_score=task_data.get('complexity'),
                    estimated_hours=task_data.get('estimatedHours'),
                    dependencies=task_data.get('dependencies', []),
                    tags=task_data.get('tags', [])
                )

        return None

    async def expand_task(self, task_id: str) -> Optional[TaskMasterTask]:
        """
        Expand a task with AI-generated subtasks.

        Args:
            task_id: ID of task to expand

        Returns:
            Expanded task with subtasks
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "expand_task",
                "arguments": {
                    "taskId": task_id
                }
            }
        })

        if response.get('result', {}).get('content'):
            task_data = json.loads(response['result']['content'][0]['text'])

            if task_data:
                task = TaskMasterTask(
                    id=task_data.get('id', ''),
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    status=task_data.get('status', 'pending'),
                    priority=task_data.get('priority', 1),
                    complexity_score=task_data.get('complexity'),
                    estimated_hours=task_data.get('estimatedHours'),
                    dependencies=task_data.get('dependencies', []),
                    tags=task_data.get('tags', [])
                )

                if task_data.get('subtasks'):
                    task.subtasks = self._parse_subtasks(task_data['subtasks'])

                return task

        return None

    async def analyze_complexity(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze task complexity using AI.

        Args:
            task_description: Description of the task

        Returns:
            Complexity analysis
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "analyze_complexity",
                "arguments": {
                    "description": task_description
                }
            }
        })

        if response.get('result', {}).get('content'):
            return json.loads(response['result']['content'][0]['text'])

        return {}

    async def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status

        Returns:
            True if update successful
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "set_status",
                "arguments": {
                    "taskId": task_id,
                    "status": status
                }
            }
        })

        if response.get('result', {}).get('content'):
            result_data = json.loads(response['result']['content'][0]['text'])
            return result_data.get('success', False)

        return False

    async def research_task(self, task_description: str, query: str) -> Dict[str, Any]:
        """
        Use AI research capabilities for task enhancement.

        Args:
            task_description: Task description
            query: Research query

        Returns:
            Research results
        """
        response = await self._send_mcp_request({
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": "research",
                "arguments": {
                    "taskDescription": task_description,
                    "query": query
                }
            }
        })

        if response.get('result', {}).get('content'):
            return json.loads(response['result']['content'][0]['text'])

        return {}

    # Utility Methods

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health status of Task-Master connection.

        Returns:
            Health status information
        """
        try:
            if not self._connected or not self._process:
                return {
                    "status": "disconnected",
                    "connected": False,
                    "process_running": False,
                    "error": "Not connected to Task-Master"
                }

            # Check if process is still running
            if self._process.poll() is not None:
                return {
                    "status": "process_terminated",
                    "connected": False,
                    "process_running": False,
                    "error": "Task-Master process terminated"
                }

            # Try a simple API call
            tasks = await self.get_tasks()

            return {
                "status": "healthy",
                "connected": True,
                "process_running": True,
                "api_responsive": True,
                "tasks_count": len(tasks),
                "default_provider": self.default_provider.value
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": self._connected,
                "process_running": self._process is not None and self._process.poll() is None,
                "error": str(e)
            }

    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers with valid API keys."""
        available = []
        for provider, api_key in self.api_keys.items():
            if api_key:
                available.append(provider.value)
        return available


# Factory function for easy instantiation
def create_taskmaster_bridge(config: Config) -> TaskMasterMCPClient:
    """
    Factory function to create Task-Master MCP client.

    Args:
        config: Dopemux configuration

    Returns:
        Configured Task-Master MCP client
    """
    return TaskMasterMCPClient(config)
