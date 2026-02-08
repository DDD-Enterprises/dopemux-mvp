"""
False Starts Aggregator - Enhancement E1

Aggregates unfinished work states from ConPort custom_data to surface
false-start patterns (detected -> acknowledged -> snoozed -> abandoned).
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FalseStartsAggregator:
    """Aggregate unfinished/untracked-work state for dashboard display."""

    UNFINISHED_STATUSES = {"detected", "acknowledged", "snoozed"}

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.category = "untracked_work"
        self.name = "False Starts Aggregator"

    async def get_false_starts_summary(self, conport_client=None) -> Dict:
        """
        Return high-level summary of untracked-work lifecycle states.

        Shape intentionally matches MCP caller expectations.
        """
        records = await self._load_records(conport_client)
        if not records:
            return self._empty_summary()

        status_breakdown: Dict[str, int] = {}
        for record in records:
            status = str(record.get("status", "detected")).lower()
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        total_unfinished = sum(
            status_breakdown.get(status, 0) for status in self.UNFINISHED_STATUSES
        )

        summary = {
            "total_items": len(records),
            "total_unfinished": total_unfinished,
            "detected": status_breakdown.get("detected", 0),
            "acknowledged": status_breakdown.get("acknowledged", 0),
            "snoozed": status_breakdown.get("snoozed", 0),
            "abandoned": status_breakdown.get("abandoned", 0),
            "converted_to_task": status_breakdown.get("converted_to_task", 0),
            "status_breakdown": status_breakdown,
        }

        top_abandoned = self._extract_top_abandoned(records, limit=5)
        if top_abandoned:
            summary["top_abandoned"] = top_abandoned

        return summary

    async def get_top_abandoned(self, conport_client=None, limit: int = 5) -> List[Dict]:
        """
        Return abandoned/aged work sorted by idle duration descending.

        Used by RevivalSuggester (E3).
        """
        records = await self._load_records(conport_client)
        if not records:
            return []
        return self._extract_top_abandoned(records, limit=max(1, int(limit)))

    def format_dashboard_message(self, summary: Dict, current_work_name: str) -> str:
        """Format ADHD-friendly dashboard message for E1 output."""
        total_unfinished = int(summary.get("total_unfinished", 0))
        abandoned = int(summary.get("abandoned", 0))
        snoozed = int(summary.get("snoozed", 0))

        if total_unfinished == 0 and abandoned == 0:
            return (
                "False-starts dashboard: clean slate. "
                f"Current work '{current_work_name}' is not competing with unfinished items."
            )

        return (
            "False-starts dashboard: "
            f"{total_unfinished} unfinished, {snoozed} snoozed, {abandoned} abandoned. "
            f"Before diving deeper into '{current_work_name}', consider closing one old thread."
        )

    def aggregate(self, data):
        """
        Backward-compatible sync API retained for older callers/tests.

        When passed a list of records, returns a condensed summary.
        """
        if not isinstance(data, list):
            return {"false_starts": 0, "status": "no_data"}

        status_breakdown: Dict[str, int] = {}
        for record in data:
            if isinstance(record, dict):
                status = str(record.get("status", "detected")).lower()
                status_breakdown[status] = status_breakdown.get(status, 0) + 1

        unfinished = sum(
            status_breakdown.get(status, 0) for status in self.UNFINISHED_STATUSES
        )
        return {
            "false_starts": unfinished,
            "status": "ok",
            "status_breakdown": status_breakdown,
        }

    async def _load_records(self, conport_client) -> List[Dict]:
        """Load untracked_work records from ConPort in a forgiving way."""
        if not conport_client:
            return []

        try:
            rows = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category=self.category,
            )
        except TypeError:
            rows = await conport_client.get_custom_data(self.workspace_id, self.category)
        except Exception as exc:
            logger.warning("Failed loading false-start records: %s", exc)
            return []

        records: List[Dict] = []
        for row in rows or []:
            if isinstance(row, dict) and "value" in row and isinstance(row["value"], dict):
                records.append(row["value"])
            elif isinstance(row, dict):
                records.append(row)
        return records

    def _extract_top_abandoned(self, records: List[Dict], limit: int) -> List[Dict]:
        """Extract revival-ready abandoned items from untracked_work records."""
        candidates: List[Dict] = []

        for record in records:
            status = str(record.get("status", "detected")).lower()
            # Revival can use explicit abandoned items plus stale unfinished items.
            if status == "converted_to_task":
                continue

            git_summary = record.get("git_summary", {}) or {}
            files = git_summary.get("files", []) or []
            if not files:
                continue

            detected_at = self._parse_datetime(record.get("detected_at"))
            first_change = self._parse_datetime(git_summary.get("first_change_time"))
            reference_time = first_change or detected_at
            days_idle = 0
            if reference_time is not None:
                now = (
                    datetime.now(reference_time.tzinfo)
                    if reference_time.tzinfo is not None
                    else datetime.now()
                )
                days_idle = max(0, (now - reference_time).days)

            # Only include stale work in revival pool.
            if status != "abandoned" and days_idle < 3:
                continue

            candidates.append(
                {
                    "name": record.get("auto_generated_name", "Untracked work"),
                    "status": status,
                    "detected_at": record.get("detected_at"),
                    "days_idle": days_idle,
                    "files": files,
                    "branch": git_summary.get("branch"),
                }
            )

        candidates.sort(key=lambda item: item.get("days_idle", 0), reverse=True)
        return candidates[:limit]

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse ISO-ish datetimes safely (supports trailing Z)."""
        if not value or not isinstance(value, str):
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    def _empty_summary(self) -> Dict:
        return {
            "total_items": 0,
            "total_unfinished": 0,
            "detected": 0,
            "acknowledged": 0,
            "snoozed": 0,
            "abandoned": 0,
            "converted_to_task": 0,
            "status_breakdown": {},
        }
