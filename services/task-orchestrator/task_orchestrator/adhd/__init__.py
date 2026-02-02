"""
Task-Orchestrator ADHD Module.

ADHD monitoring, accommodations, and cognitive load management.
Extracted from enhanced_orchestrator.py lines 634-690 and 1402-1443.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..config import settings
from ..models import OrchestrationTask, OrchestratorMetrics, TaskStatus


logger = logging.getLogger(__name__)


class ADHDMonitor:
    """Background monitor for ADHD accommodations."""

    def __init__(self):
        self.config = settings.adhd_config
        self.metrics = OrchestratorMetrics()
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Session tracking
        self.session_start: Optional[datetime] = None
        self.last_break: Optional[datetime] = None
        self.context_switch_count = 0
        self.current_cognitive_load = 0.0

    async def start_monitoring(self):
        """Start ADHD monitoring background worker."""
        self.running = True
        self.session_start = datetime.now(timezone.utc)
        self.last_break = self.session_start
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("🧠 ADHD monitoring started")

    async def stop_monitoring(self):
        """Stop ADHD monitoring."""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🧠 ADHD monitoring stopped")

    async def _monitor_loop(self):
        """Background monitor loop."""
        while self.running:
            try:
                await self._check_break_requirements()
                await self._monitor_cognitive_load()
                await self._detect_excessive_context_switching()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"ADHD monitoring error: {e}")
                await asyncio.sleep(300)  # 5-minute backoff on error

    async def _check_break_requirements(self):
        """Check if break is needed based on session duration."""
        if not self.last_break:
            return

        now = datetime.now(timezone.utc)
        minutes_since_break = (now - self.last_break).total_seconds() / 60

        if minutes_since_break >= self.config["mandatory_break_minutes"]:
            logger.warning("🛑 MANDATORY BREAK REQUIRED - Session too long!")
            self.metrics.adhd_accommodations_applied += 1
            
        elif minutes_since_break >= self.config["hyperfocus_warning_minutes"]:
            logger.warning(f"⚠️ Hyperfocus warning: {minutes_since_break:.0f} minutes without break")
            self.metrics.adhd_accommodations_applied += 1

        elif minutes_since_break >= self.config["break_interval_minutes"]:
            logger.info(f"💡 Break recommended: {minutes_since_break:.0f} minutes active")

    async def _monitor_cognitive_load(self):
        """Monitor overall cognitive load across active tasks."""
        # This would integrate with actual task tracking
        if self.current_cognitive_load > 0.8:
            logger.warning(f"⚠️ High cognitive load detected: {self.current_cognitive_load:.2f}")
            self.metrics.adhd_accommodations_applied += 1

    async def _detect_excessive_context_switching(self):
        """Detect and mitigate excessive context switching."""
        if self.context_switch_count > 5:
            logger.warning(
                f"⚠️ Excessive context switching detected: {self.context_switch_count} switches. "
                "Consider focusing on one task."
            )
            self.metrics.adhd_accommodations_applied += 1
            # Reset counter after warning
            self.context_switch_count = 0

    def record_break(self):
        """Record that a break was taken."""
        self.last_break = datetime.now(timezone.utc)
        self.context_switch_count = 0
        logger.info("☕ Break recorded - counters reset")

    def record_context_switch(self):
        """Record a context switch."""
        self.context_switch_count += 1

    async def apply_adhd_optimizations(self, task: OrchestrationTask) -> OrchestrationTask:
        """Apply ADHD optimizations to a task."""
        # Break down large tasks
        if task.estimated_minutes > 25:
            task.break_frequency_minutes = 25
            logger.debug(f"🧠 ADHD optimization: Set break frequency for task {task.id}")

        # Adjust cognitive load based on complexity
        task.cognitive_load = min(1.0, task.complexity_score * 1.2)

        # Set context switch limits based on priority
        if task.priority >= 3:  # High priority
            task.context_switches_allowed = 1
        else:
            task.context_switches_allowed = 2

        self.metrics.adhd_accommodations_applied += 1
        return task

    def get_adhd_state(self) -> Dict[str, Any]:
        """Get current ADHD state for Component 5 queries."""
        now = datetime.now(timezone.utc)
        
        session_minutes = 0
        if self.session_start:
            session_minutes = (now - self.session_start).total_seconds() / 60

        break_needed = False
        if self.last_break:
            minutes_since_break = (now - self.last_break).total_seconds() / 60
            break_needed = minutes_since_break >= self.config["break_interval_minutes"]

        return {
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "session_duration_minutes": round(session_minutes, 1),
            "last_break": self.last_break.isoformat() if self.last_break else None,
            "break_needed": break_needed,
            "context_switches": self.context_switch_count,
            "cognitive_load": self.current_cognitive_load,
            "accommodations_applied": self.metrics.adhd_accommodations_applied
        }


# Global singleton instance
adhd_monitor = ADHDMonitor()
