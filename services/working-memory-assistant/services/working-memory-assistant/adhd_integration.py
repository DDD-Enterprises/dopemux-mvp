#!/usr/bin/env python3
"""
ADHD Integration Module for Working Memory Assistant

Integrates ADHD Engine metrics into WMA snapshot creation and recovery processes.
Enriches context snapshots with real-time energy monitoring, attention state correlation,
and cognitive load assessment for ADHD-optimized interrupt recovery.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import time

from adhd_engine_client import get_adhd_client, get_adhd_context_for_snapshot

logger = logging.getLogger(__name__)

class ADHDIntegrationManager:
    """Manages integration between WMA and ADHD Engine."""

    def __init__(self):
        self.adhd_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize ADHD Engine connection."""
        if self._initialized:
            return

        try:
            self.adhd_client = await get_adhd_client()
            self._initialized = True
            logger.info("ADHD Integration Manager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ADHD Integration: {e}")
            self.adhd_client = None

    async def enrich_snapshot_with_adhd(self,
                                       snapshot_data: Dict[str, Any],
                                       user_id: str) -> Dict[str, Any]:
        """
        Enrich snapshot data with ADHD metrics.

        Args:
            snapshot_data: Base snapshot data
            user_id: User identifier for ADHD metrics

        Returns:
            Enhanced snapshot data with ADHD context
        """
        if not self.adhd_client:
            await self.initialize()
            if not self.adhd_client:
                logger.warning("ADHD Engine not available - enriching with degraded mode")
                return self._add_degraded_adhd_context(snapshot_data, user_id)

        try:
            # Get comprehensive ADHD context
            adhd_context = await self.adhd_client.get_comprehensive_adhd_context(user_id)

            # Enhance snapshot data
            enhanced_data = snapshot_data.copy()
            enhanced_data["adhd_context"] = adhd_context

            # Update snapshot metadata based on ADHD metrics
            enhanced_data = self._apply_adhd_metadata_enhancement(enhanced_data, adhd_context)

            logger.info(f"Enhanced snapshot for {user_id} with ADHD metrics")
            return enhanced_data

        except Exception as e:
            logger.error(f"Failed to enrich snapshot with ADHD data: {e}")
            return self._add_degraded_adhd_context(snapshot_data, user_id)

    def _add_degraded_adhd_context(self, snapshot_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Add degraded ADHD context when ADHD Engine is unavailable."""
        enhanced_data = snapshot_data.copy()
        enhanced_data["adhd_context"] = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "adhd_engine_available": False,
            "degraded_mode": True,
            "metrics": {
                "energy_level": {"error": "adhd_engine_unavailable"},
                "attention_state": {"error": "adhd_engine_unavailable"},
                "cognitive_load": {"error": "adhd_engine_unavailable"},
                "flow_state": {"error": "adhd_engine_unavailable"},
                "session_time": {"error": "adhd_engine_unavailable"},
                "activity_data": {"error": "adhd_engine_unavailable"},
                "break_recommendation": {"error": "adhd_engine_unavailable"}
            },
            "snapshot_priority": {
                "should_snapshot": True,  # Conservative default
                "priority_score": 0.5,
                "urgency": "medium",
                "reasoning": ["ADHD Engine unavailable - using conservative defaults"]
            }
        }
        return enhanced_data

    def _apply_adhd_metadata_enhancement(self,
                                       snapshot_data: Dict[str, Any],
                                       adhd_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply ADHD-aware metadata enhancements to snapshot."""

        enhanced = snapshot_data.copy()
        metrics = adhd_context.get("metrics", {})

        # Extract key ADHD metrics
        attention_state = self._extract_attention_state(metrics)
        energy_level = self._extract_energy_level(metrics)
        cognitive_load = self._extract_cognitive_load(metrics)

        # Enhance snapshot metadata
        metadata = enhanced.get("metadata", {})

        # Add ADHD-specific metadata
        metadata["adhd_enhanced"] = True
        metadata["attention_state"] = attention_state
        metadata["energy_level"] = energy_level
        metadata["cognitive_load"] = cognitive_load

        # Add snapshot priority
        priority = adhd_context.get("snapshot_priority", {})
        metadata["snapshot_priority"] = priority.get("priority_score", 0.5)
        metadata["snapshot_urgency"] = priority.get("urgency", "medium")

        # Add ADHD-aware recovery hints
        metadata["recovery_hints"] = self._generate_recovery_hints(adhd_context)

        enhanced["metadata"] = metadata
        return enhanced

    def _extract_attention_state(self, metrics: Dict[str, Any]) -> str:
        """Extract attention state from ADHD metrics."""
        attention = metrics.get("attention_state", {})
        if attention.get("error"):
            return "unknown"
        return attention.get("current_state", "unknown")

    def _extract_energy_level(self, metrics: Dict[str, Any]) -> float:
        """Extract energy level from ADHD metrics."""
        energy = metrics.get("energy_level", {})
        if energy.get("error"):
            return 0.5  # Neutral default
        return energy.get("current_energy", 0.5)

    def _extract_cognitive_load(self, metrics: Dict[str, Any]) -> float:
        """Extract cognitive load from ADHD metrics."""
        cognitive = metrics.get("cognitive_load", {})
        if cognitive.get("error"):
            return 0.5  # Neutral default
        return cognitive.get("current_load", 0.5)

    def _generate_recovery_hints(self, adhd_context: Dict[str, Any]) -> List[str]:
        """Generate ADHD-aware recovery hints."""
        hints = []
        metrics = adhd_context.get("metrics", {})
        priority = adhd_context.get("snapshot_priority", {})

        # Attention state hints
        attention = metrics.get("attention_state", {})
        if not attention.get("error"):
            state = attention.get("current_state")
            if state == "scattered":
                hints.append("Resume in focused environment - minimize distractions")
                hints.append("Use progressive disclosure - start with overview")
            elif state == "focused":
                hints.append("Resume directly - attention was stable")
            elif state == "transitioning":
                hints.append("Allow transition time - context may need rebuilding")

        # Energy level hints
        energy = metrics.get("energy_level", {})
        if not energy.get("error"):
            level = energy.get("current_energy", 0.5)
            if level < 0.3:
                hints.append("Low energy detected - consider break before resuming")
                hints.append("Start with small, manageable tasks")
            elif level > 0.7:
                hints.append("Good energy level - can handle complex recovery")

        # Cognitive load hints
        cognitive = metrics.get("cognitive_load", {})
        if not cognitive.get("error"):
            load = cognitive.get("current_load", 0.5)
            if load > 0.8:
                hints.append("High cognitive load - use gentle recovery approach")
                hints.append("Break complex tasks into smaller steps")
            elif load < 0.3:
                hints.append("Low cognitive load - can handle detailed recovery")

        # Break recommendation hints
        break_rec = metrics.get("break_recommendation", {})
        if not break_rec.get("error") and break_rec.get("should_take_break"):
            hints.append("Break recommended - consider taking break before recovery")
            hints.append("Recovery may be more effective after mental reset")

        # Priority-based hints
        urgency = priority.get("urgency", "medium")
        if urgency == "critical":
            hints.append("Critical context preservation - review carefully")
        elif urgency == "high":
            hints.append("High priority context - focus on key elements first")

        return hints if hints else ["Standard recovery approach recommended"]

    async def should_snapshot_based_on_adhd(self, user_id: str) -> Dict[str, Any]:
        """Determine if snapshot should be taken based on ADHD metrics."""
        if not self.adhd_client:
            await self.initialize()
            if not self.adhd_client:
                return {
                    "should_snapshot": True,  # Conservative default
                    "priority_score": 0.5,
                    "urgency": "medium",
                    "reasoning": ["ADHD Engine unavailable - using conservative defaults"]
                }

        try:
            return await self.adhd_client.should_snapshot_based_on_adhd(user_id)
        except Exception as e:
            logger.error(f"Failed to get ADHD-based snapshot decision: {e}")
            return {
                "should_snapshot": True,
                "priority_score": 0.5,
                "urgency": "medium",
                "reasoning": ["ADHD Engine error - using conservative defaults"]
            }

    async def get_recovery_optimization(self,
                                      user_id: str,
                                      context_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get ADHD-optimized recovery recommendations.

        Args:
            user_id: User identifier
            context_snapshot: The snapshot being recovered

        Returns:
            Recovery optimization recommendations
        """
        if not self.adhd_client:
            await self.initialize()

        optimization = {
            "recovery_approach": "standard",
            "progressive_disclosure": True,
            "chunking_strategy": "default",
            "attention_management": [],
            "energy_optimization": [],
            "cognitive_load_management": []
        }

        if not self.adhd_client:
            return optimization

        try:
            # Get current ADHD state
            current_context = await self.adhd_client.get_comprehensive_adhd_context(user_id)

            # Get snapshot ADHD context
            snapshot_adhd = context_snapshot.get("adhd_context", {})
            snapshot_metrics = snapshot_adhd.get("metrics", {})

            # Compare current vs snapshot state
            optimization = self._calculate_recovery_optimization(
                current_context, snapshot_metrics, context_snapshot
            )

        except Exception as e:
            logger.warning(f"Failed to get recovery optimization: {e}")

        return optimization

    def _calculate_recovery_optimization(self,
                                       current_context: Dict[str, Any],
                                       snapshot_metrics: Dict[str, Any],
                                       context_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal recovery approach based on ADHD state comparison."""

        optimization = {
            "recovery_approach": "progressive",
            "progressive_disclosure": True,
            "chunking_strategy": "small_chunks",
            "attention_management": [],
            "energy_optimization": [],
            "cognitive_load_management": []
        }

        current_metrics = current_context.get("metrics", {})

        # Compare attention states
        current_attention = self._extract_attention_state(current_metrics)
        snapshot_attention = snapshot_metrics.get("attention_state", {}).get("current_state", "unknown")

        if current_attention == "scattered" or snapshot_attention == "scattered":
            optimization["attention_management"].extend([
                "Minimize visual distractions during recovery",
                "Use single-focus recovery mode",
                "Consider noise-cancelling environment"
            ])
            optimization["chunking_strategy"] = "minimal_chunks"

        # Compare energy levels
        current_energy = self._extract_energy_level(current_metrics)
        snapshot_energy = snapshot_metrics.get("energy_level", {}).get("current_energy", 0.5)

        if current_energy < 0.4 or snapshot_energy < 0.4:
            optimization["energy_optimization"].extend([
                "Start with overview only",
                "Allow frequent breaks during recovery",
                "Consider postponing complex elements"
            ])
            optimization["progressive_disclosure"] = True
            optimization["recovery_approach"] = "gentle"

        # Compare cognitive load
        current_load = self._extract_cognitive_load(current_metrics)
        snapshot_load = snapshot_metrics.get("cognitive_load", {}).get("current_load", 0.5)

        if current_load > 0.7 or snapshot_load > 0.7:
            optimization["cognitive_load_management"].extend([
                "Present information in small chunks",
                "Allow time between recovery steps",
                "Provide clear navigation cues"
            ])
            optimization["chunking_strategy"] = "micro_chunks"

        # Check for break recommendations
        break_rec = current_metrics.get("break_recommendation", {})
        if not break_rec.get("error") and break_rec.get("should_take_break"):
            optimization["energy_optimization"].append(
                "Break recommended - consider short break before recovery"
            )

        return optimization

# Global integration manager instance
_adhd_integration = None

async def get_adhd_integration_manager() -> ADHDIntegrationManager:
    """Get or create ADHD Integration Manager instance."""
    global _adhd_integration
    if _adhd_integration is None:
        _adhd_integration = ADHDIntegrationManager()
        await _adhd_integration.initialize()
    return _adhd_integration

async def enrich_snapshot_with_adhd(snapshot_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Convenience function to enrich snapshot with ADHD data."""
    try:
        manager = await get_adhd_integration_manager()
        return await manager.enrich_snapshot_with_adhd(snapshot_data, user_id)
    except Exception as e:
        logger.error(f"Failed to enrich snapshot with ADHD data: {e}")
        # Return original data with degraded ADHD context
        return ADHDIntegrationManager()._add_degraded_adhd_context(snapshot_data, user_id)

async def should_snapshot_based_on_adhd(user_id: str) -> Dict[str, Any]:
    """Convenience function to check if snapshot should be taken."""
    try:
        manager = await get_adhd_integration_manager()
        return await manager.should_snapshot_based_on_adhd(user_id)
    except Exception as e:
        logger.warning(f"ADHD snapshot decision failed: {e}")
        return {"should_snapshot": True, "priority_score": 0.5, "urgency": "medium"}

async def get_recovery_optimization(user_id: str, context_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to get recovery optimization recommendations."""
    try:
        manager = await get_adhd_integration_manager()
        return await manager.get_recovery_optimization(user_id, context_snapshot)
    except Exception as e:
        logger.warning(f"Failed to get recovery optimization: {e}")
        return {
            "recovery_approach": "standard",
            "progressive_disclosure": True,
            "chunking_strategy": "default"
        }