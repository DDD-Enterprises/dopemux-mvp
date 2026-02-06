#!/usr/bin/env python3
"""
Git Commit Event Emitter

Publishes code.committed events to Redis Streams for ADHD activity tracking.
Called by post-commit git hook.

ADHD Benefit: Commits = completed work, high-productivity signal
"""

import logging

import asyncio
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add DopeconBridge to path
bridge_path = Path(__file__).parent.parent / "services" / "mcp-dopecon-bridge"
sys.path.insert(0, str(bridge_path))

from event_bus import Event, EventBus


async def emit_commit_event(
    commit_hash: str,
    files_changed: int,
    lines_added: int,
    lines_removed: int,
    workspace: str,
    commit_message: str
):
    """
    Emit code.committed event to Redis Streams.

    Args:
        commit_hash: Git commit SHA
        files_changed: Number of files changed
        lines_added: Lines added in commit
        lines_removed: Lines removed in commit
        workspace: Workspace path
        commit_message: First line of commit message
    """
    try:
        # Calculate complexity from commit size
        total_changes = lines_added + lines_removed
        complexity = min(total_changes / 100.0, 1.0)  # Cap at 1.0

        # Connect to Redis
        event_bus = EventBus(redis_url="redis://localhost:6379")
        await event_bus.initialize()

        # Create event
        import time
        event = Event(
            type="code.committed",
            data={
                "commit_hash": commit_hash[:8],  # Short hash
                "commit_message": commit_message[:100],  # First 100 chars
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "total_changes": total_changes,
                "complexity": complexity,
                "workspace": workspace,
                "timestamp": f"{time.time()}",
                "activity_signal": "high_productivity"  # Commits = completed work!
            },
            source="git-hook"
        )

        # Publish event
        msg_id = await event_bus.publish("dopemux:events", event)

        if msg_id:
            # Success (silent, don't slow down git)
            pass
        else:
            # Failed (also silent, don't block git)
            pass

        await event_bus.close()

    except Exception as e:
        # Silently fail - don't break git commits
        pass


        logger.error(f"Error: {e}")
if __name__ == "__main__":
    if len(sys.argv) < 7:
        sys.exit(0)  # Missing args, exit silently

    commit_hash = sys.argv[1]
    files_changed = int(sys.argv[2])
    lines_added = int(sys.argv[3])
    lines_removed = int(sys.argv[4])
    workspace = sys.argv[5]
    commit_message = sys.argv[6] if len(sys.argv) > 6 else ""

    # Run async event emission
    asyncio.run(emit_commit_event(
        commit_hash,
        files_changed,
        lines_added,
        lines_removed,
        workspace,
        commit_message
    ))
