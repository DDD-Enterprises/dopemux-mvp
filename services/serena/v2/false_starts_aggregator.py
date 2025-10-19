"""
False-Starts Dashboard Aggregator - Enhancement E1

Queries ConPort for aggregate untracked work statistics to create
awareness without shame. Shows total unfinished projects with breakdown
by status (acknowledged, snoozed, abandoned).

Part of F001 Enhancement E1: False-Starts Dashboard
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class FalseStartsAggregator:
    """
    Aggregate statistics for unfinished work across sessions.

    Creates gentle awareness of accumulated untracked work without
    judgment or shame. ADHD-optimized with progressive disclosure.
    """

    def __init__(self, workspace_id: str):
        """
        Initialize false-starts aggregator.

        Args:
            workspace_id: Workspace ID for ConPort queries
        """
        self.workspace_id = workspace_id

    async def get_false_starts_summary(
        self,
        conport_client=None
    ) -> Dict[str, Any]:
        """
        Get aggregate unfinished work statistics.

        Args:
            conport_client: Optional ConPort MCP client for queries

        Returns:
            {
                "total_unfinished": int,
                "acknowledged": int,
                "snoozed": int,
                "abandoned": int,
                "converted_to_tasks": int,
                "oldest_date": str | None,
                "newest_date": str | None,
                "top_abandoned": [
                    {
                        "name": str,
                        "detected_at": str,
                        "files": List[str],
                        "days_idle": int
                    }
                ],
                "status_breakdown": Dict[str, int]
            }
        """
        try:
            if not conport_client:
                logger.warning("No ConPort client - returning empty summary")
                return self._empty_summary()

            # Query all untracked work from ConPort
            untracked_data = await self._query_untracked_work(conport_client)

            # Calculate statistics
            stats = self._calculate_statistics(untracked_data)

            # Identify top abandoned for revival feature (E3)
            stats["top_abandoned"] = self._identify_top_abandoned(
                untracked_data, limit=5
            )

            logger.info(
                f"📊 False-starts summary: {stats['total_unfinished']} total, "
                f"{stats['abandoned']} abandoned"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get false-starts summary: {e}")
            return self._empty_summary()

    async def _query_untracked_work(self, conport_client) -> List[Dict]:
        """Query all untracked work from ConPort custom_data."""
        try:
            # Query ConPort custom_data category="untracked_work"
            result = await conport_client.get_custom_data(
                workspace_id=self.workspace_id,
                category="untracked_work"
            )

            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "items" in result:
                return result["items"]
            else:
                logger.warning(f"Unexpected ConPort response format: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Failed to query untracked work: {e}")
            return []

    def _calculate_statistics(self, untracked_data: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate statistics from untracked work data."""
        stats = {
            "total_unfinished": 0,
            "acknowledged": 0,
            "snoozed": 0,
            "abandoned": 0,
            "converted_to_tasks": 0,
            "oldest_date": None,
            "newest_date": None,
            "status_breakdown": {}
        }

        oldest_timestamp = None
        newest_timestamp = None

        for work_entry in untracked_data:
            # Extract value (actual data)
            data = work_entry.get("value", {})
            status = data.get("status", "detected")
            detected_at = data.get("detected_at")

            # Count by status
            stats["status_breakdown"][status] = stats["status_breakdown"].get(status, 0) + 1

            # Categorize
            if status == "converted_to_task":
                stats["converted_to_tasks"] += 1
            else:
                stats["total_unfinished"] += 1

                if status == "acknowledged":
                    stats["acknowledged"] += 1
                elif status == "snoozed":
                    stats["snoozed"] += 1
                elif status == "abandoned":
                    stats["abandoned"] += 1

            # Track date range
            if detected_at:
                try:
                    timestamp = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
                    if oldest_timestamp is None or timestamp < oldest_timestamp:
                        oldest_timestamp = timestamp
                    if newest_timestamp is None or timestamp > newest_timestamp:
                        newest_timestamp = timestamp
                except Exception as e:
                    logger.debug(f"Failed to parse timestamp {detected_at}: {e}")

        # Format dates
        if oldest_timestamp:
            stats["oldest_date"] = oldest_timestamp.isoformat()
        if newest_timestamp:
            stats["newest_date"] = newest_timestamp.isoformat()

        return stats

    def _identify_top_abandoned(
        self,
        untracked_data: List[Dict],
        limit: int = 5
    ) -> List[Dict]:
        """
        Identify top abandoned work for revival suggestions (E3).

        Sorted by recency (most recent first) for revival prompting.
        """
        abandoned_items = []

        for work_entry in untracked_data:
            data = work_entry.get("value", {})
            status = data.get("status", "detected")

            if status == "abandoned":
                detected_at = data.get("detected_at")

                # Calculate days idle
                days_idle = 0
                if detected_at:
                    try:
                        detected_timestamp = datetime.fromisoformat(
                            detected_at.replace('Z', '+00:00')
                        )
                        days_idle = (datetime.now(timezone.utc) - detected_timestamp).days
                    except Exception:
                        pass

                # Extract file list from detection signals
                files = []
                signals = data.get("detection_signals", {})
                if "git_uncommitted_files" in signals:
                    files = signals["git_uncommitted_files"]

                abandoned_items.append({
                    "name": data.get("auto_generated_name", "Unknown work"),
                    "detected_at": detected_at,
                    "files": files,
                    "days_idle": days_idle,
                    "branch": data.get("branch_name"),
                    "file_count": len(files)
                })

        # Sort by recency (newest first for revival relevance)
        abandoned_items.sort(
            key=lambda x: x["detected_at"] if x["detected_at"] else "",
            reverse=True
        )

        return abandoned_items[:limit]

    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure."""
        return {
            "total_unfinished": 0,
            "acknowledged": 0,
            "snoozed": 0,
            "abandoned": 0,
            "converted_to_tasks": 0,
            "oldest_date": None,
            "newest_date": None,
            "top_abandoned": [],
            "status_breakdown": {}
        }

    def format_dashboard_message(
        self,
        stats: Dict[str, Any],
        new_work_name: str
    ) -> str:
        """
        Format the gentle "Sure you want to make it 48?" message.

        ADHD-optimized: factual, non-judgmental, actionable.

        Args:
            stats: Statistics from get_false_starts_summary
            new_work_name: Name of newly detected work

        Returns:
            Formatted dashboard message string
        """
        total = stats["total_unfinished"]

        # Header
        lines = ["📊 UNFINISHED WORK SUMMARY"]
        lines.append("─" * 45)

        # Gentle messaging based on severity
        if total == 0:
            lines.append("✨ Clean slate! No unfinished projects right now.")
            lines.append("")
            lines.append(f"New work detected: '{new_work_name}'")
            return "\n".join(lines)

        # Show total
        lines.append(f"Total unfinished projects: {total}")
        lines.append("")

        # Status breakdown
        if stats["acknowledged"] or stats["snoozed"] or stats["abandoned"]:
            lines.append("Status breakdown:")
            if stats["acknowledged"]:
                lines.append(f"  🔄 Acknowledged (still working): {stats['acknowledged']}")
            if stats["snoozed"]:
                lines.append(f"  ⏸️  Snoozed: {stats['snoozed']}")
            if stats["abandoned"]:
                lines.append(f"  🗑️  Abandoned: {stats['abandoned']}")
            lines.append("")

        # New detection
        lines.append(f"New untracked work detected:")
        lines.append(f"  ⚠️  '{new_work_name}'")
        lines.append("")

        # Gentle reality check (progressive based on count)
        if total <= 5:
            lines.append(f"❓ Track this one properly?")
        elif total <= 20:
            lines.append(f"❓ Sure you want to add another? ({total} → {total + 1})")
        else:
            lines.append(f"❓ Sure you want to make it {total + 1}?")
            lines.append("")
            lines.append("💡 Maybe finish one first? Or is this truly urgent?")

        return "\n".join(lines)
