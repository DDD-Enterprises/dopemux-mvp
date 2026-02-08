"""
ADHD Engine Client for Activity Capture

Handles communication with the ADHD Accommodation Engine API.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


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
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    async def check_health(self) -> bool:
        """Check if ADHD Engine is healthy."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def send_activity_data(self, activity_data: Dict[str, Any]):
        """
        Send activity data to ADHD Engine.

        Args:
            activity_data: Activity data to send
        """
        try:
            payload = {
                "user_id": self.user_id,
                "activity_data": activity_data,
                "timestamp": activity_data.get("timestamp", asyncio.get_event_loop().time())
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/activity/{self.user_id}",
                json=payload
            ) as response:
                if response.status == 200:
                    logger.debug("Activity data sent successfully")
                else:
                    logger.warning(f"Failed to send activity data: {response.status}")

        except Exception as e:
            logger.error(f"Error sending activity data: {e}")

    async def get_accommodation_recommendations(self) -> Dict[str, Any]:
        """
        Get current accommodation recommendations from ADHD Engine.

        Returns:
            Dict with accommodation recommendations
        """
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/recommend-break?user_id={self.user_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to get recommendations: {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return {}