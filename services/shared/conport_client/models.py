"""
Shared Pydantic models for ConPort data structures.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Decision(BaseModel):
    """Decision record."""

    id: Optional[int] = None
    summary: str
    rationale: Optional[str] = None
    implementation_details: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None


class ProgressEntry(BaseModel):
    """Progress/task entry."""

    id: Optional[int] = None
    status: str  # TODO, IN_PROGRESS, DONE, BLOCKED
    description: str
    parent_id: Optional[int] = None
    linked_item_type: Optional[str] = None
    linked_item_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class SystemPattern(BaseModel):
    """System/coding pattern."""

    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None


class CustomData(BaseModel):
    """Custom key-value data."""

    category: str
    key: str
    value: dict
    timestamp: Optional[datetime] = None


class ActiveContext(BaseModel):
    """Active context data."""

    workspace_id: str
    session_id: str = "default"
    content: dict = Field(default_factory=dict)
    updated_at: Optional[datetime] = None
