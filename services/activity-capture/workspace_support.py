#!/usr/bin/env python3
"""
Activity Capture Multi-Workspace Support

Enhances activity events with workspace metadata.
This is a simple metadata addition - just tag events with workspace.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Add shared utilities
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))

from shared.workspace_utils import resolve_workspaces


def enrich_event_with_workspace(
    event: Dict[str, Any],
    workspace_path: Optional[str] = None,
    auto_detect: bool = True,
) -> Dict[str, Any]:
    """
    Add workspace metadata to activity event.
    
    Args:
        event: Original event dict
        workspace_path: Explicit workspace path
        auto_detect: Auto-detect workspace from cwd if no path given
        
    Returns:
        Event with workspace metadata added
    """
    # Resolve workspace
    workspaces = resolve_workspaces(
        workspace_path=workspace_path,
        env_var_name="ACTIVITY_CAPTURE_WORKSPACE",
        fallback_to_current=auto_detect,
    )
    
    if workspaces:
        workspace = workspaces[0]  # Use first workspace
        event["workspace"] = {
            "path": str(workspace),
            "name": workspace.name,
        }
    
    return event


def create_workspace_aware_event(
    event_type: str,
    data: Dict[str, Any],
    workspace_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create activity event with workspace context.
    
    Args:
        event_type: Type of event (e.g., 'file.modified', 'task.completed')
        data: Event data
        workspace_path: Optional workspace path
        
    Returns:
        Complete event dict with workspace context
    """
    event = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }
    
    return enrich_event_with_workspace(event, workspace_path)


# Export functions
__all__ = [
    "enrich_event_with_workspace",
    "create_workspace_aware_event",
]
