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

        # Update last steps (keep max 3, newest first, as dicts)
        # Only track high-signal entries
        high_signal_types = {"decision", "blocker", "task_event", "debugging", "implementation"}
        if entry.get("entry_type") in high_signal_types or entry.get("category") in high_signal_types:
            step = {
                "summary": entry["summary"][:100],
                "ts_utc": entry.get("ts_utc", datetime.now(timezone.utc).isoformat()),
                "entry_type": entry.get("entry_type", "unknown"),
                "category": entry.get("category", "unknown"),
            }
            last_steps = current.get("last_steps", [])
            last_steps.insert(0, step)  # Add to front (newest first)
            current["last_steps"] = last_steps[:3]  # Keep first 3

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
        self, entry: dict[str, Any], trajectory: Optional[dict[str, Any]]
    ) -> float:
        """Calculate deterministic boost factor for entry relevance.

        Per spec: Boost range 0.0 to 0.5 (conservative, additive)

        Boost factors:
        - 0.5 if entry.category matches trajectory stream category
        - 0.2 if tag overlap exists (if tags present)
        - 0.1 if file overlap exists (if linked_files present)
        - else 0.0
        - Cap at 0.5

        Args:
            entry: Work log entry dict
            trajectory: Current trajectory state (can be None)

        Returns:
            Boost factor (0.0 to 0.5)
        """
        if not trajectory:
            return 0.0

        boost = 0.0

        # Category match (0.5 if matches)
        stream = trajectory.get("current_stream", "")
        entry_category = entry.get("category", "")
        
        # Stream format is "Active in {category}"
        if stream and entry_category:
            if f"Active in {entry_category}" == stream or entry_category in stream:
                boost = 0.5
                return min(boost, 0.5)  # Early return since this is max

        # Tag overlap (0.2)
        try:
            import json
            entry_tags_json = entry.get("tags_json", "[]")
            if isinstance(entry_tags_json, str):
                entry_tags = set(json.loads(entry_tags_json))
            else:
                entry_tags = set(entry_tags_json or [])
            
            # Trajectory might have tags in current_goal or in last_steps
            traj_goal = trajectory.get("current_goal", {})
            traj_tags = set(traj_goal.get("tags", []))
            
            if entry_tags and traj_tags and (entry_tags & traj_tags):
                boost += 0.2
        except (json.JSONDecodeError, TypeError):
            pass

        # File overlap (0.1)
        try:
            import json
            entry_files_json = entry.get("linked_files_json")
            if entry_files_json:
                if isinstance(entry_files_json, str):
                    entry_files = json.loads(entry_files_json)
                else:
                    entry_files = entry_files_json
                
                # Extract file paths from entry
                entry_file_paths = set()
                if isinstance(entry_files, list):
                    for f in entry_files:
                        if isinstance(f, dict) and "path" in f:
                            entry_file_paths.add(f["path"])
                        elif isinstance(f, str):
                            entry_file_paths.add(f)
                
                # Check if trajectory has file references in last_steps
                last_steps = trajectory.get("last_steps", [])
                traj_file_paths = set()
                for step in last_steps:
                    if isinstance(step, dict) and "linked_files" in step:
                        step_files = step.get("linked_files", [])
                        for f in step_files:
                            if isinstance(f, dict) and "path" in f:
                                traj_file_paths.add(f["path"])
                            elif isinstance(f, str):
                                traj_file_paths.add(f)
                
                if entry_file_paths and traj_file_paths and (entry_file_paths & traj_file_paths):
                    boost += 0.1
        except (json.JSONDecodeError, TypeError):
            pass

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
