"""
External Activity Integration for ADHD Engine

Integrates external sources into the ADHD Event system:
1. Desktop Commander - Window/app switches, workspace changes
2. Calendar MCP - Meeting start/end, schedule events
3. System idle detection - Breaks, away detection

Emits events to EventBus for implicit ADHD detection.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import httpx

logger = logging.getLogger(__name__)


@dataclass
class WindowActivity:
    """Tracks window/app activity"""
    app_name: str
    window_title: str
    timestamp: datetime
    duration_seconds: int = 0


@dataclass
class MeetingEvent:
    """Calendar meeting event"""
    title: str
    start_time: datetime
    end_time: datetime
    meeting_type: str = "video"  # video, audio, in_person
    attendees: int = 2
    is_recurring: bool = False


class DesktopActivityMonitor:
    """
    Monitors Desktop Commander for window switches and emits ADHD events.
    
    Integrates with:
    - Desktop Commander MCP (localhost:3012)
    - EventBus for ADHD event emission
    
    Detects:
    - Window switches (context change detection)
    - App focus patterns (distraction tracking)
    - Workspace changes (project switching)
    - Idle periods (break detection)
    """
    
    def __init__(
        self,
        event_bus,
        desktop_commander_url: str = "http://localhost:3012",
        poll_interval: int = 5,
        emit_events: bool = True
    ):
        self.event_bus = event_bus
        self.desktop_commander_url = desktop_commander_url
        self.poll_interval = poll_interval
        self.emit_events = emit_events
        
        # State tracking
        self.current_app: Optional[str] = None
        self.current_window: Optional[str] = None
        self.last_activity: datetime = datetime.now(timezone.utc)
        self.activity_history: List[WindowActivity] = []
        
        # Pattern tracking
        self.switch_count_last_hour: int = 0
        self.last_switch_reset: datetime = datetime.now(timezone.utc)
        
        # Config thresholds
        self.rapid_switch_threshold = 10  # switches/hour for overwhelm
        self.idle_threshold_seconds = 180  # 3 min = idle
        self.distraction_apps = {
            "Slack", "Discord", "Twitter", "X", "Messages",
            "Mail", "Safari", "Chrome", "Firefox"
        }
        self.work_apps = {
            "Code", "Terminal", "iTerm", "Cursor", "PyCharm",
            "IntelliJ", "VS Code", "Xcode"
        }
        
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start monitoring Desktop Commander"""
        if self._running:
            return
        
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("🖥️ Desktop Activity Monitor started")
    
    async def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("🖥️ Desktop Activity Monitor stopped")
    
    async def _poll_loop(self):
        """Poll Desktop Commander for window changes"""
        while self._running:
            try:
                await self._check_window_state()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.warning(f"Desktop Commander poll error: {e}")
                await asyncio.sleep(self.poll_interval * 2)
    
    async def _check_window_state(self):
        """Check current window state from Desktop Commander"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Query Desktop Commander for active window
                # API format depends on Desktop Commander implementation
                resp = await client.post(
                    f"{self.desktop_commander_url}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "list_resources",
                        "params": {},
                        "id": 1
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Extract current window info
                    # This depends on Desktop Commander's actual response format
                    await self._process_window_state(data)
                    
        except httpx.ConnectError:
            # Desktop Commander not running - fail silently
            pass
        except Exception as e:
            logger.debug(f"Desktop Commander query failed: {e}")
    
    async def _process_window_state(self, data: dict):
        """Process window state and detect changes"""
        # Extract app/window from Desktop Commander response
        # This is a placeholder - actual format depends on Desktop Commander
        result = data.get("result", {})
        
        # Try to extract active window info
        new_app = result.get("active_app", self.current_app)
        new_window = result.get("active_window", self.current_window)
        
        now = datetime.now(timezone.utc)
        
        # Detect window switch
        if new_app != self.current_app or new_window != self.current_window:
            await self._on_window_switch(
                from_app=self.current_app,
                to_app=new_app,
                from_window=self.current_window,
                to_window=new_window
            )
            
            # Update state
            self.current_app = new_app
            self.current_window = new_window
            self.last_activity = now
        
        # Detect idle
        idle_seconds = (now - self.last_activity).total_seconds()
        if idle_seconds > self.idle_threshold_seconds:
            await self._on_idle_detected(idle_seconds)
    
    async def _on_window_switch(
        self,
        from_app: Optional[str],
        to_app: Optional[str],
        from_window: Optional[str],
        to_window: Optional[str]
    ):
        """Handle window switch event"""
        if not self.emit_events or not self.event_bus:
            return
        
        now = datetime.now(timezone.utc)
        
        # Reset hourly counter if needed
        if (now - self.last_switch_reset).total_seconds() > 3600:
            self.switch_count_last_hour = 0
            self.last_switch_reset = now
        
        self.switch_count_last_hour += 1
        
        # Determine switch type
        is_distraction = to_app in self.distraction_apps
        is_leaving_work = from_app in self.work_apps and to_app not in self.work_apps
        is_returning_work = from_app not in self.work_apps and to_app in self.work_apps
        
        # Store in history
        self.activity_history.append(WindowActivity(
            app_name=to_app or "unknown",
            window_title=to_window or "",
            timestamp=now
        ))
        
        # Keep last 50 activities
        self.activity_history = self.activity_history[-50:]
        
        # Emit event
        try:
            from event_bus import Event, EventType
            
            event = Event(
                type=EventType.WINDOW_SWITCHED,
                data={
                    "from_app": from_app,
                    "to_app": to_app,
                    "from_window": from_window,
                    "to_window": to_window,
                    "is_distraction": is_distraction,
                    "is_leaving_work": is_leaving_work,
                    "is_returning_work": is_returning_work,
                    "switches_this_hour": self.switch_count_last_hour,
                    "rapid_switching": self.switch_count_last_hour > self.rapid_switch_threshold
                },
                source="desktop_activity_monitor"
            )
            
            await self.event_bus.publish("dopemux:events", event)
            
            logger.debug(f"Window switch: {from_app} → {to_app}")
            
            # Emit overwhelm warning if rapid switching
            if self.switch_count_last_hour > self.rapid_switch_threshold:
                overwhelm_event = Event(
                    type=EventType.OVERWHELM_DETECTED,
                    data={
                        "trigger": "rapid_window_switching",
                        "switches_per_hour": self.switch_count_last_hour,
                        "threshold": self.rapid_switch_threshold
                    },
                    source="desktop_activity_monitor"
                )
                await self.event_bus.publish("dopemux:events", overwhelm_event)
                
        except Exception as e:
            logger.warning(f"Failed to emit window switch event: {e}")
    
    async def _on_idle_detected(self, idle_seconds: float):
        """Handle idle detection"""
        if not self.emit_events or not self.event_bus:
            return
        
        try:
            from event_bus import Event, EventType
            
            event = Event(
                type=EventType.IDLE_DETECTED,
                data={
                    "idle_seconds": idle_seconds,
                    "idle_minutes": idle_seconds / 60,
                    "last_active_app": self.current_app,
                    "is_break": idle_seconds > 300  # 5+ min = break
                },
                source="desktop_activity_monitor"
            )
            
            await self.event_bus.publish("dopemux:events", event)
            
        except Exception as e:
            logger.warning(f"Failed to emit idle event: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get activity metrics"""
        now = datetime.now(timezone.utc)
        
        # Calculate work vs distraction time
        work_activities = sum(
            1 for a in self.activity_history
            if a.app_name in self.work_apps
        )
        distraction_activities = sum(
            1 for a in self.activity_history
            if a.app_name in self.distraction_apps
        )
        
        return {
            "current_app": self.current_app,
            "current_window": self.current_window,
            "switches_this_hour": self.switch_count_last_hour,
            "rapid_switching": self.switch_count_last_hour > self.rapid_switch_threshold,
            "recent_work_activities": work_activities,
            "recent_distraction_activities": distraction_activities,
            "activity_history_size": len(self.activity_history)
        }


