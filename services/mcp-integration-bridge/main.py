"""
MCP Integration Bridge Service - Multi-Instance Compatible
Central coordination layer for task management systems integration
Designed for Dopemux's git worktree multi-instance architecture

Supports:
- PORT_BASE + offset system (PORT_BASE + 16 = 3016, 3046, 3076, etc.)
- Instance-aware service discovery via environment variables
- PostgreSQL shared state for cross-instance coordination
- Redis for caching and session management
- Container naming: mcp-${INSTANCE_NAME}-service-name
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import uuid

import aiohttp
import asyncpg
import redis.asyncio as redis
from mcp import types
from mcp.client import Client
from mcp.client.stdio import stdio_client
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MULTI-INSTANCE CONFIGURATION
# ============================================================================

# Instance configuration - automatically detected from environment
INSTANCE_NAME = os.getenv("DOPEMUX_INSTANCE", "default")
PORT_BASE = int(os.getenv("PORT_BASE", "3000"))
CONTAINER_PREFIX = os.getenv("CONTAINER_PREFIX", f"mcp-{INSTANCE_NAME}")
NETWORK_NAME = os.getenv("NETWORK_NAME", f"mcp-network-{INSTANCE_NAME}")

# Integration bridge port (PORT_BASE + 16)
MCP_INTEGRATION_PORT = PORT_BASE + 16

# Service discovery - instance-aware container names
TASK_MASTER_URL = f"http://{CONTAINER_PREFIX}-task-master-ai:3005"
TASK_ORCHESTRATOR_URL = f"http://{CONTAINER_PREFIX}-task-orchestrator:3014"
LEANTIME_BRIDGE_URL = f"http://{CONTAINER_PREFIX}-leantime-bridge:3015"

# Shared infrastructure (external to instances)
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+asyncpg://dopemux:dopemux_password@postgres:5432/dopemux_tasks")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

logger.info(f"🚀 MCP Integration Bridge starting for instance: {INSTANCE_NAME}")
logger.info(f"📊 Port allocation: {MCP_INTEGRATION_PORT} (BASE+16)")
logger.info(f"🔗 Task Master: {TASK_MASTER_URL}")
logger.info(f"🔗 Task Orchestrator: {TASK_ORCHESTRATOR_URL}")
logger.info(f"🔗 Leantime Bridge: {LEANTIME_BRIDGE_URL}")

# ============================================================================
# DATA MODELS & DATABASE SCHEMA
# ============================================================================

class TaskStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# SQLAlchemy models for shared state
Base = declarative_base()

class TaskRecord(Base):
    """Shared task record across all Dopemux instances"""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    instance_id = Column(String, nullable=False, index=True)  # Which instance owns this task
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="planned")
    priority = Column(String, nullable=False, default="medium")
    project_id = Column(String, nullable=True, index=True)
    parent_task_id = Column(String, nullable=True, index=True)
    dependencies = Column(JSON, nullable=True)  # List of task IDs
    tags = Column(JSON, nullable=True)  # List of tags
    metadata = Column(JSON, nullable=True)  # Additional instance-specific data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = Column(String, nullable=True)
    estimated_hours = Column(Integer, nullable=True)

class ProjectRecord(Base):
    """Shared project record across all Dopemux instances"""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    instance_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic models for API
@dataclass
class Task:
    """Unified task model for integration bridge"""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    instance_id: str = INSTANCE_NAME
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = None
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

# ============================================================================
# DATABASE & CACHE MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manages PostgreSQL connections for shared state"""

    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_async_engine(
                POSTGRES_URL,
                echo=False,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("✅ Database connection established")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()

class CacheManager:
    """Manages Redis connections for caching and session state"""

    def __init__(self):
        self.redis_client = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                REDIS_URL,
                password=REDIS_PASSWORD if REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")

        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise

    async def get_client(self):
        """Get Redis client"""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

# ============================================================================
# MCP CLIENT MANAGEMENT (Instance-Aware)
# ============================================================================

class MCPClientManager:
    """Manages connections to instance-specific MCP servers"""

    def __init__(self):
        self.session = None

    async def initialize(self):
        """Initialize HTTP session for MCP server communication"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("✅ MCP client manager initialized")

    async def call_tool(self, service: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an instance-specific MCP service"""
        if not self.session:
            raise RuntimeError("MCP client not initialized")

        service_url = self._get_service_url(service)
        url = f"{service_url}/api/tools/{tool_name}"

        try:
            async with self.session.post(url, json=arguments) as response:
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"🔧 {service}.{tool_name} -> {result}")
                return result

        except aiohttp.ClientError as e:
            logger.error(f"❌ MCP call failed: {service}.{tool_name} - {e}")
            raise HTTPException(status_code=502, detail=f"Service {service} unavailable")

    def _get_service_url(self, service: str) -> str:
        """Get instance-specific service URL"""
        urls = {
            "task-master-ai": TASK_MASTER_URL,
            "task-orchestrator": TASK_ORCHESTRATOR_URL,
            "leantime-bridge": LEANTIME_BRIDGE_URL
        }
        url = urls.get(service)
        if not url:
            raise ValueError(f"Unknown service: {service}")
        return url

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all connected services"""
        if not self.session:
            return {"status": "not_initialized"}

        services = ["task-master-ai", "task-orchestrator", "leantime-bridge"]
        health_status = {}

        for service in services:
            try:
                service_url = self._get_service_url(service)
                async with self.session.get(f"{service_url}/health") as response:
                    health_status[service] = response.status == 200
            except Exception:
                health_status[service] = False

        return health_status

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

# ============================================================================
# CONPORT INTEGRATION FOR ADHD MEMORY MANAGEMENT
# ============================================================================

class ConPortClient:
    """ConPort client for ADHD-friendly context preservation across instances"""

    def __init__(self):
        self.session = None
        self.base_url = os.getenv("CONPORT_URL", "http://conport:3020")
        self.workspace_id = "/Users/hue/code/dopemux-mvp"  # Fixed workspace for this project
        self._initialized = False

    async def initialize(self):
        """Lazy initialization of HTTP session"""
        if not self._initialized:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self._initialized = True
            logger.info("✅ ConPort client initialized")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def get_context(self, context_token: str) -> Dict[str, Any]:
        """Get context from ConPort with circuit breaker pattern"""
        if not self.session:
            await self.initialize()

        try:
            url = f"{self.base_url}/api/context/{context_token}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    context = await response.json()
                    logger.debug(f"🧠 Retrieved context for token {context_token[:8]}...")
                    return context
                elif response.status == 404:
                    # New context token, return empty context
                    return {"workspace_id": self.workspace_id, "session_data": {}}
                else:
                    response.raise_for_status()

        except Exception as e:
            logger.warning(f"⚠️ ConPort context retrieval failed: {e}")
            # Fallback: try to get from Redis cache
            return await self._get_fallback_context(context_token)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def update_context(self, context_token: str, context_deltas: Dict[str, Any]) -> bool:
        """Update context in ConPort with deltas"""
        if not self.session:
            await self.initialize()

        try:
            url = f"{self.base_url}/api/context/{context_token}"
            payload = {
                "workspace_id": self.workspace_id,
                "deltas": context_deltas,
                "timestamp": datetime.utcnow().isoformat()
            }

            async with self.session.patch(url, json=payload) as response:
                if response.status in [200, 201]:
                    logger.debug(f"💾 Updated context for token {context_token[:8]}...")
                    # Also update fallback cache
                    await self._update_fallback_context(context_token, context_deltas)
                    return True
                else:
                    response.raise_for_status()

        except Exception as e:
            logger.warning(f"⚠️ ConPort context update failed: {e}")
            # Still update fallback cache
            await self._update_fallback_context(context_token, context_deltas)
            return False

    async def _get_fallback_context(self, context_token: str) -> Dict[str, Any]:
        """Get context from Redis fallback cache"""
        try:
            cache_client = await cache_manager.get_client()
            cached_context = await cache_client.get(f"context_fallback:{context_token}")
            if cached_context:
                return json.loads(cached_context)
        except Exception as e:
            logger.error(f"❌ Fallback context retrieval failed: {e}")

        # Ultimate fallback: empty context
        return {"workspace_id": self.workspace_id, "session_data": {}}

    async def _update_fallback_context(self, context_token: str, context_deltas: Dict[str, Any]):
        """Update Redis fallback cache with context deltas"""
        try:
            cache_client = await cache_manager.get_client()

            # Get existing fallback context
            existing_raw = await cache_client.get(f"context_fallback:{context_token}")
            existing_context = json.loads(existing_raw) if existing_raw else {"workspace_id": self.workspace_id, "session_data": {}}

            # Apply deltas
            for key, value in context_deltas.items():
                if value == "__DELETE__":
                    existing_context["session_data"].pop(key, None)
                else:
                    existing_context["session_data"][key] = value

            # Update cache with 1 hour TTL
            await cache_client.setex(
                f"context_fallback:{context_token}",
                3600,
                json.dumps(existing_context, default=str)
            )

        except Exception as e:
            logger.error(f"❌ Fallback context update failed: {e}")

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

class ConPortMiddleware:
    """Middleware for ADHD-friendly context preservation"""

    def __init__(self, app: FastAPI, conport_client: ConPortClient):
        self.app = app
        self.conport_client = conport_client

    async def __call__(self, request: Request, call_next):
        """Process request with context hydration and delta persistence"""
        # Extract context token from header
        context_token = request.headers.get("X-Context-Token")

        if context_token:
            # Hydrate request state with context
            try:
                context = await self.conport_client.get_context(context_token)
                request.state.context = context
                request.state.context_token = context_token
                request.state.context_deltas = {}  # Track changes during request

                logger.debug(f"🧠 Context hydrated for {request.url.path}")

            except Exception as e:
                logger.warning(f"⚠️ Context hydration failed: {e}")
                request.state.context = {"workspace_id": self.conport_client.workspace_id, "session_data": {}}
                request.state.context_token = context_token
                request.state.context_deltas = {}
        else:
            # No context token, create minimal state
            request.state.context = None
            request.state.context_token = None
            request.state.context_deltas = {}

        # Process request
        response = await call_next(request)

        # Persist context deltas after request completion
        if context_token and hasattr(request.state, 'context_deltas') and request.state.context_deltas:
            try:
                await self.conport_client.update_context(context_token, request.state.context_deltas)
                logger.debug(f"💾 Context deltas persisted for {request.url.path}")
            except Exception as e:
                logger.warning(f"⚠️ Context delta persistence failed: {e}")

        return response

# Global ConPort client
conport_client = ConPortClient()

# Helper function for ADHD-friendly context updates
def update_context_delta(request: Request, key: str, value: Any):
    """Update context delta during request processing"""
    if hasattr(request.state, 'context_deltas'):
        request.state.context_deltas[key] = value
        logger.debug(f"📝 Context delta: {key} = {value}")

# ============================================================================
# CORE INTEGRATION SERVICE
# ============================================================================

class TaskIntegrationService:
    """Core task integration with multi-instance shared state"""

    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager, mcp_manager: MCPClientManager):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.mcp_manager = mcp_manager

    async def parse_prd_to_tasks(self, prd_content: str, project_id: str) -> List[Task]:
        """
        Parse PRD using Task-Master-AI and create shared task structure
        ADHD-friendly: Clear progress indicators and manageable chunks
        """
        logger.info(f"🔍 Parsing PRD for project {project_id} (instance: {INSTANCE_NAME})")

        try:
            # Step 1: Use Task-Master-AI to parse PRD
            prd_result = await self.mcp_manager.call_tool(
                "task-master-ai",
                "parse_prd",
                {"content": prd_content, "project_id": project_id}
            )

            # Step 2: Convert to unified task format and store in shared database
            tasks = []
            async with self.db_manager.get_session() as session:
                for i, task_data in enumerate(prd_result.get("tasks", [])):
                    task = Task(
                        id=str(uuid.uuid4()),
                        title=task_data.get("title", ""),
                        description=task_data.get("description", ""),
                        status=TaskStatus.PLANNED,
                        priority=TaskPriority(task_data.get("priority", "medium")),
                        project_id=project_id,
                        instance_id=INSTANCE_NAME,
                        tags=task_data.get("tags", [])
                    )

                    # Store in shared database
                    task_record = TaskRecord(**asdict(task))
                    session.add(task_record)
                    tasks.append(task)

                await session.commit()

            # Step 3: Use Task-Orchestrator to analyze dependencies
            await self._analyze_task_dependencies(tasks)

            # Step 4: Create tasks in Leantime for tracking
            await self._sync_tasks_to_leantime(tasks)

            # Step 5: Cache results for fast access
            cache_client = await self.cache_manager.get_client()
            await cache_client.setex(
                f"project:{project_id}:tasks",
                3600,  # 1 hour cache
                json.dumps([asdict(task) for task in tasks], default=str)
            )

            logger.info(f"✅ Successfully processed {len(tasks)} tasks from PRD")
            return tasks

        except Exception as e:
            logger.error(f"❌ PRD parsing failed: {e}")
            raise

    async def _analyze_task_dependencies(self, tasks: List[Task]):
        """Use Task-Orchestrator to analyze and set dependencies"""
        try:
            task_descriptions = [
                {"id": t.id, "title": t.title, "description": t.description}
                for t in tasks
            ]

            dependency_result = await self.mcp_manager.call_tool(
                "task-orchestrator",
                "analyze_dependencies",
                {"tasks": task_descriptions}
            )

            # Update dependencies in shared database
            async with self.db_manager.get_session() as session:
                for dep in dependency_result.get("dependencies", []):
                    task_id = dep.get("task_id")
                    depends_on = dep.get("depends_on", [])

                    # Update task in database
                    result = await session.execute(
                        TaskRecord.__table__.update()
                        .where(TaskRecord.id == task_id)
                        .values(dependencies=depends_on, updated_at=datetime.utcnow())
                    )

                    # Update local task objects
                    for task in tasks:
                        if task.id == task_id:
                            task.dependencies = depends_on

                await session.commit()

        except Exception as e:
            logger.warning(f"⚠️ Dependency analysis failed: {e}")

    async def _sync_tasks_to_leantime(self, tasks: List[Task]):
        """Sync tasks to Leantime for project management tracking"""
        try:
            for task in tasks:
                leantime_result = await self.mcp_manager.call_tool(
                    "leantime-bridge",
                    "create_ticket",
                    {
                        "projectId": int(task.project_id) if task.project_id else 1,
                        "headline": task.title,
                        "description": task.description,
                        "priority": self._map_priority_to_leantime(task.priority),
                        "type": "task"
                    }
                )

                # Store Leantime ticket ID in task metadata
                if "id" in leantime_result:
                    task.tags.append(f"leantime_id:{leantime_result['id']}")

                    # Update in database
                    async with self.db_manager.get_session() as session:
                        await session.execute(
                            TaskRecord.__table__.update()
                            .where(TaskRecord.id == task.id)
                            .values(tags=task.tags, updated_at=datetime.utcnow())
                        )
                        await session.commit()

        except Exception as e:
            logger.warning(f"⚠️ Leantime sync failed: {e}")

    def _map_priority_to_leantime(self, priority: TaskPriority) -> str:
        """Map unified priority to Leantime priority format"""
        mapping = {
            TaskPriority.LOW: "1",
            TaskPriority.MEDIUM: "2",
            TaskPriority.HIGH: "3",
            TaskPriority.CRITICAL: "4"
        }
        return mapping.get(priority, "2")

    async def get_next_actionable_tasks(self, project_id: str, limit: int = 5) -> List[Task]:
        """
        Get next actionable tasks for ADHD-friendly workflow
        Checks shared database for cross-instance task coordination
        """
        try:
            # First check cache
            cache_client = await self.cache_manager.get_client()
            cache_key = f"project:{project_id}:actionable_tasks"
            cached_result = await cache_client.get(cache_key)

            if cached_result:
                logger.debug("📋 Returning cached actionable tasks")
                task_dicts = json.loads(cached_result)
                return [Task(**task_dict) for task_dict in task_dicts]

            # Query database for actionable tasks
            async with self.db_manager.get_session() as session:
                # Get tasks with no blocking dependencies
                result = await session.execute(
                    f"""
                    SELECT t.* FROM tasks t
                    WHERE t.project_id = :project_id
                    AND t.status = 'planned'
                    AND (
                        t.dependencies IS NULL
                        OR t.dependencies = '[]'::json
                        OR NOT EXISTS (
                            SELECT 1 FROM tasks dep
                            WHERE dep.id = ANY(
                                SELECT json_array_elements_text(t.dependencies)
                            )
                            AND dep.status != 'completed'
                        )
                    )
                    ORDER BY
                        CASE t.priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        t.created_at
                    LIMIT :limit
                    """,
                    {"project_id": project_id, "limit": limit}
                )

                task_records = result.fetchall()
                actionable_tasks = [
                    Task(
                        id=record.id,
                        title=record.title,
                        description=record.description,
                        status=TaskStatus(record.status),
                        priority=TaskPriority(record.priority),
                        instance_id=record.instance_id,
                        project_id=record.project_id,
                        dependencies=record.dependencies or [],
                        tags=record.tags or [],
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                        assigned_to=record.assigned_to,
                        estimated_hours=record.estimated_hours
                    )
                    for record in task_records
                ]

                # Cache result for 5 minutes
                await cache_client.setex(
                    cache_key,
                    300,
                    json.dumps([asdict(task) for task in actionable_tasks], default=str)
                )

                logger.info(f"📋 Found {len(actionable_tasks)} actionable tasks for project {project_id}")
                return actionable_tasks

        except Exception as e:
            logger.error(f"❌ Failed to get actionable tasks: {e}")
            return []

    async def update_task_status(self, task_id: str, new_status: TaskStatus, assigned_to: str = None) -> Dict[str, Any]:
        """
        Update task status across all systems with dependency resolution
        ADHD-friendly: Clear progress feedback and automatic next-action suggestions
        """
        logger.info(f"🔄 Updating task {task_id} to status {new_status.value} (instance: {INSTANCE_NAME})")

        try:
            async with self.db_manager.get_session() as session:
                # Get current task
                result = await session.execute(
                    TaskRecord.__table__.select().where(TaskRecord.id == task_id)
                )
                task_record = result.fetchone()

                if not task_record:
                    raise ValueError(f"Task {task_id} not found")

                old_status = task_record.status

                # Update in shared database
                update_data = {
                    "status": new_status.value,
                    "updated_at": datetime.utcnow()
                }
                if assigned_to:
                    update_data["assigned_to"] = assigned_to

                await session.execute(
                    TaskRecord.__table__.update()
                    .where(TaskRecord.id == task_id)
                    .values(**update_data)
                )
                await session.commit()

                # Sync to Leantime
                await self._sync_status_to_leantime(task_id, new_status)

                # Check for newly unblocked tasks if this task was completed
                newly_unblocked = []
                if new_status == TaskStatus.COMPLETED:
                    newly_unblocked = await self._check_and_unblock_tasks(task_id)

                # Invalidate actionable tasks cache
                cache_client = await self.cache_manager.get_client()
                cache_key = f"project:{task_record.project_id}:actionable_tasks"
                await cache_client.delete(cache_key)

                # ADHD accommodation: Get next suggested actions
                next_actions = await self.get_next_actionable_tasks(task_record.project_id, 3)

                response = {
                    "success": True,
                    "task_id": task_id,
                    "old_status": old_status,
                    "new_status": new_status.value,
                    "instance": INSTANCE_NAME,
                    "timestamp": datetime.utcnow().isoformat(),
                    "newly_unblocked_count": len(newly_unblocked),
                    "newly_unblocked_tasks": [
                        {"id": t.id, "title": t.title, "priority": t.priority.value}
                        for t in newly_unblocked
                    ],
                    "suggested_next_actions": [
                        {"id": t.id, "title": t.title, "priority": t.priority.value}
                        for t in next_actions
                    ]
                }

                # Log progress for ADHD accommodation
                if new_status == TaskStatus.COMPLETED:
                    progress_summary = await self._get_project_progress(task_record.project_id)
                    response["progress_summary"] = progress_summary
                    logger.info(f"✅ Task completed! Project progress: {progress_summary['progress_percentage']:.1f}%")

                return response

        except Exception as e:
            logger.error(f"❌ Task status update failed: {e}")
            raise

    async def _sync_status_to_leantime(self, task_id: str, status: TaskStatus):
        """Sync task status to Leantime"""
        try:
            # Extract Leantime ID from task tags
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    TaskRecord.__table__.select().where(TaskRecord.id == task_id)
                )
                task_record = result.fetchone()

                if not task_record or not task_record.tags:
                    return

                leantime_id = None
                for tag in task_record.tags:
                    if tag.startswith("leantime_id:"):
                        leantime_id = tag.split(":", 1)[1]
                        break

                if leantime_id:
                    # Map status to Leantime format
                    leantime_status = self._map_status_to_leantime(status)

                    await self.mcp_manager.call_tool(
                        "leantime-bridge",
                        "update_ticket_status",
                        {
                            "ticketId": int(leantime_id),
                            "status": leantime_status
                        }
                    )

        except Exception as e:
            logger.warning(f"⚠️ Leantime status sync failed: {e}")

    def _map_status_to_leantime(self, status: TaskStatus) -> str:
        """Map unified status to Leantime status format"""
        mapping = {
            TaskStatus.PLANNED: "3",  # Open
            TaskStatus.IN_PROGRESS: "2",  # In progress
            TaskStatus.BLOCKED: "2",  # In progress (with note)
            TaskStatus.COMPLETED: "4",  # Closed
            TaskStatus.CANCELLED: "4"  # Closed
        }
        return mapping.get(status, "3")

    async def _check_and_unblock_tasks(self, completed_task_id: str) -> List[Task]:
        """Check for tasks that are now unblocked by this completion"""
        try:
            async with self.db_manager.get_session() as session:
                # Find tasks that depend on the completed task
                result = await session.execute(
                    f"""
                    SELECT * FROM tasks
                    WHERE status = 'planned'
                    AND dependencies IS NOT NULL
                    AND dependencies != '[]'::json
                    AND :completed_task_id = ANY(
                        SELECT json_array_elements_text(dependencies)
                    )
                    """,
                    {"completed_task_id": completed_task_id}
                )

                potentially_unblocked = result.fetchall()
                newly_unblocked = []

                for task_record in potentially_unblocked:
                    # Check if all dependencies are now completed
                    dependencies = task_record.dependencies or []
                    all_completed = True

                    for dep_id in dependencies:
                        dep_result = await session.execute(
                            TaskRecord.__table__.select().where(TaskRecord.id == dep_id)
                        )
                        dep_record = dep_result.fetchone()

                        if not dep_record or dep_record.status != 'completed':
                            all_completed = False
                            break

                    if all_completed:
                        task = Task(
                            id=task_record.id,
                            title=task_record.title,
                            description=task_record.description,
                            status=TaskStatus(task_record.status),
                            priority=TaskPriority(task_record.priority),
                            instance_id=task_record.instance_id,
                            project_id=task_record.project_id,
                            dependencies=task_record.dependencies or [],
                            tags=task_record.tags or [],
                            created_at=task_record.created_at,
                            updated_at=task_record.updated_at
                        )
                        newly_unblocked.append(task)

                logger.info(f"🔓 {len(newly_unblocked)} tasks newly unblocked by completion of {completed_task_id}")
                return newly_unblocked

        except Exception as e:
            logger.error(f"❌ Failed to check unblocked tasks: {e}")
            return []

    async def _get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Get project progress summary for ADHD-friendly visualization"""
        try:
            async with self.db_manager.get_session() as session:
                # Count tasks by status
                result = await session.execute(
                    f"""
                    SELECT status, COUNT(*) as count
                    FROM tasks
                    WHERE project_id = :project_id
                    GROUP BY status
                    """,
                    {"project_id": project_id}
                )

                status_counts = {record.status: record.count for record in result.fetchall()}

                total_tasks = sum(status_counts.values())
                completed_tasks = status_counts.get('completed', 0)
                in_progress_tasks = status_counts.get('in_progress', 0)
                blocked_tasks = status_counts.get('blocked', 0)

                progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

                # Create visual progress bar
                progress_blocks = int(progress_percentage / 10)  # 10 blocks total
                progress_bar = "█" * progress_blocks + "░" * (10 - progress_blocks)

                return {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "in_progress_tasks": in_progress_tasks,
                    "blocked_tasks": blocked_tasks,
                    "progress_percentage": progress_percentage,
                    "progress_bar": f"[{progress_bar}] {completed_tasks}/{total_tasks}",
                    "status_distribution": status_counts
                }

        except Exception as e:
            logger.error(f"❌ Failed to get project progress: {e}")
            return {"error": str(e)}

    async def create_workflow_from_template(self, template_name: str, project_id: str, context: Dict[str, Any]) -> List[Task]:
        """
        Create tasks from ADHD-friendly workflow templates
        Templates provide structure for common development patterns
        """
        logger.info(f"🧩 Creating workflow from template '{template_name}' for project {project_id}")

        templates = {
            "feature_development": {
                "description": "Standard feature development workflow",
                "tasks": [
                    {
                        "title": "Research and analyze requirements",
                        "description": "Understand the feature requirements and gather necessary information",
                        "priority": "high",
                        "estimated_hours": 2,
                        "tags": ["research", "planning"]
                    },
                    {
                        "title": "Design technical approach",
                        "description": "Create technical design and architecture for the feature",
                        "priority": "high",
                        "estimated_hours": 3,
                        "tags": ["design", "architecture"],
                        "depends_on": [0]  # Depends on research task
                    },
                    {
                        "title": "Implement core functionality",
                        "description": "Develop the main feature implementation",
                        "priority": "medium",
                        "estimated_hours": 8,
                        "tags": ["development", "implementation"],
                        "depends_on": [1]  # Depends on design task
                    },
                    {
                        "title": "Write tests",
                        "description": "Create comprehensive tests for the feature",
                        "priority": "medium",
                        "estimated_hours": 4,
                        "tags": ["testing", "quality"],
                        "depends_on": [2]  # Depends on implementation
                    },
                    {
                        "title": "Documentation and review",
                        "description": "Write documentation and conduct code review",
                        "priority": "medium",
                        "estimated_hours": 2,
                        "tags": ["documentation", "review"],
                        "depends_on": [3]  # Depends on testing
                    }
                ]
            },
            "bug_fix": {
                "description": "Systematic bug fixing workflow",
                "tasks": [
                    {
                        "title": "Reproduce and investigate bug",
                        "description": "Understand the bug and create reproduction steps",
                        "priority": "high",
                        "estimated_hours": 2,
                        "tags": ["investigation", "debugging"]
                    },
                    {
                        "title": "Identify root cause",
                        "description": "Find the underlying cause of the issue",
                        "priority": "high",
                        "estimated_hours": 2,
                        "tags": ["analysis", "debugging"],
                        "depends_on": [0]
                    },
                    {
                        "title": "Implement fix",
                        "description": "Develop and test the fix",
                        "priority": "medium",
                        "estimated_hours": 3,
                        "tags": ["development", "fix"],
                        "depends_on": [1]
                    },
                    {
                        "title": "Verify fix and add regression tests",
                        "description": "Ensure fix works and prevent future regressions",
                        "priority": "medium",
                        "estimated_hours": 2,
                        "tags": ["testing", "verification"],
                        "depends_on": [2]
                    }
                ]
            },
            "setup_integration": {
                "description": "Setting up new system integration",
                "tasks": [
                    {
                        "title": "Research integration requirements",
                        "description": "Understand the integration needs and constraints",
                        "priority": "high",
                        "estimated_hours": 3,
                        "tags": ["research", "integration"]
                    },
                    {
                        "title": "Set up development environment",
                        "description": "Configure local environment for integration work",
                        "priority": "medium",
                        "estimated_hours": 2,
                        "tags": ["setup", "environment"],
                        "depends_on": [0]
                    },
                    {
                        "title": "Implement basic connection",
                        "description": "Create basic connectivity between systems",
                        "priority": "medium",
                        "estimated_hours": 4,
                        "tags": ["development", "connectivity"],
                        "depends_on": [1]
                    },
                    {
                        "title": "Add error handling and monitoring",
                        "description": "Implement robust error handling and monitoring",
                        "priority": "medium",
                        "estimated_hours": 3,
                        "tags": ["reliability", "monitoring"],
                        "depends_on": [2]
                    },
                    {
                        "title": "Write integration tests",
                        "description": "Create comprehensive integration tests",
                        "priority": "medium",
                        "estimated_hours": 4,
                        "tags": ["testing", "integration"],
                        "depends_on": [3]
                    }
                ]
            }
        }

        template = templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        try:
            # Create tasks from template
            created_tasks = []
            task_id_mapping = {}  # Map template index to actual task ID

            async with self.db_manager.get_session() as session:
                for i, task_template in enumerate(template["tasks"]):
                    # Apply context substitutions
                    title = task_template["title"]
                    description = task_template["description"]

                    # Substitute context variables
                    for key, value in context.items():
                        title = title.replace(f"{{{key}}}", str(value))
                        description = description.replace(f"{{{key}}}", str(value))

                    task = Task(
                        id=str(uuid.uuid4()),
                        title=title,
                        description=description,
                        status=TaskStatus.PLANNED,
                        priority=TaskPriority(task_template.get("priority", "medium")),
                        project_id=project_id,
                        instance_id=INSTANCE_NAME,
                        tags=task_template.get("tags", []) + [f"template:{template_name}"],
                        estimated_hours=task_template.get("estimated_hours")
                    )

                    task_id_mapping[i] = task.id
                    created_tasks.append(task)

                    # Store in database
                    task_record = TaskRecord(**asdict(task))
                    session.add(task_record)

                # Set up dependencies after all tasks are created
                for i, task_template in enumerate(template["tasks"]):
                    if "depends_on" in task_template:
                        dependencies = [
                            task_id_mapping[dep_index]
                            for dep_index in task_template["depends_on"]
                        ]

                        # Update task dependencies
                        created_tasks[i].dependencies = dependencies

                        # Update in database
                        await session.execute(
                            TaskRecord.__table__.update()
                            .where(TaskRecord.id == created_tasks[i].id)
                            .values(dependencies=dependencies)
                        )

                await session.commit()

            # Sync to Leantime
            await self._sync_tasks_to_leantime(created_tasks)

            logger.info(f"✅ Created {len(created_tasks)} tasks from template '{template_name}'")
            return created_tasks

        except Exception as e:
            logger.error(f"❌ Template workflow creation failed: {e}")
            raise

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Global managers
db_manager = DatabaseManager()
cache_manager = CacheManager()
mcp_manager = MCPClientManager()
task_service = TaskIntegrationService(db_manager, cache_manager, mcp_manager)

