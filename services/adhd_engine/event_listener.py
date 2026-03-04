"""
ADHD Event Listener - Central Event-Driven Trigger System

Subscribes to EventBus and triggers ADHD detectors implicitly based on events.
Runs as a background asyncio task in the ADHD Engine.

This is the core of Phase 1: Implicit Trigger Infrastructure.
Events flow in from various sources (Workspace Watcher, Desktop Commander,
Claude Code hooks, etc.) and automatically trigger the appropriate detectors.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ADHDFinding:
    """Structured finding from an ADHD detector."""
    finding_type: str
    severity: str  # low, medium, high, critical
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None
    source_event: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class ADHDEventListener:
    """
    Central event listener that triggers ADHD detectors implicitly.
    
    Features:
    - Subscribes to EventBus for all ADHD-relevant events
    - Routes events to appropriate detectors
    - Surfaces findings through multiple channels
    - Maintains rolling activity windows for pattern detection
    """
    
    def __init__(
        self,
        event_bus,
        hyperfocus_guard=None,
        overwhelm_detector=None,
        procrastination_detector=None,
        working_memory_support=None,
        context_preserver=None,
        activity_tracker=None,
        output_channels: Optional[List] = None
    ):
        """
        Initialize ADHD Event Listener.
        
        Args:
            event_bus: EventBus instance for subscribing to events
            hyperfocus_guard: HyperfocusGuard detector instance
            overwhelm_detector: OverwhelmDetector instance
            procrastination_detector: ProcrastinationDetector instance
            working_memory_support: WorkingMemorySupport instance
            context_preserver: ContextPreserver instance
            activity_tracker: ActivityTracker instance
            output_channels: List of output channel handlers
        """
        self.event_bus = event_bus
        self.hyperfocus_guard = hyperfocus_guard
        self.overwhelm_detector = overwhelm_detector
        self.procrastination_detector = procrastination_detector
        self.working_memory_support = working_memory_support
        self.context_preserver = context_preserver
        self.activity_tracker = activity_tracker
        self.output_channels = output_channels or []
        
        # Rolling activity windows for pattern detection
        self._file_activity_window: List[Dict] = []  # Last 15 min
        self._task_switch_window: List[Dict] = []    # Last 15 min
        self._context_switch_count = 0
        
        # State tracking
        self._is_running = False
        self._current_user_id: Optional[str] = None
        self._session_start_time: Optional[datetime] = None
        
        # Event handlers mapping
        self._handlers: Dict[str, Callable[[Dict], Awaitable[None]]] = {
            # Activity events
            "file_opened": self._on_file_activity,
            "file_saved": self._on_file_activity,
            "file_closed": self._on_file_activity,
            "file_activity": self._on_file_activity,
            "window_switched": self._on_window_switch,
            "app_focused": self._on_app_focus,
            "idle_detected": self._on_idle,
            "activity_resumed": self._on_activity_resumed,
            
            # Session events
            "session_started": self._on_session_started,
            "session_paused": self._on_session_paused,
            "session_completed": self._on_session_completed,
            
            # Progress events
            "task_started": self._on_task_started,
            "task_completed": self._on_task_completed,
            "task_switched": self._on_task_switched,
            "git_commit": self._on_git_commit,
            
            # ADHD state events
            "energy_changed": self._on_energy_changed,
            "attention_changed": self._on_attention_changed,
            "break_refused": self._on_break_refused,
            
            # Calendar events
            "meeting_started": self._on_meeting_started,
            "meeting_ended": self._on_meeting_ended,
            
            # Claude Code events
            "claude_prompt_received": self._on_claude_prompt,
            "claude_tool_started": self._on_claude_tool,
            "claude_session_stopped": self._on_claude_stop,
        }
    
    async def start(self, user_id: str = "default"):
        """
        Start listening for events.
        
        Args:
            user_id: User identifier for personalized detection
        """
        self._is_running = True
        self._current_user_id = user_id
        
        logger.info(f"🎯 ADHD Event Listener starting for user: {user_id}")
        
        try:
            async for msg_id, event in self.event_bus.subscribe(
                stream="dopemux:events",
                consumer_group="adhd-engine",
                consumer_name=f"listener-{user_id}"
            ):
                if not self._is_running:
                    break
                    
                await self._dispatch(event)
                
        except Exception as e:
            logger.error(f"❌ ADHD Event Listener error: {e}")
            raise
        finally:
            self._is_running = False
            logger.info("📭 ADHD Event Listener stopped")
    
    async def stop(self):
        """Stop the event listener."""
        self._is_running = False
    
    async def _dispatch(self, event):
        """Dispatch event to appropriate handler."""
        handler = self._handlers.get(event.type)
        
        if handler:
            try:
                await handler(event.data)
            except Exception as e:
                logger.error(f"❌ Handler error for {event.type}: {e}")
        else:
            logger.debug(f"No handler for event type: {event.type}")
    
    # ─────────────────────────────────────────────────────────────
    # Activity Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    async def _on_file_activity(self, data: Dict[str, Any]):
        """Handle file activity events."""
        # Add to rolling window
        self._file_activity_window.append({
            "file": data.get("file"),
            "action": data.get("action"),
            "timestamp": datetime.utcnow()
        })
        
        # Trim window to last 15 minutes
        cutoff = datetime.utcnow().timestamp() - 900
        self._file_activity_window = [
            a for a in self._file_activity_window 
            if a["timestamp"].timestamp() > cutoff
        ]
        
        # Check for procrastination patterns (lots of reads, few writes)
        if self.procrastination_detector:
            reads = sum(1 for a in self._file_activity_window if a["action"] == "opened")
            writes = sum(1 for a in self._file_activity_window if a["action"] == "saved")
            
            if reads > 10 and writes < 2:
                # Possible research rabbit hole
                result = self.procrastination_detector.check_procrastination(
                    self._current_user_id,
                    {"file_views": [a["file"] for a in self._file_activity_window]}
                )
                if result.get("detected"):
                    await self._surface_finding(ADHDFinding(
                        finding_type="procrastination_detected",
                        severity="medium",
                        message=result.get("message", "Possible research rabbit hole detected"),
                        data=result,
                        source_event="file_activity",
                        recommended_actions=["Consider writing code", "Set 5-min micro-goal"]
                    ))
    
    async def _on_window_switch(self, data: Dict[str, Any]):
        """Handle window/app switch events from Desktop Commander."""
        from_app = data.get("from_app")
        to_app = data.get("to_app")
        
        # Track context switch
        self._context_switch_count += 1
        
        # Trigger working memory support
        if self.working_memory_support:
            # Auto-save breadcrumb on IDE exit
            if from_app and "code" in from_app.lower():
                await self.working_memory_support.save_breadcrumb(
                    self._current_user_id,
                    f"Switched from {from_app} to {to_app}"
                )
        
        # Trigger context preserver on significant switches
        if self.context_preserver:
            # Leaving IDE for >5 switches might indicate distraction
            if self._context_switch_count > 5:
                await self.context_preserver.maybe_save_context(
                    self._current_user_id,
                    reason="frequent_context_switches"
                )
    
    async def _on_app_focus(self, data: Dict[str, Any]):
        """Handle app focus events."""
        app_name = data.get("app")
        
        # Reset context switch count when returning to IDE
        if app_name and "code" in app_name.lower():
            if self._context_switch_count > 3:
                # Offer "where was I?" on return
                if self.working_memory_support:
                    summary = await self.working_memory_support.get_return_summary(
                        self._current_user_id
                    )
                    if summary:
                        await self._surface_finding(ADHDFinding(
                            finding_type="context_restored",
                            severity="low",
                            message=f"Welcome back! {summary}",
                            source_event="app_focused"
                        ))
            
            self._context_switch_count = 0
    
    async def _on_idle(self, data: Dict[str, Any]):
        """Handle idle detection."""
        idle_minutes = data.get("minutes", 0)
        
        # Trigger context save on extended idle
        if idle_minutes >= 5 and self.context_preserver:
            await self.context_preserver.save_context(
                self._current_user_id,
                reason="idle_detected"
            )
    
    async def _on_activity_resumed(self, data: Dict[str, Any]):
        """Handle activity resumed after idle."""
        if self.working_memory_support:
            summary = await self.working_memory_support.remind_forgotten_context()
            if summary:
                await self._surface_finding(ADHDFinding(
                    finding_type="context_reminder",
                    severity="low",
                    message=summary,
                    source_event="activity_resumed"
                ))
    
    # ─────────────────────────────────────────────────────────────
    # Session Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    async def _on_session_started(self, data: Dict[str, Any]):
        """Handle session start."""
        self._session_start_time = datetime.utcnow()
        self._context_switch_count = 0
        
        logger.info(f"🎯 Session started for {self._current_user_id}")
    
    async def _on_session_paused(self, data: Dict[str, Any]):
        """Handle session pause."""
        if self.context_preserver:
            await self.context_preserver.save_context(
                self._current_user_id,
                reason="session_paused"
            )
    
    async def _on_session_completed(self, data: Dict[str, Any]):
        """Handle session completion."""
        # Calculate session duration for hyperfocus check
        if self._session_start_time and self.hyperfocus_guard:
            duration = (datetime.utcnow() - self._session_start_time).total_seconds() / 60
            
            if duration > 90:
                await self._surface_finding(ADHDFinding(
                    finding_type="hyperfocus_detected",
                    severity="medium" if duration < 120 else "high",
                    message=f"Extended focus session: {int(duration)} minutes",
                    data={"duration_minutes": int(duration)},
                    source_event="session_completed",
                    recommended_actions=["Take a break", "Stretch", "Hydrate"]
                ))
    
    # ─────────────────────────────────────────────────────────────
    # Progress Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    async def _on_task_started(self, data: Dict[str, Any]):
        """Handle task start."""
        pass  # Tracking only
    
    async def _on_task_completed(self, data: Dict[str, Any]):
        """Handle task completion."""
        # Positive reinforcement!
        await self._surface_finding(ADHDFinding(
            finding_type="task_completed",
            severity="low",
            message="🎉 Task completed! Great work!",
            data=data,
            source_event="task_completed"
        ))
    
    async def _on_task_switched(self, data: Dict[str, Any]):
        """Handle task switch - potential overwhelm indicator."""
        self._task_switch_window.append({
            "from_task": data.get("from_task"),
            "to_task": data.get("to_task"),
            "timestamp": datetime.utcnow()
        })
        
        # Trim to 15 min window
        cutoff = datetime.utcnow().timestamp() - 900
        self._task_switch_window = [
            s for s in self._task_switch_window 
            if s["timestamp"].timestamp() > cutoff
        ]
        
        # Check for overwhelm (rapid task switching)
        if len(self._task_switch_window) > 5 and self.overwhelm_detector:
            result = self.overwhelm_detector.check_overwhelm(
                self._current_user_id,
                {"task_switches": len(self._task_switch_window)}
            )
            if result.get("level") in ["high", "critical"]:
                await self._surface_finding(ADHDFinding(
                    finding_type="overwhelm_detected",
                    severity=result.get("level"),
                    message=result.get("message", "Rapid task switching detected"),
                    data=result,
                    source_event="task_switched",
                    recommended_actions=result.get("actions", ["Take a breath", "Pick one task"])
                ))
    
    async def _on_git_commit(self, data: Dict[str, Any]):
        """Handle git commit - progress indicator."""
        # Update hyperfocus guard with progress
        if self.hyperfocus_guard:
            self.hyperfocus_guard.record_progress("git_commit")
    
    # ─────────────────────────────────────────────────────────────
    # ADHD State Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    async def _on_energy_changed(self, data: Dict[str, Any]):
        """Handle energy level change."""
        new_energy = data.get("level")
        
        if new_energy == "low":
            await self._surface_finding(ADHDFinding(
                finding_type="energy_low",
                severity="medium",
                message="Energy dropping. Consider simpler tasks or a break.",
                data=data,
                source_event="energy_changed",
                recommended_actions=["Take a break", "Switch to low-complexity task"]
            ))
    
    async def _on_attention_changed(self, data: Dict[str, Any]):
        """Handle attention state change."""
        new_attention = data.get("state")
        
        if new_attention == "hyperfocus" and self.hyperfocus_guard:
            # Start hyperfocus monitoring
            self.hyperfocus_guard.start_monitoring(self._current_user_id)
    
    async def _on_break_refused(self, data: Dict[str, Any]):
        """Handle break refusal - overwhelm/hyperfocus indicator."""
        if self.overwhelm_detector:
            self.overwhelm_detector.record_break_refusal(self._current_user_id)
    
    # ─────────────────────────────────────────────────────────────
    # Calendar Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    async def _on_meeting_started(self, data: Dict[str, Any]):
        """Handle meeting start - social battery drain."""
        # Auto-save context before meeting
        if self.context_preserver:
            await self.context_preserver.save_context(
                self._current_user_id,
                reason="meeting_started"
            )
    
    async def _on_meeting_ended(self, data: Dict[str, Any]):
        """Handle meeting end - offer context restoration."""
        if self.working_memory_support:
            summary = await self.working_memory_support.get_return_summary(
                self._current_user_id
            )
            if summary:
                await self._surface_finding(ADHDFinding(
                    finding_type="context_restored",
                    severity="low",
                    message=f"Meeting ended. {summary}",
                    source_event="meeting_ended"
                ))
    
    # ─────────────────────────────────────────────────────────────
    # Claude Code Event Handlers
    # ─────────────────────────────────────────────────────────────
    
    async def _on_claude_prompt(self, data: Dict[str, Any]):
        """Handle Claude Code prompt - analyze intent."""
        # Intent analysis happens in the hook, but we log here
        signals = data.get("adhd_signals", {})
        
        if signals.get("is_context_switch"):
            # Auto-save breadcrumb
            if self.working_memory_support:
                await self.working_memory_support.save_breadcrumb(
                    self._current_user_id,
                    data.get("prompt_hint", "Context switch in Claude")
                )
    
    async def _on_claude_tool(self, data: Dict[str, Any]):
        """Handle Claude tool execution - track progress."""
        tool_name = data.get("tool")
        
        # Complex tools during low energy warning
        if tool_name in ["thinkdeep", "batch_edit", "refactor"]:
            # Energy check would happen in PreToolUse hook
            pass
    
    async def _on_claude_stop(self, data: Dict[str, Any]):
        """Handle Claude session stop - preserve context."""
        if self.context_preserver:
            await self.context_preserver.save_context(
                self._current_user_id,
                reason="claude_session_stopped"
            )
    
    # ─────────────────────────────────────────────────────────────
    # Output Channel Management
    # ─────────────────────────────────────────────────────────────
    
    async def _surface_finding(self, finding: ADHDFinding):
        """Surface finding through configured output channels."""
        logger.info(f"📢 ADHD Finding: [{finding.severity}] {finding.finding_type}: {finding.message}")
        
        # Publish to EventBus for downstream consumers
        from event_bus import Event
        await self.event_bus.publish(
            "dopemux:adhd-findings",
            Event(
                type=finding.finding_type,
                data={
                    "severity": finding.severity,
                    "message": finding.message,
                    "data": finding.data,
                    "recommended_actions": finding.recommended_actions,
                    "source_event": finding.source_event
                }
            )
        )
        
        # Route to output channels based on severity
        for channel in self.output_channels:
            try:
                await channel.send(finding)
            except Exception as e:
                logger.error(f"❌ Failed to send to channel: {e}")


# Factory function for easy setup
def create_adhd_event_listener(
    event_bus,
    engine
) -> ADHDEventListener:
    """
    Create ADHDEventListener with detectors from engine.
    
    Args:
        event_bus: EventBus instance
        engine: ADHDAccommodationEngine instance
        
    Returns:
        Configured ADHDEventListener
    """
    return ADHDEventListener(
        event_bus=event_bus,
        hyperfocus_guard=getattr(engine, 'hyperfocus_guard', None),
        overwhelm_detector=getattr(engine, 'overwhelm_detector', None),
        procrastination_detector=getattr(engine, 'procrastination_detector', None),
        working_memory_support=getattr(engine, 'working_memory_support', None),
        context_preserver=getattr(engine, 'context_preserver', None),
        activity_tracker=getattr(engine, 'activity_tracker', None)
    )
