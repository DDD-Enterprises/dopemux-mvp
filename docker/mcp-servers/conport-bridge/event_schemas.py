"""Event type definitions for ConPort Event Bridge"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DecisionLoggedEvent(BaseModel):
    """Event schema for decision.logged"""
    event_type: str = "decision.logged"
    timestamp: str
    source: str
    data: Dict[str, Any]  # Contains: id, summary, rationale, tags, etc.


class DecisionUpdatedEvent(BaseModel):
    """Event schema for decision.updated"""
    event_type: str = "decision.updated"
    timestamp: str
    source: str
    data: Dict[str, Any]


class ProgressUpdatedEvent(BaseModel):
    """Event schema for progress.updated"""
    event_type: str = "progress.updated"
    timestamp: str
    source: str
    data: Dict[str, Any]


# Event type registry
EVENT_TYPES = {
    "decision.logged": DecisionLoggedEvent,
    "decision.updated": DecisionUpdatedEvent,
    "progress.updated": ProgressUpdatedEvent,
}
