"""
DopeconBridge Data Models - SQLAlchemy ORM and Pydantic schemas.

Extracted from main.py lines 111-223.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.ext.declarative import declarative_base


# SQLAlchemy Base
Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class TaskStatus(Enum):
    """Task status values."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# SQLAlchemy ORM MODELS
# ============================================================================

class TaskRecord(Base):
    """Shared task record across all Dopemux instances."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    instance_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="planned")
    priority = Column(String, nullable=False, default="medium")
    project_id = Column(String, nullable=True, index=True)
    parent_task_id = Column(String, nullable=True, index=True)
    dependencies = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    task_metadata = Column('metadata', JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = Column(String, nullable=True)
    estimated_hours = Column(Integer, nullable=True)


class ProjectRecord(Base):
    """Shared project record across all Dopemux instances."""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    instance_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    project_metadata = Column('metadata', JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DdgDecision(Base):
    """Dope Decision Graph - Decision records."""
    __tablename__ = "ddg_decisions"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, index=True, nullable=False)
    instance_id = Column(String, index=True, nullable=True)
    summary = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DdgProgress(Base):
    """Dope Decision Graph - Progress records."""
    __tablename__ = "ddg_progress"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, index=True, nullable=False)
    instance_id = Column(String, index=True, nullable=True)
    status = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    percentage = Column(Integer, default=0)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DdgEmbedding(Base):
    """Optional embeddings store (fallback when vector DB not used)."""
    __tablename__ = "ddg_embeddings"

    id = Column(String, primary_key=True)  # decision_id
    vector = Column(JSON, nullable=False)  # Store as JSON array
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# DATACLASS MODELS
# ============================================================================

@dataclass
class Task:
    """Unified task model for integration bridge."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    instance_id: str = "default"
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = None
