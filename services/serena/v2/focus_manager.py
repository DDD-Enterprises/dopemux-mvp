"""
Serena v2 Focus Manager

Intelligent focus mode and cognitive load management for ADHD developers.
Manages attention state, distraction filtering, and focus session optimization.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class FocusMode(str, Enum):
    """Focus mode states."""
    OFF = "off"
    LIGHT = "light"      # Gentle filtering, reduce noise
    MEDIUM = "medium"    # Moderate filtering, focus on essential
    DEEP = "deep"        # Heavy filtering, minimal distractions
    HYPERFOCUS = "hyperfocus"  # Maximum filtering, single-task mode


class AttentionState(str, Enum):
    """Current attention state tracking."""
    SCATTERED = "scattered"
    TRANSITIONING = "transitioning"
    FOCUSED = "focused"
    HYPERFOCUSED = "hyperfocused"
    BREAK_NEEDED = "break_needed"


@dataclass
class FocusSession:
    """Represents a focus session with ADHD tracking."""
    session_id: str
    start_time: datetime
    mode: FocusMode
    target_duration: int  # minutes
    focus_area: str  # file or function being focused on
    distractions_filtered: int = 0
    context_switches: int = 0
    productivity_score: float = 0.0
    break_reminders: int = 0


class FocusManager:
    """
    Manages focus modes and attention state for ADHD developers.

    Features:
    - Intelligent focus mode with adaptive filtering
    - Attention state tracking and recommendations
    - Distraction detection and filtering
    - Break reminders and hyperfocus protection
    - Context switching minimization
    - Productivity insights and gentle feedback
    """

    def __init__(self):
        self.current_mode = FocusMode.OFF
        self.attention_state = AttentionState.SCATTERED
        self.current_session: Optional[FocusSession] = None

        # Focus configuration
        self.break_interval_minutes = 25  # Pomodoro-style
        self.max_hyperfocus_duration = 90  # Prevent ADHD hyperfocus burnout
        self.distraction_sensitivity = 0.7  # How aggressive filtering is

        # Tracking state
        self.sessions_today = []
        self.total_focus_time = 0  # minutes
        self.distractions_blocked = 0
        self.context_switch_count = 0
        self.last_break_time = datetime.now(timezone.utc)

        # Focus area tracking
        self.current_focus_files: Set[str] = set()
        self.focus_depth_stack = []  # Track navigation depth in focus area

        # Callbacks for UI integration
        self.mode_change_callbacks: List[Callable] = []
        self.break_reminder_callbacks: List[Callable] = []

    async def initialize(self) -> None:
        """Initialize focus manager and start background monitoring."""
        # Start background tasks
        asyncio.create_task(self._monitor_attention_state())
        asyncio.create_task(self._break_reminder_scheduler())

        logger.info("🧠 Focus Manager initialized with ADHD monitoring")

    # Focus Mode Management

    async def set_focus_mode(
        self,
        mode: FocusMode,
        target_file: str = None,
        duration_minutes: int = 25
    ) -> Dict[str, Any]:
        """Set focus mode with ADHD-optimized configuration."""
        previous_mode = self.current_mode
        self.current_mode = mode

        # End current session if active
        if self.current_session:
            await self._end_focus_session()

        # Start new session if not OFF
        if mode != FocusMode.OFF:
            await self._start_focus_session(mode, target_file, duration_minutes)

        # Notify callbacks
        for callback in self.mode_change_callbacks:
            try:
                await callback(mode, previous_mode)
            except Exception as e:
                logger.error(f"Focus mode callback failed: {e}")

        logger.info(f"🎯 Focus mode: {previous_mode.value} → {mode.value}")

        return {
            "previous_mode": previous_mode.value,
            "new_mode": mode.value,
            "session_active": self.current_session is not None,
            "target_file": target_file,
            "estimated_duration": duration_minutes,
            "adhd_benefits": self._get_mode_benefits(mode)
        }

    async def _start_focus_session(
        self,
        mode: FocusMode,
        target_file: str = None,
        duration_minutes: int = 25
    ) -> None:
        """Start new focus session."""
        session_id = f"focus_{datetime.now().timestamp()}"

        self.current_session = FocusSession(
            session_id=session_id,
            start_time=datetime.now(timezone.utc),
            mode=mode,
            target_duration=duration_minutes,
            focus_area=target_file or "general"
        )

        # Configure focus area
        if target_file:
            self.current_focus_files.add(target_file)
            # Add related files to focus area
            related_files = await self._find_focus_related_files(target_file)
            self.current_focus_files.update(related_files)

        logger.info(f"▶️ Focus session started: {mode.value} for {duration_minutes}min")

    async def _end_focus_session(self) -> Dict[str, Any]:
        """End current focus session with ADHD-friendly summary."""
        if not self.current_session:
            return {"message": "No active session"}

        session = self.current_session
        end_time = datetime.now(timezone.utc)
        duration = (end_time - session.start_time).total_seconds() / 60  # minutes

        # Calculate productivity score
        productivity_score = self._calculate_productivity_score(session, duration)
        session.productivity_score = productivity_score

        # Generate ADHD-friendly session summary
        summary = {
            "session_id": session.session_id,
            "mode": session.mode.value,
            "duration_minutes": round(duration, 1),
            "target_duration": session.target_duration,
            "productivity_score": f"{productivity_score:.1%}",
            "distractions_filtered": session.distractions_filtered,
            "context_switches": session.context_switches,
            "focus_area": session.focus_area,
            "completion_rate": f"{min(duration / session.target_duration, 1.0):.1%}",
            "session_quality": self._assess_session_quality(productivity_score, duration, session.target_duration)
        }

        # Archive session
        self.sessions_today.append(session)
        self.current_session = None
        self.current_focus_files.clear()

        logger.info(f"⏹️ Focus session ended: {summary['session_quality']} ({summary['duration_minutes']}min)")
        return summary

    def _calculate_productivity_score(self, session: FocusSession, actual_duration: float) -> float:
        """Calculate session productivity score."""
        base_score = 0.5

        # Duration factor (close to target = better)
        duration_ratio = actual_duration / max(session.target_duration, 1)
        if 0.8 <= duration_ratio <= 1.2:  # Within 20% of target
            base_score += 0.3
        elif 0.5 <= duration_ratio <= 1.5:  # Within 50% of target
            base_score += 0.1
        else:
            base_score -= 0.1

        # Distraction factor (fewer distractions = better)
        if session.distractions_filtered == 0:
            base_score += 0.2
        elif session.distractions_filtered <= 3:
            base_score += 0.1
        else:
            base_score -= 0.1

        # Context switching factor (fewer switches = better)
        if session.context_switches <= 2:
            base_score += 0.2
        elif session.context_switches <= 5:
            base_score += 0.1
        else:
            base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def _assess_session_quality(self, productivity_score: float, duration: float, target: float) -> str:
        """Assess session quality with ADHD-friendly labels."""
        if productivity_score >= 0.8:
            return "🚀 Excellent focus session!"
        elif productivity_score >= 0.6:
            return "✅ Good focused work"
        elif productivity_score >= 0.4:
            return "👍 Decent session with some distractions"
        else:
            return "💙 That's ok - focus takes practice"

    # Distraction Filtering

    async def should_filter_result(
        self,
        result: Dict[str, Any],
        file_path: str,
        result_type: str
    ) -> Tuple[bool, Optional[str]]:
        """Determine if result should be filtered based on current focus mode."""
        if self.current_mode == FocusMode.OFF:
            return False, None

        # Focus area filtering
        if self.current_session and self.current_focus_files:
            if file_path not in self.current_focus_files:
                if self.current_mode in {FocusMode.DEEP, FocusMode.HYPERFOCUS}:
                    return True, f"Outside focus area ({Path(file_path).name})"

        # Complexity filtering
        if result_type in {"symbols", "references"}:
            complexity = result.get("_adhd_metadata", {}).get("complexity_score", 0.5)

            complexity_thresholds = {
                FocusMode.LIGHT: 0.9,
                FocusMode.MEDIUM: 0.8,
                FocusMode.DEEP: 0.7,
                FocusMode.HYPERFOCUS: 0.6
            }

            threshold = complexity_thresholds.get(self.current_mode, 1.0)
            if complexity > threshold:
                return True, f"High complexity ({complexity:.1%})"

        # Result count filtering (prevent overwhelm)
        if result_type == "references":
            count_limits = {
                FocusMode.LIGHT: 50,
                FocusMode.MEDIUM: 20,
                FocusMode.DEEP: 10,
                FocusMode.HYPERFOCUS: 5
            }

            limit = count_limits.get(self.current_mode, 100)
            result_count = len(result) if isinstance(result, list) else 1

            if result_count > limit:
                return True, f"Too many results ({result_count} > {limit})"

        return False, None

    async def apply_focus_filtering(
        self,
        results: List[Dict[str, Any]],
        file_path: str,
        result_type: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply focus filtering to results with tracking."""
        if self.current_mode == FocusMode.OFF:
            return results, {"filtered": False}

        filtered_results = []
        filter_stats = {
            "original_count": len(results),
            "filtered_count": 0,
            "filter_reasons": [],
            "mode": self.current_mode.value
        }

        for result in results:
            should_filter, reason = await self.should_filter_result(result, file_path, result_type)

            if should_filter:
                filter_stats["filtered_count"] += 1
                if reason and reason not in filter_stats["filter_reasons"]:
                    filter_stats["filter_reasons"].append(reason)

                # Track distraction filtering
                if self.current_session:
                    self.current_session.distractions_filtered += 1
            else:
                filtered_results.append(result)

        filter_stats["final_count"] = len(filtered_results)

        if filter_stats["filtered_count"] > 0:
            logger.debug(f"🎯 Focus filter: {filter_stats['filtered_count']}/{filter_stats['original_count']} items filtered")

        return filtered_results, filter_stats

    # Attention State Monitoring

    async def _monitor_attention_state(self) -> None:
        """Background monitoring of attention state."""
        while True:
            try:
                await self._assess_attention_state()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Attention monitoring error: {e}")
                await asyncio.sleep(60)

    async def _assess_attention_state(self) -> None:
        """Assess current attention state based on activity patterns."""
        current_time = datetime.now(timezone.utc)

        # Check for signs of scattered attention
        if self.context_switch_count > 10:  # Many context switches
            if self.attention_state != AttentionState.SCATTERED:
                self.attention_state = AttentionState.SCATTERED
                logger.debug("🌀 Attention state: SCATTERED (many context switches)")

        # Check for sustained focus
        elif self.current_session:
            session_duration = (current_time - self.current_session.start_time).total_seconds() / 60

            if session_duration > 60 and self.current_session.context_switches <= 2:
                if self.attention_state != AttentionState.HYPERFOCUSED:
                    self.attention_state = AttentionState.HYPERFOCUSED
                    logger.debug("🚀 Attention state: HYPERFOCUSED")

                    # Hyperfocus protection for ADHD users
                    if session_duration > self.max_hyperfocus_duration:
                        await self._suggest_break("hyperfocus_protection")

            elif session_duration > 15 and self.current_session.context_switches <= 5:
                if self.attention_state != AttentionState.FOCUSED:
                    self.attention_state = AttentionState.FOCUSED
                    logger.debug("🎯 Attention state: FOCUSED")

        # Check if break is needed
        time_since_break = (current_time - self.last_break_time).total_seconds() / 60
        if time_since_break > self.break_interval_minutes * 2:  # Double break interval
            if self.attention_state != AttentionState.BREAK_NEEDED:
                self.attention_state = AttentionState.BREAK_NEEDED
                await self._suggest_break("time_based")

    async def _suggest_break(self, reason: str) -> None:
        """Suggest break with ADHD-friendly messaging."""
        break_messages = {
            "time_based": "☕ You've been coding for a while - consider a 5-minute break",
            "hyperfocus_protection": "🛡️ Hyperfocus detected - time for a healthy break to maintain productivity",
            "complexity_overload": "🧠 High complexity detected - a brief break might help clear your mind",
            "context_switching": "🌀 Lots of context switching - a break might help refocus"
        }

        message = break_messages.get(reason, "☕ Break time suggested")

        # Execute callbacks
        for callback in self.break_reminder_callbacks:
            try:
                await callback(message, reason)
            except Exception as e:
                logger.error(f"Break reminder callback failed: {e}")

        # Track break suggestion
        if self.current_session:
            self.current_session.break_reminders += 1

        logger.info(f"☕ Break suggested: {reason}")

    async def _break_reminder_scheduler(self) -> None:
        """Background scheduler for break reminders."""
        while True:
            try:
                await asyncio.sleep(self.break_interval_minutes * 60)  # Convert to seconds

                # Only suggest breaks during active sessions
                if self.current_session and self.current_mode != FocusMode.OFF:
                    session_duration = (
                        datetime.now(timezone.utc) - self.current_session.start_time
                    ).total_seconds() / 60

                    if session_duration >= self.break_interval_minutes:
                        await self._suggest_break("time_based")

            except Exception as e:
                logger.error(f"Break reminder scheduler error: {e}")
                await asyncio.sleep(300)  # 5 minutes before retry

    # Focus Area Management

    async def set_focus_area(
        self,
        file_path: str,
        function_name: str = None,
        context_radius: int = 3
    ) -> Dict[str, Any]:
        """Set current focus area with intelligent context building."""
        try:
            # Clear previous focus area
            self.current_focus_files.clear()

            # Add primary focus file
            self.current_focus_files.add(file_path)

            # Add contextually related files
            related_files = await self._build_focus_context(file_path, context_radius)
            self.current_focus_files.update(related_files)

            # Update current session
            if self.current_session:
                self.current_session.focus_area = f"{Path(file_path).name}"
                if function_name:
                    self.current_session.focus_area += f"::{function_name}"

            focus_info = {
                "primary_file": file_path,
                "function": function_name,
                "context_files": list(self.current_focus_files),
                "context_radius": context_radius,
                "mode": self.current_mode.value,
                "adhd_guidance": self._generate_focus_guidance()
            }

            logger.info(f"🎯 Focus area set: {Path(file_path).name} (+{len(related_files)} context files)")
            return focus_info

        except Exception as e:
            logger.error(f"Failed to set focus area: {e}")
            return {"error": str(e)}

    async def _build_focus_context(self, primary_file: str, radius: int) -> Set[str]:
        """Build intelligent focus context around primary file."""
        context_files = set()

        try:
            primary_path = Path(primary_file)

            # Same directory files (immediate context)
            if radius >= 1 and primary_path.parent.exists():
                same_dir = [
                    str(f) for f in primary_path.parent.glob(f"*{primary_path.suffix}")
                    if f != primary_path and f.is_file()
                ]
                context_files.update(same_dir[:3])  # Limit to 3 for ADHD

            # Parent directory files (broader context)
            if radius >= 2 and primary_path.parent.parent.exists():
                parent_files = [
                    str(f) for f in primary_path.parent.parent.rglob(f"*{primary_path.suffix}")
                    if f != primary_path and "test" not in str(f).lower()
                ]
                context_files.update(parent_files[:2])  # Limit to 2

            # Test files (if relevant)
            if radius >= 3:
                test_patterns = [
                    f"test_{primary_path.stem}.py",
                    f"{primary_path.stem}_test.py",
                    f"test_{primary_path.stem}.ts",
                    f"{primary_path.stem}.test.ts"
                ]

                for pattern in test_patterns:
                    test_file = primary_path.parent / pattern
                    if test_file.exists():
                        context_files.add(str(test_file))

            return context_files

        except Exception as e:
            logger.error(f"Failed to build focus context: {e}")
            return set()

    def _generate_focus_guidance(self) -> List[str]:
        """Generate ADHD-friendly focus guidance."""
        guidance = []

        mode_guidance = {
            FocusMode.LIGHT: [
                "✨ Light focus: Gentle noise reduction active",
                "💡 Complex items are still visible but marked"
            ],
            FocusMode.MEDIUM: [
                "🎯 Medium focus: Moderate filtering to reduce cognitive load",
                "📋 Only showing relevant results and essential information"
            ],
            FocusMode.DEEP: [
                "🔬 Deep focus: Heavy filtering for concentration",
                "⚡ Only essential items shown - distractions minimized"
            ],
            FocusMode.HYPERFOCUS: [
                "🚀 Hyperfocus mode: Maximum concentration support",
                "🛡️ All non-essential information filtered out"
            ]
        }

        guidance.extend(mode_guidance.get(self.current_mode, []))

        # Session-specific guidance
        if self.current_session:
            duration = (datetime.now(timezone.utc) - self.current_session.start_time).total_seconds() / 60
            if duration > self.break_interval_minutes:
                guidance.append("☕ Consider taking a break soon")

        return guidance

    # Context Switching Management

    async def track_context_switch(
        self,
        from_file: str,
        to_file: str,
        reason: str = "navigation"
    ) -> Dict[str, Any]:
        """Track context switch for ADHD pattern analysis."""
        self.context_switch_count += 1

        # Update session tracking
        if self.current_session:
            self.current_session.context_switches += 1

        switch_info = {
            "from_file": Path(from_file).name,
            "to_file": Path(to_file).name,
            "reason": reason,
            "session_switches": self.current_session.context_switches if self.current_session else 0,
            "total_switches_today": self.context_switch_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # ADHD guidance for excessive switching
        if self.current_session and self.current_session.context_switches > 10:
            switch_info["adhd_guidance"] = "🌀 Many context switches detected - consider using focus mode to reduce distractions"

        logger.debug(f"🔄 Context switch: {switch_info['from_file']} → {switch_info['to_file']}")
        return switch_info

    # Utility Methods

    def is_focus_mode_active(self) -> bool:
        """Check if any focus mode is active."""
        return self.current_mode != FocusMode.OFF

    def get_focus_mode(self) -> FocusMode:
        """Get current focus mode."""
        return self.current_mode

    def is_in_focus_area(self, file_path: str) -> bool:
        """Check if file is in current focus area."""
        return file_path in self.current_focus_files

    async def _find_focus_related_files(self, file_path: str) -> List[str]:
        """Find files related to focus area."""
        # This would implement intelligent related file detection
        # For now, simple implementation
        try:
            path = Path(file_path)
            if path.parent.exists():
                related = [
                    str(f) for f in path.parent.glob(f"*{path.suffix}")
                    if f != path and f.is_file()
                ]
                return related[:2]  # Limit for ADHD
            return []
        except Exception:
            return []

    def _get_mode_benefits(self, mode: FocusMode) -> List[str]:
        """Get ADHD benefits for focus mode."""
        benefits = {
            FocusMode.OFF: ["Full information available", "No filtering applied"],
            FocusMode.LIGHT: ["Gentle noise reduction", "Complexity indicators added"],
            FocusMode.MEDIUM: ["Moderate distraction filtering", "Essential information prioritized"],
            FocusMode.DEEP: ["Heavy distraction filtering", "Focus area emphasized"],
            FocusMode.HYPERFOCUS: ["Maximum concentration support", "Minimal information display"]
        }

        return benefits.get(mode, [])

    # Event Management

    def add_mode_change_callback(self, callback: Callable) -> None:
        """Add callback for focus mode changes."""
        self.mode_change_callbacks.append(callback)

    def add_break_reminder_callback(self, callback: Callable) -> None:
        """Add callback for break reminders."""
        self.break_reminder_callbacks.append(callback)

    # Health and Statistics

    async def get_focus_statistics(self) -> Dict[str, Any]:
        """Get focus session statistics for ADHD insights."""
        try:
            current_time = datetime.now(timezone.utc)

            # Today's session stats
            today_sessions = len(self.sessions_today)
            total_focus_minutes = sum(
                (session.start_time - session.start_time).total_seconds() / 60
                for session in self.sessions_today
            )

            # Current session info
            current_session_info = {}
            if self.current_session:
                session_duration = (current_time - self.current_session.start_time).total_seconds() / 60
                current_session_info = {
                    "active": True,
                    "mode": self.current_session.mode.value,
                    "duration_minutes": round(session_duration, 1),
                    "target_minutes": self.current_session.target_duration,
                    "distractions_filtered": self.current_session.distractions_filtered,
                    "context_switches": self.current_session.context_switches,
                    "focus_area": self.current_session.focus_area
                }
            else:
                current_session_info = {"active": False}

            return {
                "current_session": current_session_info,
                "attention_state": self.attention_state.value,
                "todays_stats": {
                    "sessions_completed": today_sessions,
                    "total_focus_minutes": round(total_focus_minutes, 1),
                    "context_switches": self.context_switch_count,
                    "distractions_blocked": self.distractions_blocked
                },
                "focus_areas": list(self.current_focus_files),
                "time_since_last_break": round(
                    (current_time - self.last_break_time).total_seconds() / 60, 1
                )
            }

        except Exception as e:
            logger.error(f"Failed to get focus statistics: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for focus manager."""
        try:
            return {
                "status": "🧠 Active",
                "current_mode": self.current_mode.value,
                "attention_state": self.attention_state.value,
                "session_active": self.current_session is not None,
                "monitoring_active": True,
                "callbacks_registered": {
                    "mode_change": len(self.mode_change_callbacks),
                    "break_reminder": len(self.break_reminder_callbacks)
                }
            }

        except Exception as e:
            logger.error(f"Focus manager health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Close focus manager and end any active session."""
        if self.current_session:
            await self._end_focus_session()

        logger.info("🧠 Focus Manager closed")

    # Quick Action Methods for UI Integration

    async def quick_focus_toggle(self, file_path: str = None) -> Dict[str, Any]:
        """Quick toggle between off and medium focus for ADHD users."""
        if self.current_mode == FocusMode.OFF:
            return await self.set_focus_mode(FocusMode.MEDIUM, file_path, 25)
        else:
            return await self.set_focus_mode(FocusMode.OFF)

    async def emergency_focus_reset(self) -> Dict[str, Any]:
        """Emergency reset for overwhelmed ADHD users."""
        logger.info("🚨 Emergency focus reset - clearing all state")

        # End current session
        if self.current_session:
            await self._end_focus_session()

        # Reset state
        self.current_mode = FocusMode.OFF
        self.attention_state = AttentionState.TRANSITIONING
        self.current_focus_files.clear()
        self.context_switch_count = 0
        self.distractions_blocked = 0

        return {
            "status": "reset_complete",
            "message": "💙 Focus state reset - starting fresh",
            "recommendations": [
                "Take a 5-minute break",
                "Start with light focus mode",
                "Focus on one file at a time"
            ]
        }