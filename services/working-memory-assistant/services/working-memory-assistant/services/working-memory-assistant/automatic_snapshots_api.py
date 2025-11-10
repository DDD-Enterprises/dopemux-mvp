#!/usr/bin/env python3
"""
Automatic Snapshots API for Working Memory Assistant

REST API endpoints for managing automatic snapshot triggers and monitoring.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from automatic_snapshots import (
    SnapshotTrigger,
    get_automatic_snapshots_service,
    register_snapshot_trigger,
    manual_snapshot_trigger,
    start_automatic_snapshots,
    stop_automatic_snapshots
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automatic", tags=["automatic-snapshots"])

# Pydantic models for API
class SnapshotTriggerRequest(BaseModel):
    """Request model for creating snapshot triggers."""
    user_id: str = Field(..., description="User identifier")
    trigger_type: str = Field(..., description="Type of trigger: attention_shift, manual, scheduled")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    priority_threshold: float = Field(0.5, description="Minimum priority score to trigger (0.0-1.0)")
    cooldown_seconds: int = Field(300, description="Minimum seconds between snapshots")
    enabled: bool = Field(True, description="Whether the trigger is enabled")

class SnapshotTriggerResponse(BaseModel):
    """Response model for snapshot trigger operations."""
    trigger_type: str
    user_id: str
    session_id: Optional[str]
    priority_threshold: float
    cooldown_seconds: int
    enabled: bool

class ManualSnapshotRequest(BaseModel):
    """Request model for manual snapshot triggers."""
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")

class SnapshotStatistics(BaseModel):
    """Statistics about automatic snapshots."""
    user_id: str
    total_snapshots: int
    trigger_stats: List[Dict[str, Any]]
    active_triggers: int

# API Endpoints

@router.post("/triggers", response_model=SnapshotTriggerResponse)
async def create_trigger(trigger_req: SnapshotTriggerRequest):
    """Create a new automatic snapshot trigger."""
    try:
        trigger = SnapshotTrigger(
            trigger_type=trigger_req.trigger_type,
            user_id=trigger_req.user_id,
            session_id=trigger_req.session_id,
            priority_threshold=trigger_req.priority_threshold,
            cooldown_seconds=trigger_req.cooldown_seconds,
            enabled=trigger_req.enabled
        )

        await register_snapshot_trigger(trigger)

        return SnapshotTriggerResponse(
            trigger_type=trigger.trigger_type,
            user_id=trigger.user_id,
            session_id=trigger.session_id,
            priority_threshold=trigger.priority_threshold,
            cooldown_seconds=trigger.cooldown_seconds,
            enabled=trigger.enabled
        )

    except Exception as e:
        logger.error(f"Failed to create trigger: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trigger")

@router.delete("/triggers/{user_id}/{trigger_type}")
async def delete_trigger(user_id: str, trigger_type: str):
    """Delete an automatic snapshot trigger."""
    try:
        service = await get_automatic_snapshots_service()
        await service.unregister_trigger(user_id, trigger_type)
        return {"message": f"Trigger {trigger_type} deleted for user {user_id}"}

    except Exception as e:
        logger.error(f"Failed to delete trigger: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete trigger")

@router.get("/triggers", response_model=List[SnapshotTriggerResponse])
async def list_triggers(user_id: Optional[str] = None):
    """List all automatic snapshot triggers."""
    try:
        service = await get_automatic_snapshots_service()
        triggers = await service.list_triggers(user_id)

        return [
            SnapshotTriggerResponse(
                trigger_type=t.trigger_type,
                user_id=t.user_id,
                session_id=t.session_id,
                priority_threshold=t.priority_threshold,
                cooldown_seconds=t.cooldown_seconds,
                enabled=t.enabled
            ) for t in triggers
        ]

    except Exception as e:
        logger.error(f"Failed to list triggers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list triggers")

@router.post("/snapshot")
async def manual_snapshot(snapshot_req: ManualSnapshotRequest, background_tasks: BackgroundTasks):
    """Manually trigger an automatic snapshot."""
    try:
        # Run in background to avoid blocking the API response
        background_tasks.add_task(manual_snapshot_trigger, snapshot_req.user_id, snapshot_req.session_id)

        return {
            "message": f"Manual snapshot triggered for user {snapshot_req.user_id}",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Failed to trigger manual snapshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger snapshot")

@router.get("/statistics/{user_id}", response_model=SnapshotStatistics)
async def get_statistics(user_id: str):
    """Get snapshot statistics for a user."""
    try:
        service = await get_automatic_snapshots_service()
        stats = await service.get_snapshot_statistics(user_id)
        return SnapshotStatistics(**stats)

    except Exception as e:
        logger.error(f"Failed to get statistics for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.post("/start-monitoring")
async def start_monitoring():
    """Start the automatic snapshots monitoring service."""
    try:
        await start_automatic_snapshots()
        return {"message": "Automatic snapshots monitoring started"}

    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@router.post("/stop-monitoring")
async def stop_monitoring():
    """Stop the automatic snapshots monitoring service."""
    try:
        await stop_automatic_snapshots()
        return {"message": "Automatic snapshots monitoring stopped"}

    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@router.get("/status")
async def get_monitoring_status():
    """Get the current status of automatic snapshots monitoring."""
    try:
        service = await get_automatic_snapshots_service()
        return {
            "monitoring_active": service.monitoring_active if service else False,
            "active_triggers": len(service.active_triggers) if service else 0,
            "monitoring_interval": service.monitoring_interval if service else 0,
            "max_concurrent_snapshots": service.max_concurrent_snapshots if service else 0
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")

# Default triggers for common use cases
DEFAULT_TRIGGERS = [
    {
        "trigger_type": "attention_shift",
        "priority_threshold": 0.6,
        "cooldown_seconds": 300,  # 5 minutes
        "description": "Trigger when attention state changes significantly"
    },
    {
        "trigger_type": "scheduled",
        "priority_threshold": 0.4,
        "cooldown_seconds": 3600,  # 1 hour
        "description": "Regular snapshots during work hours"
    }
]

@router.post("/setup-default-triggers/{user_id}")
async def setup_default_triggers(user_id: str):
    """Set up default automatic snapshot triggers for a user."""
    try:
        triggers_created = []

        for trigger_config in DEFAULT_TRIGGERS:
            trigger = SnapshotTrigger(
                trigger_type=trigger_config["trigger_type"],
                user_id=user_id,
                priority_threshold=trigger_config["priority_threshold"],
                cooldown_seconds=trigger_config["cooldown_seconds"]
            )

            await register_snapshot_trigger(trigger)
            triggers_created.append(trigger_config["trigger_type"])

        return {
            "message": f"Created {len(triggers_created)} default triggers for {user_id}",
            "triggers": triggers_created
        }

    except Exception as e:
        logger.error(f"Failed to setup default triggers for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup default triggers")