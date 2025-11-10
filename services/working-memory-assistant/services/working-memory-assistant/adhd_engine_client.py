#!/usr/bin/env python3
"""
ADHD Engine Client for Working Memory Assistant Integration

Provides real-time ADHD accommodation data to enhance context snapshots and recovery.
Integrates with ADHD Engine for energy monitoring, attention state correlation, and cognitive load assessment.
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class ADHDEngineClient:
    """Client for integrating with ADHD Engine services."""

    def __init__(self, base_url: str = "http://host.docker.internal:8095"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=5.0)
        self._connection_verified = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def verify_connection(self) -> bool:
        """Verify connection to ADHD Engine."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self._connection_verified = True
                    logger.info("ADHD Engine connection verified")
                    return True
        except Exception as e:
            logger.warning(f"ADHD Engine connection failed: {e}")

        self._connection_verified = False
        return False

    async def get_energy_level(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current energy level for user."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/energy-level/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get energy level for {user_id}: {e}")
        return None

    async def get_attention_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current attention state for user."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/attention-state/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get attention state for {user_id}: {e}")
        return None

    async def get_cognitive_load(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current cognitive load for user."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/cognitive-load/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get cognitive load for {user_id}: {e}")
        return None

    async def get_flow_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current flow state for user."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/flow-state/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get flow state for {user_id}: {e}")
        return None

    async def get_session_time(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session time information for user."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/session-time/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get session time for {user_id}: {e}")
        return None

    async def recommend_break(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get break recommendation for user."""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/recommend-break",
                                            json={"user_id": user_id})
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get break recommendation for {user_id}: {e}")
        return None

    async def get_activity_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get recent activity data for user."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/activity/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get activity data for {user_id}: {e}")
        return None

    async def assess_task_complexity(self, task_description: str) -> Optional[Dict[str, Any]]:
        """Assess complexity of a task description."""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/assess-task",
                                            json={"task_description": task_description})
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to assess task complexity: {e}")
        return None

    async def predict_cognitive_state(self, user_id: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Predict future cognitive state based on current context."""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/predict",
                                            json={
                                                "user_id": user_id,
                                                "context": context,
                                                "prediction_type": "cognitive_state"
                                            })
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to predict cognitive state for {user_id}: {e}")
        return None

    async def get_comprehensive_adhd_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive ADHD context for snapshot enrichment."""
        if not self._connection_verified:
            if not await self.verify_connection():
                return {"error": "ADHD Engine not available", "degraded_mode": True}

        # Gather all ADHD metrics in parallel
        tasks = [
            self.get_energy_level(user_id),
            self.get_attention_state(user_id),
            self.get_cognitive_load(user_id),
            self.get_flow_state(user_id),
            self.get_session_time(user_id),
            self.get_activity_data(user_id),
            self.recommend_break(user_id)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        context = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "adhd_engine_available": True,
            "metrics": {}
        }

        metric_names = [
            "energy_level", "attention_state", "cognitive_load",
            "flow_state", "session_time", "activity_data", "break_recommendation"
        ]

        for name, result in zip(metric_names, results):
            if isinstance(result, Exception):
                context["metrics"][name] = {"error": str(result)}
            elif result is None:
                context["metrics"][name] = {"error": "not_available"}
            else:
                context["metrics"][name] = result

        # Calculate ADHD-aware snapshot priority
        context["snapshot_priority"] = self._calculate_snapshot_priority(context)

        return context

    def _calculate_snapshot_priority(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate snapshot priority based on ADHD metrics."""
        metrics = context.get("metrics", {})

        priority = {
            "should_snapshot": False,
            "priority_score": 0.0,  # 0.0-1.0
            "reasoning": [],
            "urgency": "low"  # low, medium, high, critical
        }

        # Energy level assessment
        energy = metrics.get("energy_level", {})
        if energy and not energy.get("error"):
            energy_level = energy.get("current_energy", 0.5)
            if energy_level < 0.3:  # Low energy
                priority["priority_score"] += 0.3
                priority["reasoning"].append("Low energy detected - high preservation priority")

        # Attention state assessment
        attention = metrics.get("attention_state", {})
        if attention and not attention.get("error"):
            state = attention.get("current_state", "unknown")
            if state == "scattered":
                priority["priority_score"] += 0.4
                priority["reasoning"].append("Scattered attention - critical preservation needed")
            elif state == "transitioning":
                priority["priority_score"] += 0.2
                priority["reasoning"].append("Attention transitioning - moderate preservation priority")

        # Cognitive load assessment
        cognitive = metrics.get("cognitive_load", {})
        if cognitive and not cognitive.get("error"):
            load = cognitive.get("current_load", 0.5)
            if load > 0.8:  # High cognitive load
                priority["priority_score"] += 0.3
                priority["reasoning"].append("High cognitive load - preservation critical")

        # Flow state assessment
        flow = metrics.get("flow_state", {})
        if flow and not flow.get("error"):
            in_flow = flow.get("in_flow_state", False)
            if in_flow:
                priority["priority_score"] += 0.1
                priority["reasoning"].append("In flow state - gentle preservation")

        # Break recommendation assessment
        break_rec = metrics.get("break_recommendation", {})
        if break_rec and not break_rec.get("error"):
            should_break = break_rec.get("should_take_break", False)
            if should_break:
                priority["priority_score"] += 0.2
                priority["reasoning"].append("Break recommended - context preservation advised")

        # Determine if snapshot should be taken
        priority["should_snapshot"] = priority["priority_score"] >= 0.5

        # Determine urgency level
        if priority["priority_score"] >= 0.8:
            priority["urgency"] = "critical"
        elif priority["priority_score"] >= 0.6:
            priority["urgency"] = "high"
        elif priority["priority_score"] >= 0.4:
            priority["urgency"] = "medium"
        else:
            priority["urgency"] = "low"

        return priority

    async def should_snapshot_based_on_adhd(self, user_id: str) -> Dict[str, Any]:
        """Determine if snapshot should be taken based on ADHD metrics."""
        context = await self.get_comprehensive_adhd_context(user_id)
        return context.get("snapshot_priority", {"should_snapshot": False, "urgency": "low"})

# Global client instance
_adhd_client = None

async def get_adhd_client() -> ADHDEngineClient:
    """Get or create ADHD Engine client instance."""
    global _adhd_client
    if _adhd_client is None:
        _adhd_client = ADHDEngineClient()
    return _adhd_client

async def get_adhd_context_for_snapshot(user_id: str) -> Dict[str, Any]:
    """Convenience function to get ADHD context for snapshot enrichment."""
    try:
        async with ADHDEngineClient() as client:
            return await client.get_comprehensive_adhd_context(user_id)
    except Exception as e:
        logger.warning(f"Failed to get ADHD context for snapshot: {e}")
        return {
            "error": "ADHD Engine unavailable",
            "degraded_mode": True,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "snapshot_priority": {
                "should_snapshot": False,
                "priority_score": 0.0,
                "urgency": "low",
                "reasoning": ["ADHD Engine unavailable - using degraded mode"]
            }
        }