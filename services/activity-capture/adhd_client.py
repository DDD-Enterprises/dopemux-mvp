"""
ADHD Engine Client for Activity Capture

Handles communication with the ADHD Accommodation Engine API.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

def _configure_import_paths() -> Path:
    current = Path(__file__).resolve()
    candidates = [current.parent, *current.parents]
    repo_root = next(
        (
            candidate for candidate in candidates
            if (candidate / "services" / "shared").exists() or (candidate / "src" / "dopemux").exists()
        ),
        current.parent,
    )
    for path in (repo_root, repo_root / "src"):
        path_str = str(path)
        if path.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)
    return repo_root


REPO_ROOT = _configure_import_paths()

from services.shared.brand_voice import StatusChip, brand_log
from typing import Dict, Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


ACTIVITY_PAYLOAD_KEYS = (
    "completion_rate",
    "context_switches",
    "break_compliance",
    "minutes_since_break",
)


def build_activity_payload(user_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the content-free payload accepted by the ADHD Engine activity endpoint."""
    payload = {"user_id": user_id}
    payload.update({key: activity_data.get(key) for key in ACTIVITY_PAYLOAD_KEYS})
    return payload


class ADHDEngineClient:
    """
    Client for communicating with ADHD Accommodation Engine.

    Sends activity data and receives accommodation recommendations.
    """

    def __init__(self, base_url: str, user_id: str, api_key: Optional[str] = None):
        """
        Initialize ADHD Engine client.

        Args:
            base_url: ADHD Engine API base URL
            user_id: User identifier for activity tracking
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.api_key = api_key

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key

    async def initialize(self):
        """Initialize HTTP session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    async def check_health(self) -> bool:
        """Check if ADHD Engine is healthy."""
        try:
            if self.session is None:
                await self.initialize()
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(brand_log(f"Health check failed: {e}", chip=StatusChip.BLOCKER))
            return False

    async def send_activity_data(self, activity_data: Dict[str, Any]):
        """
        Send activity data to ADHD Engine.

        Args:
            activity_data: Activity data to send
        """
        try:
            if self.session is None:
                await self.initialize()

            payload = build_activity_payload(self.user_id, activity_data)

            async with self.session.put(
                f"{self.base_url}/api/v1/activity/{self.user_id}",
                json=payload
            ) as response:
                if response.status == 200:
                    logger.debug("Activity data sent successfully")
                else:
                    logger.warning(brand_log(f"Failed to send activity data: {response.status}", chip=StatusChip.AFTERCARE))

        except Exception as e:
            logger.error(brand_log(f"Error sending activity data: {e}", chip=StatusChip.BLOCKER))

    async def get_accommodation_recommendations(self) -> Dict[str, Any]:
        """
        Get current accommodation recommendations from ADHD Engine.

        Returns:
            Dict with accommodation recommendations
        """
        try:
            if self.session is None:
                await self.initialize()
            async with self.session.get(
                f"{self.base_url}/api/v1/recommend-break?user_id={self.user_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(brand_log(f"Failed to get recommendations: {response.status}", chip=StatusChip.AFTERCARE))
                    return {}

        except Exception as e:
            logger.error(brand_log(f"Error getting recommendations: {e}", chip=StatusChip.BLOCKER))
            return {}
