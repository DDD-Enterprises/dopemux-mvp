"""
Lane-based capture policy enforcement.

Implements opt-in policy for tmux lane capture with audit logging.
Default: ALL lanes DISABLED (explicit opt-in required).
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


class LanePolicy:
    """
    Lane-based capture policy with opt-in enforcement.

    Reads configuration from .dopemux/config.yaml and enforces:
    - Per-lane enable/disable
    - Per-lane event type allowlists
    - Audit logging for all policy decisions
    """

    def __init__(self, repo_root: Path, audit_log_path: Optional[Path] = None):
        """
        Initialize lane policy.

        Args:
            repo_root: Project repository root
            audit_log_path: Path to audit log (default: .dopemux/capture_audit.log)
        """
        self.repo_root = repo_root
        self.config_path = repo_root / ".dopemux" / "config.yaml"
        self.audit_log_path = audit_log_path or (repo_root / ".dopemux" / "capture_audit.log")
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .dopemux/config.yaml"""
        if not self.config_path.exists() or yaml is None:
            return {}

        try:
            raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
            return raw.get("capture", {})
        except Exception as e:
            logger.warning(f"Failed to load capture config: {e}")
            return {}

    def should_capture(
        self,
        lane: Optional[str],
        event_type: str,
    ) -> bool:
        """
        Determine if capture should proceed for this lane + event type.

        Args:
            lane: Lane identifier (e.g., "agent:primary", "orchestrator:control")
            event_type: Event type (e.g., "file.written", "task.completed")

        Returns:
            True if capture should proceed, False otherwise
        """
        # No lane identity = fail closed (security)
        if not lane:
            self._audit_log("SKIP", lane="unknown", event_type=event_type, reason="no_lane_identity")
            return False

        # Get lane configuration
        lanes_config = self._config.get("lanes", {})
        lane_config = lanes_config.get(lane, {})

        # Default: disabled (opt-in policy)
        if not lane_config.get("enabled", False):
            self._audit_log("SKIP", lane=lane, event_type=event_type, reason="lane_disabled")
            return False

        # Check event type allowlist
        allowed_types = lane_config.get("event_types", [])
        if allowed_types and event_type not in allowed_types:
            self._audit_log(
                "SKIP",
                lane=lane,
                event_type=event_type,
                reason="event_type_not_in_allowlist"
            )
            return False

        # Capture allowed
        self._audit_log("ALLOW", lane=lane, event_type=event_type)
        return True

    def _audit_log(
        self,
        action: str,
        lane: str = "unknown",
        event_type: str = "",
        reason: str = "",
        **kwargs
    ):
        """
        Write audit log entry.

        Format: TIMESTAMP | ACTION | lane=X | type=Y | reason=Z
        """
        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Build log entry
        timestamp = datetime.now(timezone.utc).isoformat()
        parts = [timestamp, action, f"lane={lane}"]

        if event_type:
            parts.append(f"type={event_type}")
        if reason:
            parts.append(f"reason={reason}")

        for key, value in kwargs.items():
            parts.append(f"{key}={value}")

        log_line = " | ".join(parts) + "\n"

        # Write to audit log
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def get_enabled_lanes(self) -> List[str]:
        """Get list of lanes that have capture enabled."""
        lanes_config = self._config.get("lanes", {})
        return [
            lane for lane, config in lanes_config.items()
            if isinstance(config, dict) and config.get("enabled", False)
        ]

    def is_lane_enabled(self, lane: str) -> bool:
        """Check if a specific lane has capture enabled."""
        lanes_config = self._config.get("lanes", {})
        lane_config = lanes_config.get(lane, {})
        return lane_config.get("enabled", False)


def get_current_lane() -> Optional[str]:
    """
    Detect current tmux lane from environment.

    Returns lane identifier like "agent:primary" or None if not in tmux.
    """
    # Check TMUX_PANE environment variable
    tmux_pane = os.getenv("TMUX_PANE")
    if not tmux_pane:
        return None

    # Check for DOPEMUX_LANE override
    dopemux_lane = os.getenv("DOPEMUX_LANE")
    if dopemux_lane:
        return dopemux_lane

    # Try to detect from pane title or window name
    # This would require tmux integration - for now return None
    return None
