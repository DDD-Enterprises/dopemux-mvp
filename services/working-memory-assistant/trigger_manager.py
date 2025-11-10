#!/usr/bin/env python3
"""
Working Memory Assistant - Automatic Trigger Manager
Proactive snapshot creation based on ADHD state changes and system events.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from .main import WMAService
from .adhd_engine_client import ADHDEngineClient
from .utils import get_logger

class TriggerManager:
    """
    Automatic snapshot trigger manager.
    Monitors ADHD state changes and system events for proactive context capture.
    """

    def __init__(self, wma_service: WMAService, adhd_client: ADHDEngineClient):
        self.wma_service = wma_service
        self.adhd_client = adhd_client
        self.logger = get_logger(__name__)
        self.last_states = {}  # User state history
        self.trigger_thresholds = {
            'energy_delta': 0.2,
            'load_delta': 0.3,
            'poll_interval': 30,  # seconds
            'idle_timeout': 300,  # 5 minutes
            'duplicate_interval': 300  # 5 minutes between snapshots for same user
        }
        self.running = False
        self.poll_task = None

    async def start_monitoring(self):
        """Start background monitoring for all users."""
        self.running = True
        self.poll_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Automatic trigger monitoring started")

    async def stop_monitoring(self):
        """Stop background monitoring."""
        self.running = False
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Automatic trigger monitoring stopped")

    async def _monitoring_loop(self):
        """Periodic monitoring loop for all users."""
        while self.running:
            try:
                await self._check_all_users()
                await asyncio.sleep(self.trigger_thresholds['poll_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _check_all_users(self):
        """Check all users for trigger conditions."""
        # In production, query ConPort for active users
        users = ["test_user_123"]  # Placeholder for active users
        for user_id in users:
            await self._check_user_triggers(user_id)

    async def _check_user_triggers(self, user_id: str):
        """Check if user meets trigger conditions for automatic snapshot."""
        try:
            # Get current ADHD state
            adhd_state = await self.adhd_client.get_adhd_context(user_id)
            if not adhd_state or not adhd_state.get('is_available'):
                return

            current_energy = adhd_state.get('energy_level', {}).get('level', 0.5)
            current_attention = adhd_state.get('attention_state', {}).get('state', 'neutral')
            current_load = adhd_state.get('cognitive_load', {}).get('load', 0.5)

            # Get last known state
            last_state = self.last_states.get(user_id, {})
            last_energy = last_state.get('energy_level', 0.5)
            last_attention = last_state.get('attention_state', 'neutral')
            last_load = last_state.get('cognitive_load', 0.5)
            last_snapshot = last_state.get('last_snapshot', datetime.min)

            # Check triggers
            triggers = []

            # Energy change trigger
            if abs(current_energy - last_energy) > self.trigger_thresholds['energy_delta']:
                triggers.append(f"energy_change: {last_energy:.1f} → {current_energy:.1f}")

            # Attention state change trigger
            if current_attention != last_attention:
                triggers.append(f"attention_change: {last_attention} → {current_attention}")

            # Cognitive load spike trigger
            if current_load - last_load > self.trigger_thresholds['load_delta']:
                triggers.append(f"load_spike: {last_load:.1f} → {current_load:.1f}")

            # Duplicate snapshot prevention
            if (datetime.now() - last_snapshot).total_seconds() < self.trigger_thresholds['duplicate_interval']:
                triggers = []  # Skip if too soon

            # Trigger snapshot if any conditions met
            if triggers:
                await self._trigger_snapshot(user_id, triggers)

                # Update last known state
                self.last_states[user_id] = {
                    'energy_level': current_energy,
                    'attention_state': current_attention,
                    'cognitive_load': current_load,
                    'last_snapshot': datetime.now()
                }
            else:
                # Update last known state without snapshot
                self.last_states[user_id] = {
                    'energy_level': current_energy,
                    'attention_state': current_attention,
                    'cognitive_load': current_load
                }

        except Exception as e:
            self.logger.error(f"Error checking triggers for {user_id}: {e}")

    async def _trigger_snapshot(self, user_id: str, triggers: List[str]):
        """Trigger automatic context snapshot."""
        try:
            # Capture current context
            context = {
                "user_id": user_id,
                "context_type": "automatic",
                "triggers": triggers,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "automatic_capture": True,
                    "trigger_reasons": triggers,
                    "performance_note": "Proactive capture to preserve current state"
                }
            }

            # Create snapshot via WMA service
            snapshot_id = await self.wma_service.create_snapshot(context)

            self.logger.info(f"Automatic snapshot triggered for {user_id}: {triggers}", extra={
                'user_id': user_id,
                'snapshot_id': snapshot_id,
                'triggers': triggers
            })

        except Exception as e:
            self.logger.error(f"Failed to trigger snapshot for {user_id}: {e}", extra={
                'user_id': user_id,
                'triggers': triggers
            })
