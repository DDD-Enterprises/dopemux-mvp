#!/usr/bin/env python3
"""
ShieldCoordinator - Core Logic for Environmental Interruption Shield

Coordinates parallel activation of multiple environmental shields:
- Do Not Disturb (DND) mode
- Slack status updates
- Notification filtering
- False positive detection via productivity monitoring

ADHD Optimization:
- Parallel shield activation (no sequential blocking)
- 15-minute productivity monitoring for false positives
- Graceful degradation when shields unavailable
- Comprehensive logging to ConPort for debugging
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from .shields import DNDShield, SlackShield, NotificationShield
from .monitor import ProductivityMonitor
from .conport_client import get_shield_conport_client

logger = logging.getLogger(__name__)

@dataclass
class ShieldState:
    """Current state of all environmental shields"""
    dnd_active: bool = False
    slack_active: bool = False
    notifications_active: bool = False
    activated_at: Optional[datetime] = None
    productivity_baseline: float = 0.0
    false_positive_detected: bool = False

@dataclass
class ShieldConfig:
    """Configuration for shield coordinator"""
    enable_dnd: bool = True
    enable_slack: bool = True
    enable_notifications: bool = True
    productivity_threshold: float = 0.7  # Minimum productivity to avoid false positive
    monitoring_window_minutes: int = 15
    max_activation_attempts: int = 3
    activation_timeout_seconds: int = 30
    conport_workspace_id: Optional[str] = None

class ShieldCoordinator:
    """
    Core coordinator for environmental interruption shields.

    Manages parallel activation/deactivation of multiple shield types
    with productivity monitoring to prevent false positives.
    """

    def __init__(self, config: ShieldConfig):
        self.config = config
        self.state = ShieldState()

        # Initialize shield instances
        self.shields = {
            'dnd': DNDShield() if config.enable_dnd else None,
            'slack': SlackShield() if config.enable_slack else None,
            'notifications': NotificationShield() if config.enable_notifications else None,
        }

        # Initialize productivity monitor
        self.monitor = ProductivityMonitor(
            window_minutes=config.monitoring_window_minutes,
            threshold=config.productivity_threshold
        )

        # Initialize ConPort client if configured
        self.conport_client = None
        if config.conport_workspace_id:
            self.conport_client = get_shield_conport_client(config.conport_workspace_id)

        # Track active progress entry ID for shield state
        self.active_progress_id = None

        # Callbacks for state changes
        self._state_change_callbacks: List[Callable[[ShieldState], None]] = []

    async def activate_shields(self, reason: str = "Focused work session") -> Dict[str, Any]:
        """
        Activate all configured shields in parallel.

        Args:
            reason: Human-readable reason for activation

        Returns:
            Dict with activation results and any errors
        """
        logger.info(f"🛡️ Activating interruption shields: {reason}")

        # Establish productivity baseline
        self.state.productivity_baseline = await self.monitor.get_current_productivity()

        # Parallel shield activation
        activation_tasks = []
        shield_names = []

        for name, shield in self.shields.items():
            if shield is not None:
                task = asyncio.create_task(
                    self._activate_single_shield(name, shield, reason)
                )
                activation_tasks.append(task)
                shield_names.append(name)

        # Wait for all activations with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*activation_tasks, return_exceptions=True),
                timeout=self.config.activation_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error("🛡️ Shield activation timed out")
            return {
                "success": False,
                "error": "Activation timeout",
                "results": {}
            }

        # Process results
        activation_results = {}
        all_successful = True

        for name, result in zip(shield_names, results):
            if isinstance(result, Exception):
                logger.error(f"🛡️ Shield {name} failed: {result}")
                activation_results[name] = {"success": False, "error": str(result)}
                all_successful = False
            else:
                activation_results[name] = result
                if result.get("success", False):
                    # Update state
                    if name == "dnd":
                        self.state.dnd_active = True
                    elif name == "slack":
                        self.state.slack_active = True
                    elif name == "notifications":
                        self.state.notifications_active = True
                else:
                    all_successful = False

        # Update activation timestamp
        if any([self.state.dnd_active, self.state.slack_active, self.state.notifications_active]):
            self.state.activated_at = datetime.now()

        # Log to ConPort if configured
        if self.conport_client:
            logged = await self.conport_client.log_shield_activation(
                reason, activation_results, self.state.productivity_baseline, self.state.activated_at
            )
            if logged:
                logger.debug("✅ Shield activation logged to ConPort")
            else:
                logger.warning("⚠️ Failed to log shield activation to ConPort")

        # Store current state in ConPort
        if self.conport_client:
            state_data = {
                "dnd_active": self.state.dnd_active,
                "slack_active": self.state.slack_active,
                "notifications_active": self.state.notifications_active,
                "activated_at": self.state.activated_at.isoformat() if self.state.activated_at else None,
                "productivity_baseline": self.state.productivity_baseline,
                "false_positive_detected": self.state.false_positive_detected
            }
            await self.conport_client.store_shield_state(state_data)

        # Notify callbacks
        await self._notify_state_change()

        result = {
            "success": all_successful,
            "results": activation_results,
            "productivity_baseline": self.state.productivity_baseline,
            "activated_at": self.state.activated_at.isoformat() if self.state.activated_at else None
        }

        logger.info(f"🛡️ Shield activation complete: {all_successful}")
        return result

    async def deactivate_shields(self, reason: str = "Work session complete") -> Dict[str, Any]:
        """
        Deactivate all active shields in parallel.

        Args:
            reason: Human-readable reason for deactivation

        Returns:
            Dict with deactivation results
        """
        logger.info(f"🛡️ Deactivating interruption shields: {reason}")

        # Check for false positive before deactivation
        if await self._detect_false_positive():
            logger.warning("🛡️ False positive detected - maintaining shields")
            return {
                "success": False,
                "error": "False positive detected",
                "maintained_shields": True
            }

        # Parallel shield deactivation
        deactivation_tasks = []
        shield_names = []

        for name, shield in self.shields.items():
            if shield is not None and self._is_shield_active(name):
                task = asyncio.create_task(
                    self._deactivate_single_shield(name, shield, reason)
                )
                deactivation_tasks.append(task)
                shield_names.append(name)

        if not deactivation_tasks:
            logger.info("🛡️ No active shields to deactivate")
            return {"success": True, "results": {}}

        # Wait for all deactivations
        try:
            results = await asyncio.gather(*deactivation_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"🛡️ Shield deactivation error: {e}")
            return {"success": False, "error": str(e)}

        # Process results
        deactivation_results = {}
        all_successful = True

        for name, result in zip(shield_names, results):
            if isinstance(result, Exception):
                logger.error(f"🛡️ Shield {name} deactivation failed: {result}")
                deactivation_results[name] = {"success": False, "error": str(result)}
                all_successful = False
            else:
                deactivation_results[name] = result
                if result.get("success", False):
                    # Update state
                    if name == "dnd":
                        self.state.dnd_active = False
                    elif name == "slack":
                        self.state.slack_active = False
                    elif name == "notifications":
                        self.state.notifications_active = False

        # Reset activation timestamp
        self.state.activated_at = None

        # Log to ConPort if configured
        if self.conport_client:
            logged = await self.conport_client.log_shield_deactivation(
                self.active_progress_id or "shield_activation",
                reason,
                deactivation_results,
                datetime.now()
            )
            if logged:
                logger.debug("✅ Shield deactivation logged to ConPort")
                self.active_progress_id = None  # Clear active progress ID
            else:
                logger.warning("⚠️ Failed to log shield deactivation to ConPort")

        # Store updated state in ConPort
        if self.conport_client:
            state_data = {
                "dnd_active": self.state.dnd_active,
                "slack_active": self.state.slack_active,
                "notifications_active": self.state.notifications_active,
                "activated_at": None,  # Cleared
                "productivity_baseline": self.state.productivity_baseline,
                "false_positive_detected": self.state.false_positive_detected
            }
            await self.conport_client.store_shield_state(state_data)

        # Notify callbacks
        await self._notify_state_change()

        result = {
            "success": all_successful,
            "results": deactivation_results,
            "deactivated_at": datetime.now().isoformat()
        }

        logger.info(f"🛡️ Shield deactivation complete: {all_successful}")
        return result

    async def get_shield_status(self) -> Dict[str, Any]:
        """Get current status of all shields"""
        status = {
            "state": {
                "dnd_active": self.state.dnd_active,
                "slack_active": self.state.slack_active,
                "notifications_active": self.state.notifications_active,
                "activated_at": self.state.activated_at.isoformat() if self.state.activated_at else None,
                "productivity_baseline": self.state.productivity_baseline,
                "false_positive_detected": self.state.false_positive_detected
            },
            "shields": {}
        }

        # Check individual shield status
        for name, shield in self.shields.items():
            if shield is not None:
                try:
                    shield_status = await shield.get_status()
                    status["shields"][name] = shield_status
                except Exception as e:
                    status["shields"][name] = {"error": str(e)}

        return status

    def add_state_change_callback(self, callback: Callable[[ShieldState], None]):
        """Add callback for shield state changes"""
        self._state_change_callbacks.append(callback)

    async def _activate_single_shield(self, name: str, shield, reason: str) -> Dict[str, Any]:
        """Activate a single shield with error handling"""
        try:
            result = await shield.activate(reason)
            logger.info(f"🛡️ Shield {name} activated successfully")
            return result
        except Exception as e:
            logger.error(f"🛡️ Shield {name} activation failed: {e}")
            raise

    async def _deactivate_single_shield(self, name: str, shield, reason: str) -> Dict[str, Any]:
        """Deactivate a single shield with error handling"""
        try:
            result = await shield.deactivate(reason)
            logger.info(f"🛡️ Shield {name} deactivated successfully")
            return result
        except Exception as e:
            logger.error(f"🛡️ Shield {name} deactivation failed: {e}")
            raise

    def _is_shield_active(self, name: str) -> bool:
        """Check if a specific shield is currently active"""
        if name == "dnd":
            return self.state.dnd_active
        elif name == "slack":
            return self.state.slack_active
        elif name == "notifications":
            return self.state.notifications_active
        return False

    async def _detect_false_positive(self) -> bool:
        """Detect if deactivation would be a false positive based on productivity"""
        if not self.state.activated_at:
            return False

        # Only check if activated recently (avoid checking after long sessions)
        activation_duration = datetime.now() - self.state.activated_at
        if activation_duration > timedelta(minutes=self.config.monitoring_window_minutes):
            return False

        current_productivity = await self.monitor.get_current_productivity()
        productivity_drop = self.state.productivity_baseline - current_productivity

        # Consider it a false positive if productivity dropped significantly
        false_positive = productivity_drop > 0.3  # 30% drop threshold

        if false_positive:
            self.state.false_positive_detected = True
            logger.warning(f"🛡️ False positive detected: productivity drop {productivity_drop:.2f}")

            # Log false positive event to ConPort
            if self.conport_client:
                event_details = {
                    "productivity_baseline": self.state.productivity_baseline,
                    "current_productivity": current_productivity,
                    "productivity_drop": productivity_drop,
                    "activated_at": self.state.activated_at.isoformat() if self.state.activated_at else None,
                    "reason": "Productivity dropped below threshold during shield deactivation"
                }
                await self.conport_client.log_shield_event("false_positive", event_details)

        return false_positive

    async def _notify_state_change(self):
        """Notify all registered callbacks of state changes"""
        for callback in self._state_change_callbacks:
            try:
                await callback(self.state)
            except Exception as e:
                logger.error(f"State change callback failed: {e}")