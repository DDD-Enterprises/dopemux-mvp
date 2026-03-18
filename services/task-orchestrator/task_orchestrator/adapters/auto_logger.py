"""Auto-logs significant orchestrator events to ConPort knowledge graph.

All methods are fire-and-forget with graceful degradation - if ConPort is
unavailable, events are silently dropped (local session state is primary).
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


class ConPortAutoLogger:
    """Automatically logs orchestrator events to ConPort."""

    def __init__(
        self,
        conport_url: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        self.conport_url = conport_url or os.environ.get(
            "CONPORT_URL", "http://localhost:3004"
        )
        self.workspace_id = workspace_id or os.environ.get(
            "WORKSPACE_ID",
            os.environ.get("DOPEMUX_WORKSPACE_ROOT", os.getcwd()),
        )

    def _post(self, endpoint: str, payload: Dict[str, Any], timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        """HTTP POST helper using stdlib only."""
        try:
            url = f"{self.conport_url}{endpoint}"
            data = json.dumps(payload).encode("utf-8")
            req = urllib_request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                return json.loads(body.decode("utf-8")) if body else None
        except (HTTPError, URLError, TimeoutError, ConnectionRefusedError, OSError) as e:
            logger.debug(f"ConPort unavailable ({endpoint}): {e}")
            return None

    async def log_session_start(self, session_data: Dict[str, Any]) -> None:
        """Log session start as progress_entry."""
        self._post(
            "/api/progress",
            {
                "workspace_id": self.workspace_id,
                "status": "IN_PROGRESS",
                "description": f"Session started: {session_data.get('task', 'General work')}",
                "tags": [
                    "session",
                    "orchestrator",
                    f"energy:{session_data.get('energy_level', 'medium')}",
                ],
            },
        )

    async def log_session_end(
        self, session_data: Dict[str, Any], metrics: Dict[str, Any]
    ) -> None:
        """Log session completion with metrics."""
        duration = metrics.get("duration_minutes", 0)
        outcome = metrics.get("outcome", "completed")
        self._post(
            "/api/progress",
            {
                "workspace_id": self.workspace_id,
                "status": "DONE",
                "description": (
                    f"Session {outcome}: {session_data.get('task', 'General work')} "
                    f"({duration}m, files: {metrics.get('files_edited', 0)})"
                ),
                "tags": ["session", "orchestrator", outcome],
            },
        )

    async def log_context_switch(self, from_task: str, to_task: str) -> None:
        """Log context switch as a system pattern."""
        self._post(
            "/api/patterns",
            {
                "workspace_id": self.workspace_id,
                "name": f"Context Switch: {from_task[:30]} -> {to_task[:30]}",
                "description": (
                    f"Switched from '{from_task}' to '{to_task}' "
                    f"at {datetime.now(timezone.utc).isoformat()}"
                ),
                "tags": ["context-switch", "adhd", "orchestrator"],
            },
        )

    async def log_decomposition(
        self, parent: str, subtask_count: int, total_minutes: int
    ) -> None:
        """Log task decomposition as decision."""
        self._post(
            "/api/decisions",
            {
                "workspace_id": self.workspace_id,
                "summary": f"Decomposed '{parent}' into {subtask_count} subtasks (~{total_minutes}m)",
                "rationale": "ADHD-optimized task decomposition for cognitive load management",
                "tags": ["decomposition", "adhd", "orchestrator"],
            },
        )

    async def log_decision_to_conport(
        self, summary: str, rationale: str, tags: List[str]
    ) -> None:
        """Log an explicit decision."""
        all_tags = list(set(tags + ["orchestrator"]))
        self._post(
            "/api/decisions",
            {
                "workspace_id": self.workspace_id,
                "summary": summary,
                "rationale": rationale,
                "tags": all_tags,
            },
        )


# Global singleton
auto_logger = ConPortAutoLogger()
