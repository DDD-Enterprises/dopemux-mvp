"""
TrajectoryManager - Trajectory state management and boost factor calculation.

Per docs/spec/dope-memory/v1/08_phased_roadmap.md Phase 2:
- Maintain trajectory_state per workspace+instance
- Track current_stream, current_goal, last_steps
- Deterministic boost factor (0.0-0.5 range)

Boost is conservative and additive to existing ranking.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional


class TrajectoryManager:
    """Manages trajectory state and boost factor calculation."""

    def __init__(self, chronicle_store):
        """Initialize with a ChronicleStore instance."""
        self.store = chronicle_store

    def update_trajectory(
        self,
        workspace_id: str,
        instance_id: str,
        entry: dict[str, Any],
    ) -> dict[str, Any]:
        """Update trajectory state with a new entry.

        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            entry: Work log entry dict

        Returns:
            Updated trajectory state dict
        """
        # Get current trajectory
        current = self.store.get_trajectory_state(workspace_id, instance_id)

        if not current:
            current = {
                "workspace_id": workspace_id,
                "instance_id": instance_id,
                "session_id": entry.get("session_id"),
                "current_stream": "",
                "current_goal": {},
                "last_steps": [],
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            }

        # Update stream (based on category or tags)
        stream = self._extract_stream(entry)
        if stream:
            current["current_stream"] = stream

        # Update last steps (keep max 3, newest last)
        last_steps = current.get("last_steps", [])
        last_steps.append(entry["summary"][:100])
        current["last_steps"] = last_steps[-3:]  # Keep last 3

        # Update session_id if present
        if entry.get("session_id"):
            current["session_id"] = entry["session_id"]

        # Update timestamp
        current["updated_at_utc"] = datetime.now(timezone.utc).isoformat()

        # Persist
        self.store.upsert_trajectory_state(workspace_id, instance_id, current)

        return current

    def get_trajectory(
        self, workspace_id: str, instance_id: str
    ) -> Optional[dict[str, Any]]:
        """Get current trajectory state.

        Returns:
            Trajectory state dict or None
        """
        return self.store.get_trajectory_state(workspace_id, instance_id)

    def get_boost_factor(
        self, entry: dict[str, Any], trajectory: dict[str, Any]
    ) -> float:
        """Calculate deterministic boost factor for entry relevance.

        Boost range: 0.0 to 0.5 (conservative, additive)

        Boost factors:
        - Stream match: +0.2
        - Tag overlap: +0.1
        - Same session + recent: +0.2

        Args:
            entry: Work log entry dict
            trajectory: Current trajectory state

        Returns:
            Boost factor (0.0 to 0.5)
        """
        boost = 0.0

        # Stream match
        stream = trajectory.get("current_stream", "")
        if stream and (
            stream in entry.get("category", "")
            or stream in str(entry.get("tags", []))
        ):
            boost += 0.2

        # Tag overlap
        traj_tags = set(trajectory.get("current_goal", {}).get("tags", []))
        entry_tags = set(entry.get("tags", []))
        if traj_tags and entry_tags and traj_tags & entry_tags:
            boost += 0.1

        # Same session + recent (within last hour)
        traj_session = trajectory.get("session_id")
        entry_session = entry.get("session_id")
        if traj_session and traj_session == entry_session:
            updated_at = datetime.fromisoformat(trajectory["updated_at_utc"])
            now_utc = datetime.now(timezone.utc)
            hours_since = (now_utc - updated_at).total_seconds() / 3600
            if hours_since <= 1.0:
                boost += 0.2

        return min(boost, 0.5)  # Cap at 0.5

    def _extract_stream(self, entry: dict[str, Any]) -> str:
        """Extract stream keyword from entry.

        Returns formatted stream in "Active in {category}" format.
        """
        category = entry.get("category", "")
        if category:
            return f"Active in {category}"

        tags = entry.get("tags", [])
        if tags:
            return f"Active in {tags[0]}"

        return "idle"