class CalendarIntegration:
    """
    Integrates calendar events into ADHD system.
    
    Features:
    - Meeting start/end detection
    - Social battery tracking
    - Pre-meeting warnings (energy prep)
    - Post-meeting recovery suggestions
    
    Supports:
    - Apple Calendar (via osascript)
    - Google Calendar (via API)
    - Calendar MCP (when available)
    """
    
    def __init__(
        self,
        event_bus,
        calendar_source: str = "apple",  # apple, google, mcp
        poll_interval: int = 60,
        emit_events: bool = True
    ):
        self.event_bus = event_bus
        self.calendar_source = calendar_source
        self.poll_interval = poll_interval
        self.emit_events = emit_events
        
        # State
        self.current_meeting: Optional[MeetingEvent] = None
        self.upcoming_meetings: List[MeetingEvent] = []
        self.meetings_today: int = 0
        self.meeting_hours_today: float = 0.0
        
        # Social battery tracking
        self.social_battery: float = 100.0  # 0-100
        self.last_meeting_end: Optional[datetime] = None
        
        # Thresholds
        self.pre_meeting_warning_minutes = 5
        self.social_battery_per_meeting_hour = 15  # Drain per hour
        self.recovery_per_hour_solo = 10  # Recovery per hour alone
        
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start calendar monitoring"""
        if self._running:
            return
        
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("📅 Calendar Integration started")
    
    async def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("📅 Calendar Integration stopped")
    
    async def _poll_loop(self):
        """Poll calendar for events"""
        while self._running:
            try:
                await self._check_calendar()
                await self._update_social_battery()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.warning(f"Calendar poll error: {e}")
                await asyncio.sleep(self.poll_interval * 2)
    
    async def _check_calendar(self):
        """Check calendar for current and upcoming events"""
        now = datetime.now(timezone.utc)
        
        if self.calendar_source == "apple":
            meetings = await self._get_apple_calendar_events()
        elif self.calendar_source == "google":
            meetings = await self._get_google_calendar_events()
        elif self.calendar_source == "mcp":
            meetings = await self._get_mcp_calendar_events()
        else:
            meetings = []
        
        self.upcoming_meetings = meetings
        
        # Check for current meeting
        for meeting in meetings:
            if meeting.start_time <= now <= meeting.end_time:
                if self.current_meeting != meeting:
                    await self._on_meeting_started(meeting)
                    self.current_meeting = meeting
                break
        else:
            if self.current_meeting:
                await self._on_meeting_ended(self.current_meeting)
                self.current_meeting = None
        
        # Check for upcoming meeting warnings
        for meeting in meetings:
            minutes_until = (meeting.start_time - now).total_seconds() / 60
            if 0 < minutes_until <= self.pre_meeting_warning_minutes:
                await self._on_meeting_approaching(meeting, minutes_until)
    
    async def _get_apple_calendar_events(self) -> List[MeetingEvent]:
        """Get events from Apple Calendar via osascript"""
        try:
            import subprocess
            
            # AppleScript to get today's events
            script = '''
            tell application "Calendar"
                set today to current date
                set tomorrow to today + 1 * days
                set allEvents to {}
                
                repeat with cal in calendars
                    set calEvents to (every event of cal whose start date >= today and start date < tomorrow)
                    repeat with evt in calEvents
                        set end of allEvents to {summary of evt, start date of evt, end date of evt}
                    end repeat
                end repeat
                
                return allEvents
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse AppleScript output
                # This is simplified - actual parsing would be more complex
                return []
            
        except Exception as e:
            logger.debug(f"Apple Calendar query failed: {e}")
        
        return []
    
    async def _get_google_calendar_events(self) -> List[MeetingEvent]:
        """Get events from Google Calendar API"""
        # Placeholder - would require OAuth setup
        return []
    
    async def _get_mcp_calendar_events(self) -> List[MeetingEvent]:
        """Get events from Calendar MCP server"""
        # Placeholder - when Calendar MCP is available
        return []
    
    async def _update_social_battery(self):
        """Update social battery based on meeting time"""
        now = datetime.now(timezone.utc)
        
        # If in meeting, drain battery
        if self.current_meeting:
            drain = self.social_battery_per_meeting_hour / 60  # Per minute
            self.social_battery = max(0, self.social_battery - drain)
        
        # If not in meeting and had one recently, recover slowly
        elif self.last_meeting_end:
            recovery_minutes = (now - self.last_meeting_end).total_seconds() / 60
            recovery = (self.recovery_per_hour_solo / 60) * recovery_minutes
            self.social_battery = min(100, self.social_battery + recovery)
    
    async def _on_meeting_started(self, meeting: MeetingEvent):
        """Handle meeting start"""
        if not self.emit_events or not self.event_bus:
            return
        
        self.meetings_today += 1
        
        try:
            from event_bus import Event, EventType
            
            event = Event(
                type=EventType.MEETING_STARTED,
                data={
                    "title": meeting.title,
                    "meeting_type": meeting.meeting_type,
                    "attendees": meeting.attendees,
                    "duration_minutes": (meeting.end_time - meeting.start_time).total_seconds() / 60,
                    "social_battery_before": self.social_battery,
                    "meetings_today": self.meetings_today
                },
                source="calendar_integration"
            )
            
            await self.event_bus.publish("dopemux:events", event)
            logger.info(f"📅 Meeting started: {meeting.title}")
            
        except Exception as e:
            logger.warning(f"Failed to emit meeting start event: {e}")
    
    async def _on_meeting_ended(self, meeting: MeetingEvent):
        """Handle meeting end"""
        if not self.emit_events or not self.event_bus:
            return
        
        self.last_meeting_end = datetime.now(timezone.utc)
        duration_minutes = (meeting.end_time - meeting.start_time).total_seconds() / 60
        self.meeting_hours_today += duration_minutes / 60
        
        try:
            from event_bus import Event, EventType
            
            # Determine recovery suggestion based on social battery
            if self.social_battery < 20:
                recovery_suggestion = "Take a 15-minute solo break - social battery critically low"
            elif self.social_battery < 50:
                recovery_suggestion = "Consider a 5-minute break before next task"
            else:
                recovery_suggestion = None
            
            event = Event(
                type=EventType.MEETING_ENDED,
                data={
                    "title": meeting.title,
                    "duration_minutes": duration_minutes,
                    "social_battery_after": self.social_battery,
                    "meeting_hours_today": self.meeting_hours_today,
                    "recovery_suggestion": recovery_suggestion
                },
                source="calendar_integration"
            )
            
            await self.event_bus.publish("dopemux:events", event)
            logger.info(f"📅 Meeting ended: {meeting.title}")
            
            # Emit social battery warning if low
            if self.social_battery < 30:
                battery_event = Event(
                    type=EventType.SOCIAL_BATTERY_LOW,
                    data={
                        "social_battery": self.social_battery,
                        "meeting_hours_today": self.meeting_hours_today,
                        "recovery_time_needed_minutes": (50 - self.social_battery) * 6
                    },
                    source="calendar_integration"
                )
                await self.event_bus.publish("dopemux:events", battery_event)
                
        except Exception as e:
            logger.warning(f"Failed to emit meeting end event: {e}")
    
    async def _on_meeting_approaching(self, meeting: MeetingEvent, minutes_until: float):
        """Handle approaching meeting warning"""
        if not self.emit_events or not self.event_bus:
            return
        
        try:
            from event_bus import Event
            
            # Determine preparation suggestion based on current state
            if self.social_battery < 30:
                prep_suggestion = "Low social battery - consider declining or shortening this meeting"
            elif minutes_until < 2:
                prep_suggestion = "Meeting starting soon - save your work"
            else:
                prep_suggestion = f"Meeting in {int(minutes_until)} minutes"
            
            event = Event(
                type="meeting.approaching",  # Custom event
                data={
                    "title": meeting.title,
                    "minutes_until": minutes_until,
                    "social_battery": self.social_battery,
                    "preparation_suggestion": prep_suggestion
                },
                source="calendar_integration"
            )
            
            await self.event_bus.publish("dopemux:events", event)
            
        except Exception as e:
            logger.warning(f"Failed to emit meeting approaching event: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get calendar metrics"""
        return {
            "in_meeting": self.current_meeting is not None,
            "current_meeting": self.current_meeting.title if self.current_meeting else None,
            "meetings_today": self.meetings_today,
            "meeting_hours_today": round(self.meeting_hours_today, 1),
            "social_battery": round(self.social_battery, 1),
            "upcoming_meetings_count": len(self.upcoming_meetings)
        }


