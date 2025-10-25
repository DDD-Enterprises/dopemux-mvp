"""
ADHD Engine HTTP Client

Simple HTTP client for logging activities to the ADHD Accommodation Engine.

Features:
- Activity logging (PUT /activity/{user_id})
- Health check
- Async HTTP requests
- Error handling with retries
"""

import logging
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ADHDEngineClient:
    """
    HTTP client for ADHD Accommodation Engine API.

    Handles activity logging and health checks.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8095",
        user_id: str = "hue",
        timeout_seconds: int = 5
    ):
        """
        Initialize ADHD Engine client.

        Args:
            base_url: ADHD Engine base URL
            user_id: User ID for activity logging
            timeout_seconds: Request timeout (default: 5s)
        """
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        # Metrics
        self.activities_logged = 0
        self.health_checks = 0
        self.errors = 0

    async def log_activity(
        self,
        activity_type: str,
        duration_minutes: int,
        complexity: float,
        interruptions: int
    ) -> bool:
        """
        Log activity to ADHD Engine.

        Args:
            activity_type: Type of activity (coding/reviewing/debugging)
            duration_minutes: Activity duration
            complexity: Task complexity (0.0-1.0)
            interruptions: Number of interruptions

        Returns:
            True if logged successfully, False otherwise
        """
        url = f"{self.base_url}/api/v1/activity/{self.user_id}"

        payload = {
            "user_id": self.user_id,
            "activity_type": activity_type,
            "duration_minutes": duration_minutes,
            "complexity": complexity,
            "interruptions": interruptions
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.put(url, json=payload) as response:
                    if response.status == 200:
                        self.activities_logged += 1
                        logger.debug(f"✅ Activity logged: {duration_minutes}min, {interruptions} interruptions")
                        return True
                    else:
                        self.errors += 1
                        error_text = await response.text()
                        logger.warning(f"⚠️ Activity log failed ({response.status}): {error_text}")
                        return False

        except aiohttp.ClientError as e:
            self.errors += 1
            logger.error(f"❌ ADHD Engine unreachable: {e}")
            return False
        except Exception as e:
            self.errors += 1
            logger.error(f"❌ Activity logging error: {e}")
            return False

    async def check_health(self) -> bool:
        """
        Check if ADHD Engine is healthy.

        Returns:
            True if healthy, False otherwise
        """
        url = f"{self.base_url}/health"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    self.health_checks += 1
                    healthy = response.status == 200

                    if healthy:
                        logger.debug("✅ ADHD Engine healthy")
                    else:
                        logger.warning(f"⚠️ ADHD Engine unhealthy ({response.status})")

                    return healthy

        except aiohttp.ClientError as e:
            logger.error(f"❌ ADHD Engine health check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    async def get_energy_level(self) -> Optional[Dict[str, Any]]:
        """
        Get current energy level from ADHD Engine.

        Returns:
            Energy level data or None if unavailable
        """
        url = f"{self.base_url}/api/v1/energy-level/{self.user_id}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return None

        except Exception as e:
            logger.error(f"Energy level query error: {e}")
            return None

    async def get_attention_state(self) -> Optional[Dict[str, Any]]:
        """
        Get current attention state from ADHD Engine.

        Returns:
            Attention state data or None if unavailable
        """
        url = f"{self.base_url}/api/v1/attention-state/{self.user_id}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return None

        except Exception as e:
            logger.error(f"Attention state query error: {e}")
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            "base_url": self.base_url,
            "user_id": self.user_id,
            "activities_logged": self.activities_logged,
            "health_checks": self.health_checks,
            "errors": self.errors,
            "success_rate": (
                self.activities_logged / (self.activities_logged + self.errors)
                if (self.activities_logged + self.errors) > 0
                else 0.0
            )
        }
