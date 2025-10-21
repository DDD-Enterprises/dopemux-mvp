#!/usr/bin/env python3
"""
ConPort Client for Environmental Interruption Shield

Provides ADHD-optimized ConPort integration for shield event logging:
- Progress entry creation for shield activation/deactivation
- Custom data storage for shield state tracking
- Decision logging for shield configuration changes
- System pattern logging for shield behavior patterns

ADHD Optimizations:
- Fast-fail timeout (5 seconds) to avoid blocking
- Circuit breaker for degraded mode operation
- Graceful fallback when ConPort unavailable
- Minimal cognitive load during critical operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ShieldConPortClient:
    """
    ConPort client specifically for Environmental Interruption Shield.

    Provides logging capabilities for shield events with ADHD optimizations:
    - Fast timeouts (5s) to prevent blocking
    - Circuit breaker for graceful degradation
    - Fallback to local logging when ConPort unavailable
    - Minimal API surface for shield operations
    """

    def __init__(self, workspace_id: str, bridge_url: str = "http://localhost:3016"):
        """
        Initialize ConPort client for shields.

        Args:
            workspace_id: ConPort workspace identifier
            bridge_url: Integration Bridge URL
        """
        self.workspace_id = workspace_id
        self.bridge_url = bridge_url
        self.logger = logging.getLogger(f"{__name__}.{workspace_id}")

        # Circuit breaker state
        self.failure_count = 0
        self.last_failure = None
        self.circuit_open = False
        self.circuit_open_until = None

        # Fallback storage for when ConPort is unavailable
        self.fallback_log = []

    async def log_shield_activation(
        self,
        reason: str,
        results: Dict[str, Any],
        productivity_baseline: float,
        activated_at: datetime
    ) -> bool:
        """
        Log shield activation to ConPort progress entries.

        Args:
            reason: Human-readable activation reason
            results: Shield activation results
            productivity_baseline: Baseline productivity score
            activated_at: Activation timestamp

        Returns:
            True if logged successfully, False if failed (with fallback)
        """
        summary = f"🛡️ Activated interruption shields: {reason}"
        description = {
            "type": "shield_activation",
            "reason": reason,
            "results": results,
            "productivity_baseline": productivity_baseline,
            "activated_at": activated_at.isoformat(),
            "workspace_id": self.workspace_id
        }

        # Create progress entry for active shield state
        progress_data = {
            "workspace_id": self.workspace_id,
            "status": "IN_PROGRESS",
            "description": summary,
            "tags": ["interruption_shield", "activation", "active"],
            "parent_id": None,
            "linked_item_type": None,
            "linked_item_id": None,
            "link_relationship_type": None
        }

        return await self._call_conport_api("POST", "/progress", progress_data, summary)

    async def log_shield_deactivation(
        self,
        progress_id: str,
        reason: str,
        results: Dict[str, Any],
        deactivated_at: datetime
    ) -> bool:
        """
        Update shield progress entry for deactivation.

        Args:
            progress_id: ID of the activation progress entry to update
            reason: Human-readable deactivation reason
            results: Shield deactivation results
            deactivated_at: Deactivation timestamp

        Returns:
            True if logged successfully, False if failed
        """
        summary = f"🛡️ Deactivated interruption shields: {reason}"
        update_data = {
            "status": "DONE",
            "description": summary,
            "tags": ["interruption_shield", "deactivation", "completed"]
        }

        return await self._call_conport_api("PUT", f"/progress/{progress_id}", update_data, summary)

    async def log_shield_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Log custom shield events to ConPort custom data.

        Args:
            event_type: Type of shield event (e.g., 'false_positive', 'error')
            details: Event details

        Returns:
            True if logged successfully, False if failed
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "workspace_id": self.workspace_id,
            **details
        }

        custom_data = {
            "workspace_id": self.workspace_id,
            "category": "interruption_shield_events",
            "key": f"{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": event_data
        }

        summary = f"🛡️ Shield event: {event_type}"
        return await self._call_conport_api("POST", "/custom-data", custom_data, summary)

    async def store_shield_state(
        self,
        state: Dict[str, Any]
    ) -> bool:
        """
        Store current shield state in ConPort custom data.

        Args:
            state: Current shield state dictionary

        Returns:
            True if stored successfully, False if failed
        """
        state_data = {
            "workspace_id": self.workspace_id,
            "category": "interruption_shield_state",
            "key": "current_state",
            "value": {
                "timestamp": datetime.now().isoformat(),
                "workspace_id": self.workspace_id,
                **state
            }
        }

        summary = "🛡️ Shield state updated"
        return await self._call_conport_api("POST", "/custom-data", state_data, summary)

    async def _call_conport_api(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any],
        operation_summary: str
    ) -> bool:
        """
        Call ConPort API with circuit breaker and fallback logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            operation_summary: Human-readable operation description

        Returns:
            True if successful, False if failed (with fallback logging)
        """
        # Check circuit breaker
        if self._is_circuit_open():
            self.logger.warning(f"🛡️ Circuit breaker open, falling back for: {operation_summary}")
            self._fallback_log(operation_summary, data)
            return False

        try:
            import httpx

            # Fast timeout for ADHD optimization
            timeout = httpx.Timeout(5.0, connect=2.0)  # 5s total, 2s connect

            async with httpx.AsyncClient(timeout=timeout) as client:
                url = f"{self.bridge_url}{endpoint}"

                # Convert data to JSON
                json_data = json.dumps(data)

                response = await client.request(
                    method,
                    url,
                    content=json_data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code in [200, 201, 204]:
                    self._reset_circuit_breaker()
                    self.logger.debug(f"✅ ConPort logged: {operation_summary}")
                    return True
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            self.logger.warning(f"⚠️ ConPort API failed ({operation_summary}): {e}")
            self._record_failure()
            self._fallback_log(operation_summary, data)
            return False

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is currently open."""
        if not self.circuit_open:
            return False

        # Allow half-open test after 30 seconds
        if self.circuit_open_until and datetime.now() > self.circuit_open_until:
            self.circuit_open = False
            self.circuit_open_until = None
            self.logger.info("🛡️ Circuit breaker entering half-open state")
            return False

        return True

    def _record_failure(self):
        """Record a failure and potentially open circuit breaker."""
        self.failure_count += 1
        self.last_failure = datetime.now()

        # Open circuit breaker after 3 failures
        if self.failure_count >= 3:
            self.circuit_open = True
            self.circuit_open_until = datetime.now() + timedelta(seconds=30)
            self.logger.warning("🛡️ Circuit breaker opened due to repeated failures")

    def _reset_circuit_breaker(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.last_failure = None
        if self.circuit_open:
            self.circuit_open = False
            self.circuit_open_until = None
            self.logger.info("🛡️ Circuit breaker reset after successful call")

    def _fallback_log(self, operation: str, data: Dict[str, Any]):
        """Log to fallback storage when ConPort is unavailable."""
        fallback_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "data": data,
            "workspace_id": self.workspace_id
        }

        self.fallback_log.append(fallback_entry)

        # Keep only last 100 entries
        if len(self.fallback_log) > 100:
            self.fallback_log = self.fallback_log[-100:]

        self.logger.debug(f"📝 Fallback logged: {operation}")

    def get_fallback_log(self) -> List[Dict[str, Any]]:
        """Get fallback log entries for later sync."""
        return self.fallback_log.copy()

    def clear_fallback_log(self):
        """Clear fallback log after successful sync."""
        self.fallback_log.clear()


# Global client instance for shield coordinator
_shield_conport_client = None

def get_shield_conport_client(workspace_id: str) -> ShieldConPortClient:
    """
    Get or create global shield ConPort client instance.

    Args:
        workspace_id: ConPort workspace identifier

    Returns:
        ShieldConPortClient instance
    """
    global _shield_conport_client

    if _shield_conport_client is None or _shield_conport_client.workspace_id != workspace_id:
        _shield_conport_client = ShieldConPortClient(workspace_id)

    return _shield_conport_client