# FastAPI app
app = FastAPI(
    title=f"MCP Integration Bridge - {INSTANCE_NAME}",
    version="1.0.0",
    description=f"Task management coordination for Dopemux instance: {INSTANCE_NAME}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add ConPort middleware for ADHD context preservation
app.middleware("http")(ConPortMiddleware(app, conport_client))

# Pydantic models for API requests
class PRDParseRequest(BaseModel):
    prd_content: str
    project_id: str

class TaskStatusUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None

class WorkflowTemplate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    template_type: str
    tasks: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WorkflowFromTemplateRequest(BaseModel):
    template_name: str
    project_id: str
    context: Dict[str, Any] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize all connections on startup"""
    try:
        await db_manager.initialize()
        await cache_manager.initialize()
        await mcp_manager.initialize()
        await conport_client.initialize()  # Initialize ConPort for ADHD context preservation

        logger.info(f"🚀 MCP Integration Bridge started successfully for instance: {INSTANCE_NAME}")
        logger.info(f"📊 Running on port: {MCP_INTEGRATION_PORT}")
        logger.info(f"🧠 ConPort ADHD context preservation enabled")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    await mcp_manager.close()
    await cache_manager.close()
    await db_manager.close()
    await conport_client.close()  # Clean up ConPort connection
    logger.info(f"✅ MCP Integration Bridge shut down for instance: {INSTANCE_NAME}")
    logger.info(f"🧠 ConPort context preserved for next session")

@app.get("/health")
async def health_check():
    """Health check with service status"""
    mcp_health = await mcp_manager.health_check_all()

    return {
        "status": "healthy",
        "instance": INSTANCE_NAME,
        "port": MCP_INTEGRATION_PORT,
        "timestamp": datetime.utcnow().isoformat(),
        "services": mcp_health
    }

@app.post("/api/parse-prd")
async def parse_prd(request: PRDParseRequest, http_request: Request):
    """Parse PRD document into tasks across all systems with ADHD context preservation"""
    try:
        # ADHD context: Track PRD parsing activity
        if hasattr(http_request.state, 'context_token'):
            update_context_delta(http_request, 'last_prd_parse', {
                'project_id': request.project_id,
                'timestamp': datetime.utcnow().isoformat(),
                'prd_length': len(request.prd_content),
                'action': 'parsing_prd'
            })

        tasks = await task_service.parse_prd_to_tasks(
            request.prd_content,
            request.project_id
        )

        # ADHD context: Record successful parsing and next actions
        if hasattr(http_request.state, 'context_token'):
            actionable_tasks = [t for t in tasks if not t.dependencies]
            update_context_delta(http_request, 'prd_parse_result', {
                'project_id': request.project_id,
                'total_tasks_created': len(tasks),
                'immediately_actionable': len(actionable_tasks),
                'next_suggested_task': actionable_tasks[0].title if actionable_tasks else None,
                'status': 'completed',
                'instance': INSTANCE_NAME
            })

        response = {
            "success": True,
            "instance": INSTANCE_NAME,
            "task_count": len(tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "dependencies": task.dependencies,
                    "instance_id": task.instance_id
                }
                for task in tasks
            ],
            "adhd_guidance": {
                "next_focus": tasks[0].title if tasks else None,
                "quick_start_tip": "🎯 Start with the first task to build momentum!",
                "total_work_estimate": f"{sum(t.estimated_hours or 2 for t in tasks)} hours estimated"
            }
        }

        return response

    except Exception as e:
        logger.error(f"❌ PRD parsing failed: {e}")
        # ADHD context: Track errors for learning
        if hasattr(http_request.state, 'context_token'):
            update_context_delta(http_request, 'last_error', {
                'action': 'prd_parsing',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'project_id': request.project_id
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/next-tasks")
async def get_next_tasks(project_id: str, limit: int = 5):
    """Get next actionable tasks for ADHD-friendly workflow"""
    try:
        tasks = await task_service.get_next_actionable_tasks(project_id, limit)

        return {
            "instance": INSTANCE_NAME,
            "project_id": project_id,
            "actionable_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority.value,
                    "estimated_hours": task.estimated_hours,
                    "instance_id": task.instance_id
                }
                for task in tasks
            ]
        }
    except Exception as e:
        logger.error(f"❌ Failed to get next tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/tasks/{task_id}/status")
async def update_task_status(task_id: str, request: TaskStatusUpdate, http_request: Request):
    """Update task status with ADHD-friendly progress feedback and context preservation"""
    try:
        # ADHD context: Track task status changes for momentum building
        if hasattr(http_request.state, 'context_token'):
            update_context_delta(http_request, 'last_task_update', {
                'task_id': task_id,
                'new_status': request.status,
                'timestamp': datetime.utcnow().isoformat(),
                'instance': INSTANCE_NAME
            })

        result = await task_service.update_task_status(
            task_id,
            TaskStatus(request.status),
            request.assigned_to
        )

        # ADHD context: Record progress and celebration moments
        if hasattr(http_request.state, 'context_token'):
            context_update = {
                'task_completion_streak': http_request.state.context.get('session_data', {}).get('task_completion_streak', 0),
                'daily_progress': http_request.state.context.get('session_data', {}).get('daily_progress', [])
            }

            # Increment streak for completed tasks
            if request.status == 'completed':
                context_update['task_completion_streak'] += 1
                context_update['daily_progress'].append({
                    'task_id': task_id,
                    'completed_at': datetime.utcnow().isoformat(),
                    'instance': INSTANCE_NAME
                })

                # ADHD motivation: Celebrate milestones
                if context_update['task_completion_streak'] % 3 == 0:
                    context_update['milestone_celebration'] = {
                        'type': 'completion_streak',
                        'count': context_update['task_completion_streak'],
                        'message': f"🎉 Amazing! {context_update['task_completion_streak']} tasks completed!",
                        'timestamp': datetime.utcnow().isoformat()
                    }

            # Reset streak if task is moved back
            elif request.status in ['planned', 'blocked']:
                context_update['task_completion_streak'] = 0

            # Update context with progress tracking
            for key, value in context_update.items():
                update_context_delta(http_request, key, value)

        # Add ADHD-friendly elements to response
        if 'suggested_next_actions' in result:
            result['adhd_guidance'] = {
                'celebration': "🎉 Great progress!" if request.status == 'completed' else "🚀 Keep going!",
                'next_focus': result['suggested_next_actions'][0]['title'] if result['suggested_next_actions'] else "No immediate tasks ready",
                'momentum_tip': "Strike while the iron is hot - tackle the next task!" if request.status == 'completed' else "One step at a time!"
            }

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Task status update failed: {e}")
        # ADHD context: Track errors for pattern recognition
        if hasattr(http_request.state, 'context_token'):
            update_context_delta(http_request, 'last_error', {
                'action': 'task_status_update',
                'task_id': task_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow-from-template")
async def create_workflow_from_template(request: WorkflowFromTemplateRequest):
    """Create task workflow from ADHD-friendly template"""
    try:
        tasks = await task_service.create_workflow_from_template(
            request.template_name,
            request.project_id,
            request.context
        )

        return {
            "success": True,
            "instance": INSTANCE_NAME,
            "template_name": request.template_name,
            "project_id": request.project_id,
            "tasks_created": len(tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "dependencies": task.dependencies,
                    "estimated_hours": task.estimated_hours
                }
                for task in tasks
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Workflow template creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/dashboard")
async def get_project_dashboard(project_id: str):
    """Get ADHD-friendly project dashboard with progress visualization"""
    try:
        # Get project progress summary
        progress = await task_service._get_project_progress(project_id)

        # Get actionable tasks
        actionable_tasks = await task_service.get_next_actionable_tasks(project_id, 5)

        # Get recent activity (last 24 hours)
        async with task_service.db_manager.get_session() as session:
            recent_updates = await session.execute(
                f"""
                SELECT id, title, status, updated_at
                FROM tasks
                WHERE project_id = :project_id
                AND updated_at >= NOW() - INTERVAL '24 hours'
                ORDER BY updated_at DESC
                LIMIT 10
                """,
                {"project_id": project_id}
            )

            recent_activity = [
                {
                    "id": record.id,
                    "title": record.title,
                    "status": record.status,
                    "updated_at": record.updated_at.isoformat()
                }
                for record in recent_updates.fetchall()
            ]

        # ADHD-friendly dashboard with visual elements
        dashboard = {
            "instance": INSTANCE_NAME,
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat(),
            "progress_summary": progress,
            "adhd_helpers": {
                "next_focus": actionable_tasks[0] if actionable_tasks else None,
                "quick_wins": [
                    task for task in actionable_tasks
                    if task.estimated_hours and task.estimated_hours <= 2
                ],
                "motivation": {
                    "completed_today": len([a for a in recent_activity if a["status"] == "completed"]),
                    "streak_encouragement": "🎯 Keep up the momentum!" if progress.get("completed_tasks", 0) > 0 else "🚀 Ready to start!"
                }
            },
            "actionable_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority.value,
                    "estimated_hours": task.estimated_hours,
                    "difficulty_indicator": "🟢 Easy" if (task.estimated_hours or 4) <= 2 else "🟡 Medium" if (task.estimated_hours or 4) <= 6 else "🔴 Complex"
                }
                for task in actionable_tasks
            ],
            "recent_activity": recent_activity
        }

        # Cache dashboard for 2 minutes (fresh but not overwhelming)
        cache_client = await task_service.cache_manager.get_client()
        await cache_client.setex(
            f"dashboard:{project_id}",
            120,
            json.dumps(dashboard, default=str)
        )

        return dashboard

    except Exception as e:
        logger.error(f"❌ Dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow-templates")
async def list_workflow_templates():
    """List available ADHD-friendly workflow templates"""
    templates = {
        "feature_development": {
            "name": "Feature Development",
            "description": "Standard feature development workflow with ADHD-friendly structure",
            "estimated_tasks": 5,
            "total_estimated_hours": 19,
            "difficulty": "medium",
            "adhd_benefits": ["Clear progression", "Built-in breaks", "Celebration points"]
        },
        "bug_fix": {
            "name": "Bug Fix",
            "description": "Systematic bug fixing workflow with investigation structure",
            "estimated_tasks": 4,
            "total_estimated_hours": 9,
            "difficulty": "low",
            "adhd_benefits": ["Clear investigation steps", "Quick resolution", "Immediate feedback"]
        },
        "setup_integration": {
            "name": "Setup Integration",
            "description": "Setting up new system integration with proper testing",
            "estimated_tasks": 5,
            "total_estimated_hours": 16,
            "difficulty": "high",
            "adhd_benefits": ["Structured approach", "Built-in validation", "Progress checkpoints"]
        }
    }

    return {
        "instance": INSTANCE_NAME,
        "available_templates": templates,
        "total_templates": len(templates)
    }

@app.get("/api/debug/instance-info")
async def debug_instance_info():
    """Debug endpoint with instance configuration"""
    return {
        "instance_name": INSTANCE_NAME,
        "port_base": PORT_BASE,
        "integration_port": MCP_INTEGRATION_PORT,
        "container_prefix": CONTAINER_PREFIX,
        "network_name": NETWORK_NAME,
        "service_urls": {
            "task_master": TASK_MASTER_URL,
            "task_orchestrator": TASK_ORCHESTRATOR_URL,
            "leantime_bridge": LEANTIME_BRIDGE_URL
        },
        "database_url": POSTGRES_URL,
        "redis_url": REDIS_URL
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=MCP_INTEGRATION_PORT,
        reload=False  # Disable reload in production
    )