class ExternalActivityManager:
    """
    Manages all external activity integrations for ADHD Engine.
    
    Coordinates:
    - Desktop Commander (window switches)
    - Calendar (meetings, social battery)
    - Future: Browser MCP, Spotify, etc.
    """
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        
        # Initialize integrations
        self.desktop_monitor = DesktopActivityMonitor(
            event_bus=event_bus,
            desktop_commander_url=os.getenv("DESKTOP_COMMANDER_URL", "http://localhost:3012")
        )
        
        self.calendar = CalendarIntegration(
            event_bus=event_bus,
            calendar_source=os.getenv("CALENDAR_SOURCE", "apple")
        )
        
        self._running = False
    
    async def start(self):
        """Start all integrations"""
        if self._running:
            return
        
        self._running = True
        
        await self.desktop_monitor.start()
        await self.calendar.start()
        
        logger.info("🔗 External Activity Manager started")
    
    async def stop(self):
        """Stop all integrations"""
        self._running = False
        
        await self.desktop_monitor.stop()
        await self.calendar.stop()
        
        logger.info("🔗 External Activity Manager stopped")
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics from all integrations"""
        return {
            "desktop": self.desktop_monitor.get_metrics(),
            "calendar": self.calendar.get_metrics(),
            "running": self._running
        }


def create_external_activity_manager(event_bus) -> ExternalActivityManager:
    """Factory function to create ExternalActivityManager"""
    return ExternalActivityManager(event_bus)
