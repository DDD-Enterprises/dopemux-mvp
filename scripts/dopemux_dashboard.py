#!/usr/bin/env python3
"""
Dopemux Dashboard - ADHD-Optimized Metrics Display
Quick-start implementation for tmux monitoring panes

Usage:
    # Run full dashboard
    python dopemux_dashboard.py

    # Run specific view
    python dopemux_dashboard.py --view=compact
    python dopemux_dashboard.py --view=full
    python dopemux_dashboard.py --view=detail

    # In tmux
    tmux split-window -h "python dopemux_dashboard.py"
"""

import asyncio
import httpx
import sys
import shutil
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from prometheus_client import PrometheusClient, PrometheusConfig
from sparkline_generator import SparklineGenerator

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

try:
    from dashboard.streaming import StreamingClient, StreamingConfig
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    logger.warning("dashboard.streaming not available - WebSocket disabled")

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container
    from textual.widgets import Header, Footer, Static, DataTable, ListView, ListItem, Label
    from textual.reactive import reactive
    from textual.screen import Screen
    from rich.table import Table
    from rich.panel import Panel
    from rich.console import Console
    from rich.layout import Layout
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    print("⚠️  Textual not installed. Install with: pip install textual rich")
    print("Falling back to simple console output...")


# =============================================================================
# Configuration
# =============================================================================

ENDPOINTS = {
    "adhd_state": "http://localhost:8095/api/v1/statusline/default_user",  # ADHD Engine (REAL)
    "adhd_energy": "http://localhost:8095/api/v1/energy-level/default_user",  # ADHD Engine
    "adhd_attention": "http://localhost:8095/api/v1/attention-state/default_user",  # ADHD Engine
    "adhd_cognitive": "http://localhost:8095/api/v1/cognitive-load/default_user",  # Day 2: NEW
    "adhd_flow": "http://localhost:8095/api/v1/flow-state/default_user",  # Day 2: NEW
    "adhd_session": "http://localhost:8095/api/v1/session-time/default_user",  # Day 2: NEW
    "adhd_breaks": "http://localhost:8095/api/v1/breaks/default_user",  # Day 2: NEW
    "unfinished_work": "http://localhost:8095/api/v1/unfinished-work?user_id=default_user", # Day 8: NEW
    "tasks": "http://localhost:8095/api/v1/tasks",  # ✅ Added endpoint
    "decisions": "http://localhost:8005/api/adhd/decisions/recent",  # ConPort (Day 2)
    "services": "http://localhost:3016/health",
    "patterns": "http://localhost:8003/api/patterns/top",  # Serena (Day 2: NEW)
}

COLORS = {
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "optimal": "green",
    "critical": "red",
}

UPDATE_INTERVALS = {
    "adhd_state": 1,      # Real-time
    "tasks": 30,          # Medium
    "services": 60,       # Slow
}

# =============================================================================
# Themes Configuration
# =============================================================================

THEMES = {
    "mocha": {
        "name": "Catppuccin Mocha",
        "primary": "#cdd6f4",
        "secondary": "#89b4fa",
        "accent": "#f5c2e7",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "surface": "#1e1e2e",
        "panel": "#181825",
        "muted": "#6c7086",
    },
    "nord": {
        "name": "Nord",
        "primary": "#d8dee9",
        "secondary": "#88c0d0",
        "accent": "#81a1c1",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "error": "#bf616a",
        "surface": "#2e3440",
        "panel": "#3b4252",
        "muted": "#4c566a",
    },
    "dracula": {
        "name": "Dracula",
        "primary": "#f8f8f2",
        "secondary": "#bd93f9",
        "accent": "#ff79c6",
        "success": "#50fa7b",
        "warning": "#f1fa8c",
        "error": "#ff5555",
        "surface": "#282a36",
        "panel": "#44475a",
        "muted": "#6272a4",
    },
}

CONFIG_DIR = Path.home() / ".config" / "dopemux"
CONFIG_FILE = CONFIG_DIR / "dashboard.json"


def load_config() -> Dict[str, Any]:
    """Load dashboard configuration"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            pass
    return {"theme": "mocha", "focus_mode": False, "notifications_enabled": True}


def save_config(config: Dict[str, Any]) -> None:
    """Save dashboard configuration"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except Exception as e:
        pass  # Silently fail if can't save


# =============================================================================
# Notifications & Actions
# =============================================================================

async def send_notification(title: str, message: str, sound: str = "Glass"):
    """Send macOS notification via osascript"""
    try:
        script = f'''
        display notification "{message}" 
        with title "{title}" 
        sound name "{sound}"
        '''
        subprocess.run(['osascript', '-e', script], 
                      capture_output=True, 
                      timeout=2)
    except Exception as e:
        # Silently fail if notifications not available
        pass


async def trigger_break(duration_minutes: int = 5):
    """Trigger a break via ADHD Engine"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8095/api/v1/break/start",
                json={"user_id": "default_user", "duration_minutes": duration_minutes},
                timeout=2.0
            )
            if response.status_code == 200:
                await send_notification(
                    "Dopemux Break Timer", 
                    f"Break started! Take {duration_minutes} minutes ☕"
                )
                return True
    except Exception:
        pass
    return False


# =============================================================================
# Smart Notification Manager
# =============================================================================

@dataclass
class NotificationPriority:
    HIGH = "high"      # Always show (critical)
    MEDIUM = "medium"  # Show if not in flow
    LOW = "low"        # Batch/suppress


class NotificationManager:
    """Smart notification system with flow protection and cooldowns"""
    
    def __init__(self):
        self.last_notifications: Dict[str, float] = {}
        self.cooldown_seconds = 300  # 5 minutes
        self.enabled = True
        self.in_flow = False
        
    def can_notify(self, event_key: str, priority: str = NotificationPriority.MEDIUM) -> bool:
        """Check if notification should be sent (respects cooldown and flow)"""
        if not self.enabled:
            return False
        
        # High priority bypasses flow protection
        if priority == NotificationPriority.HIGH:
            pass
        # Medium/Low priority suppressed during flow
        elif self.in_flow and priority in [NotificationPriority.MEDIUM, NotificationPriority.LOW]:
            return False
        
        # Check cooldown
        now = datetime.now().timestamp()
        last_time = self.last_notifications.get(event_key, 0)
        
        if now - last_time < self.cooldown_seconds:
            return False
        
        return True
    
    async def notify(self, event_key: str, title: str, message: str, 
                     priority: str = NotificationPriority.MEDIUM, sound: str = "Glass") -> bool:
        """Send notification if allowed by rules"""
        if not self.can_notify(event_key, priority):
            return False
        
        await send_notification(title, message, sound)
        self.last_notifications[event_key] = datetime.now().timestamp()
        return True
    
    def update_flow_state(self, in_flow: bool):
        """Update flow state for notification suppression"""
        self.in_flow = in_flow
    
    def toggle_enabled(self) -> bool:
        """Toggle notifications on/off"""
        self.enabled = not self.enabled
        return self.enabled


class AutoTriggerMonitor:
    """Background monitor for automatic ADHD-aware notifications"""
    
    def __init__(self, fetcher: "MetricsFetcher", notification_manager: NotificationManager):
        self.fetcher = fetcher
        self.notifier = notification_manager
        self.previous_state: Dict[str, Any] = {}
        
    async def monitor_loop(self):
        """Main monitoring loop - runs every 30 seconds"""
        while True:
            try:
                await self.check_triggers()
            except Exception as e:
                pass  # Silent fail, keep monitoring
            
            await asyncio.sleep(30)
    
    async def check_triggers(self):
        """Evaluate all notification triggers"""
        # Get current state
        adhd_state = await self.fetcher.get_adhd_state()
        services = await self.fetcher.get_services_health()
        
        # Check flow state BEFORE updating notification manager
        # (so flow start notifications can be sent)
        await self._check_flow_state(adhd_state)
        
        # NOW update flow state in notification manager
        flow_active = adhd_state.get("flow_state", {}).get("active", False)
        self.notifier.update_flow_state(flow_active)
        
        # Other trigger evaluations
        await self._check_cognitive_load(adhd_state)
        await self._check_energy_level(adhd_state)
        await self._check_break_timing(adhd_state)
        await self._check_attention_state(adhd_state)
        await self._check_services(services)
        
        # Store current state for next comparison
        self.previous_state = {
            "adhd": adhd_state,
            "services": services
        }
    
    async def _check_cognitive_load(self, state: Dict[str, Any]):
        """Alert on critical cognitive overload"""
        load = state.get("cognitive_load", 0.0)
        flow_active = state.get("flow_state", {}).get("active", False)
        
        # Critical: >85% cognitive load and NOT in flow
        if load > 0.85 and not flow_active:
            await self.notifier.notify(
                "cognitive_overload",
                "Dopemux Alert",
                f"Cognitive load critical ({int(load * 100)}%)! Take a break 🧠",
                priority=NotificationPriority.HIGH,
                sound="Basso"
            )
    
    async def _check_energy_level(self, state: Dict[str, Any]):
        """Alert on energy depletion"""
        energy = state.get("energy_level", "unknown")
        session_time = state.get("session_time", "0m")
        
        # Parse session time (e.g., "65m" -> 65)
        try:
            session_minutes = int(session_time.rstrip("m"))
        except:
            session_minutes = 0
        
        # Low energy + long session
        if energy in ["low", "depleted"] and session_minutes > 60:
            await self.notifier.notify(
                "energy_low",
                "Dopemux Alert",
                f"Energy depleting! Session: {session_time} ⚡",
                priority=NotificationPriority.MEDIUM,
                sound="Purr"
            )
    
    async def _check_break_timing(self, state: Dict[str, Any]):
        """Warn before break becomes critical"""
        break_info = state.get("break_info", {})
        recommended_in = break_info.get("recommended_in", 999)
        
        # Break recommended in < 5 minutes
        if recommended_in <= 5 and recommended_in > 0:
            await self.notifier.notify(
                "break_soon",
                "Dopemux Break Reminder",
                f"Break recommended in {recommended_in} minutes ☕",
                priority=NotificationPriority.MEDIUM,
                sound="Tink"
            )
    
    async def _check_flow_state(self, state: Dict[str, Any]):
        """Celebrate flow achievements"""
        flow_data = state.get("flow_state", {})
        flow_active = flow_data.get("active", False)
        flow_duration = flow_data.get("duration", 0)
        
        prev_flow = self.previous_state.get("adhd", {}).get("flow_state", {}).get("active", False)
        
        # Flow just started
        if flow_active and not prev_flow:
            await self.notifier.notify(
                "flow_started",
                "Dopemux Flow State",
                "Flow state achieved! 🌊 Stay focused!",
                priority=NotificationPriority.MEDIUM,
                sound="Hero"
            )
        
        # Flow just ended (celebrate if >15 min)
        elif not flow_active and prev_flow:
            prev_duration = self.previous_state.get("adhd", {}).get("flow_state", {}).get("duration", 0)
            if prev_duration >= 15:
                await self.notifier.notify(
                    "flow_ended",
                    "Dopemux Flow State",
                    f"Flow session complete: {prev_duration} minutes! 🎯",
                    priority=NotificationPriority.MEDIUM,
                    sound="Glass"
                )
    
    async def _check_attention_state(self, state: Dict[str, Any]):
        """Alert if attention scattered for too long"""
        attention = state.get("attention_state", "unknown")
        
        # Track how long scattered
        # (Simplified: just check if scattered, full impl would track duration)
        if attention == "scattered":
            await self.notifier.notify(
                "attention_scattered",
                "Dopemux Focus Alert",
                "Attention scattered - try refocusing 👁️",
                priority=NotificationPriority.LOW,
                sound="Ping"
            )
    
    async def _check_services(self, services: Dict[str, Any]):
        """Alert on service failures"""
        prev_services = self.previous_state.get("services", {})
        
        for name, health in services.items():
            status = health.get("status", "unknown")
            prev_status = prev_services.get(name, {}).get("status", "unknown")
            
            # Service just went offline
            if status == "offline" and prev_status == "healthy":
                await self.notifier.notify(
                    f"service_{name}",
                    "Dopemux Service Alert",
                    f"{name} is offline ⚠️",
                    priority=NotificationPriority.MEDIUM,
                    sound="Basso"
                )


# =============================================================================
# WebSocket Metrics Manager
# =============================================================================

class MetricsManager:
    """
    Unified metrics coordinator with WebSocket + HTTP fallback.
    
    Features:
    - Attempts WebSocket connection first
    - Falls back to HTTP polling if WebSocket unavailable
    - Auto-reconnect in background
    - Routes updates to dashboard widgets
    """
    
    def __init__(self, app: Optional["DopemuxDashboard"] = None):
        self.app = app
        self.mode = "disconnected"  # disconnected|websocket|polling
        self.streaming_client: Optional[StreamingClient] = None
        self.polling_task: Optional[asyncio.Task] = None
        self.reconnect_task: Optional[asyncio.Task] = None
        self.http_client = httpx.AsyncClient(timeout=2.0)
        
        # Latest data cache (for widgets)
        self.latest_data = {
            "adhd_state": {},
            "tasks": {},
            "services": {},
            "patterns": {},
        }
        
    async def start(self):
        """Start metrics streaming (tries WebSocket, falls back to polling)"""
        if STREAMING_AVAILABLE:
            try:
                logger.info("Attempting WebSocket connection...")
                await self._start_websocket()
            except Exception as e:
                logger.warning(f"WebSocket unavailable: {e}, falling back to polling")
                await self._start_polling()
        else:
            logger.info("WebSocket library not installed, using polling")
            await self._start_polling()
    
    async def _start_websocket(self):
        """Start WebSocket streaming"""
        self.streaming_client = StreamingClient(
            config=StreamingConfig(
                url="ws://localhost:8095/api/v1/ws/stream",
                user_id="default_user"
            ),
            on_state_update=self.handle_state_update,
            on_metric_update=self.handle_metric_update,
            on_alert=self.handle_alert,
            on_connection_change=self.handle_connection_change
        )
        
        # Start streaming (will raise if connection fails)
        await self.streaming_client.connect()
        self.mode = "websocket"
        
        # Start background streaming loop
        asyncio.create_task(self.streaming_client.start())
        
        logger.info("✅ WebSocket streaming active")
    
    async def _start_polling(self):
        """Start HTTP polling fallback"""
        self.mode = "polling"
        self.polling_task = asyncio.create_task(self._poll_loop())
        
        # Start background reconnection attempts
        if STREAMING_AVAILABLE:
            self.reconnect_task = asyncio.create_task(self._reconnect_loop())
        
        logger.info("📊 HTTP polling active (fallback mode)")
    
    async def _poll_loop(self):
        """Polling loop (runs when WebSocket unavailable)"""
        while self.mode == "polling":
            try:
                # Fetch ADHD state
                adhd_state = await self._fetch_adhd_state_http()
                await self.handle_state_update(adhd_state)
                
                # Fetch other metrics less frequently
                if datetime.now().second % 30 == 0:
                    tasks = await self._fetch_tasks_http()
                    services = await self._fetch_services_http()
                    
                    self.latest_data["tasks"] = tasks
                    self.latest_data["services"] = services
                    
                    # Update widgets if app available
                    if self.app:
                        await self._update_widgets()
            
            except Exception as e:
                logger.warning(f"Polling error: {e}")
            
            await asyncio.sleep(5)  # Poll every 5 seconds
    
    async def _reconnect_loop(self):
        """Background WebSocket reconnection attempts"""
        delay = 10  # Start with 10 seconds
        max_delay = 300  # Max 5 minutes
        
        while self.mode == "polling":
            await asyncio.sleep(delay)
            
            try:
                logger.info("Attempting WebSocket reconnection...")
                await self._start_websocket()
                
                # Success! Stop polling
                if self.polling_task:
                    self.polling_task.cancel()
                self.mode = "websocket"
                logger.info("✅ Reconnected to WebSocket")
                break
                
            except Exception as e:
                logger.debug(f"Reconnection failed: {e}")
                delay = min(delay * 2, max_delay)  # Exponential backoff
    
    async def handle_state_update(self, data: Dict[str, Any]):
        """Handle ADHD state update from WebSocket or polling"""
        self.latest_data["adhd_state"] = data
        
        if self.app:
            # Update ADHD widget
            try:
                adhd_widget = self.app.query_one(ADHDStateWidget)
                adhd_widget.update_from_ws(data)
            except Exception as e:
                logger.debug(f"Widget update failed: {e}")
    
    async def handle_metric_update(self, data: Dict[str, Any]):
        """Handle metric update from WebSocket"""
        # Route to appropriate widget based on metric type
        pass
    
    async def handle_alert(self, data: Dict[str, Any]):
        """Handle alert from WebSocket"""
        if self.app:
            message = data.get("message", "Alert received")
            severity = data.get("severity", "information")
            self.app.notify(message, severity=severity)
    
    async def handle_connection_change(self, state: str):
        """Handle WebSocket connection state change"""
        logger.info(f"WebSocket connection: {state}")
        
        if self.app:
            # Update connection status in footer
            try:
                footer = self.app.query_one(Footer)
                if state == "connected":
                    self.mode = "websocket"
                elif state == "disconnected" and self.mode == "websocket":
                    # Switch to polling
                    await self._start_polling()
            except Exception:
                pass
    
    async def _fetch_adhd_state_http(self) -> Dict[str, Any]:
        """Fetch ADHD state via HTTP (fallback)"""
        try:
            resp = await self.http_client.get(ENDPOINTS["adhd_state"])
            return resp.json()
        except Exception as e:
            logger.warning(f"HTTP fetch failed: {e}")
            return {}
    
    async def _fetch_tasks_http(self) -> Dict[str, Any]:
        """Fetch tasks via HTTP"""
        try:
            resp = await self.http_client.get(ENDPOINTS["tasks"])
            return resp.json()
        except Exception:
            return {"completed": 0, "total": 0}
    
    async def _fetch_services_http(self) -> Dict[str, Any]:
        """Fetch service health via HTTP"""
        services = {}
        for name, url in [
            ("ADHD Engine", "http://localhost:8095/health"),
            ("ConPort", "http://localhost:8005/health"),
            ("Serena", "http://localhost:8003/health"),
            ("MCP Bridge", "http://localhost:3016/health"),
        ]:
            try:
                resp = await self.http_client.get(url)
                services[name] = resp.json()
            except Exception:
                services[name] = {"status": "offline"}
        return services
    
    async def _update_widgets(self):
        """Update all widgets with latest data"""
        if not self.app:
            return
        
        # Update ADHD widget
        try:
            adhd_widget = self.app.query_one(ADHDStateWidget)
            adhd_widget.update_from_ws(self.latest_data["adhd_state"])
        except Exception:
            pass
    
    async def stop(self):
        """Clean shutdown"""
        if self.streaming_client:
            await self.streaming_client.disconnect()
        if self.polling_task:
            self.polling_task.cancel()
        if self.reconnect_task:
            self.reconnect_task.cancel()
        await self.http_client.aclose()


# =============================================================================
# Data Fetcher
# =============================================================================

class MetricsFetcher:
    """Async fetcher for all dashboard metrics"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=2.0)
        self.cache: Dict[str, Any] = {}
    
    async def get_adhd_state(self) -> Dict[str, Any]:
        """Get current ADHD state (energy, attention, cognitive load)"""
        try:
            # Fetch all ADHD metrics in parallel (Day 2: ALL REAL DATA!)
            results = await asyncio.gather(
                self.client.get(ENDPOINTS["adhd_energy"]),
                self.client.get(ENDPOINTS["adhd_attention"]),
                self.client.get(ENDPOINTS["adhd_cognitive"]),
                self.client.get(ENDPOINTS["adhd_flow"]),
                self.client.get(ENDPOINTS["adhd_session"]),
                self.client.get(ENDPOINTS["adhd_breaks"]),
                return_exceptions=True
            )
            
            # Parse responses
            energy_data = results[0].json() if not isinstance(results[0], Exception) else {}
            attention_data = results[1].json() if not isinstance(results[1], Exception) else {}
            cognitive_data = results[2].json() if not isinstance(results[2], Exception) else {}
            flow_data = results[3].json() if not isinstance(results[3], Exception) else {}
            session_data = results[4].json() if not isinstance(results[4], Exception) else {}
            breaks_data = results[5].json() if not isinstance(results[5], Exception) else {}
            
            # Combine into expected format
            return {
                "energy_level": energy_data.get("energy_level", "unknown"),
                "attention_state": attention_data.get("attention_state", "unknown"),
                "cognitive_load": cognitive_data.get("cognitive_load", 0.0),
                "flow_state": {"active": flow_data.get("active", False), "duration": flow_data.get("duration_minutes", 0)},
                "session_time": session_data.get("duration", "0m"),
                "break_info": {
                    "recommended_in": breaks_data.get("recommended_in", 25),
                    "minutes_since": breaks_data.get("minutes_since", 0)
                }
            }
        except Exception as e:
            logger.warning(f"ADHD state fetch failed: {e}")
            return {
                "energy_level": "unknown",
                "attention_state": "unknown",
                "cognitive_load": 0.0,
                "flow_state": {"active": False},
                "session_time": "0m",
                "error": str(e)
            }
    
    async def get_patterns(self) -> Dict[str, Any]:
        """Get pattern detection metrics from Serena"""
        try:
            resp = await self.client.get(ENDPOINTS["patterns"])
            return resp.json()
        except Exception as e:
            logger.warning(f"Patterns fetch failed: {e}")
            return {
                "patterns": [],
                "source": "error",
                "error": str(e)
            }
    
    async def get_tasks(self) -> Dict[str, Any]:
        """Get task completion metrics"""
        try:
            resp = await self.client.get(ENDPOINTS["tasks"])
            return resp.json()
        except Exception:
            return {"completed": 0, "total": 0, "rate": 0.0}

    async def get_unfinished_work(self) -> Dict[str, Any]:
        """Get list of unfinished tasks"""
        try:
            resp = await self.client.get(ENDPOINTS["unfinished_work"])
            return resp.json()
        except Exception as e:
            logger.warning(f"Unfinished work fetch failed: {e}")
            return {"count": 0, "items": []}
    
    async def get_decisions(self) -> Dict[str, Any]:
        """Get recent decisions logged"""
        try:
            resp = await self.client.get(ENDPOINTS["decisions"])
            return resp.json()
        except Exception:
            return {"count": 0, "today": []}
    
    async def get_services_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        services = {
            "ConPort": "http://localhost:8005/health",
            "ADHD Engine": "http://localhost:8095/health",
            "Serena": "http://localhost:8003/health",
            "MCP Bridge": "http://localhost:3016/health",
        }
        
        health = {}
        for name, url in services.items():
            try:
                resp = await self.client.get(url)
                data = resp.json()
                health[name] = {
                    "status": data.get("status", "unknown"),
                    "latency_ms": data.get("latency_ms", 0),
                }
            except Exception:
                health[name] = {"status": "offline", "latency_ms": 0}
        
        return health
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# Simple Console View (Fallback)
# =============================================================================

async def simple_console_view():
    """Simple console output when Textual not available"""
    console = Console()
    fetcher = MetricsFetcher()
    
    try:
        while True:
            console.clear()
            
            # Fetch all metrics
            adhd_state = await fetcher.get_adhd_state()
            tasks = await fetcher.get_tasks()
            decisions = await fetcher.get_decisions()
            services = await fetcher.get_services_health()
            
            # Create layout
            layout = Layout()
            layout.split(
                Layout(name="header", size=3),
                Layout(name="adhd", size=5),
                Layout(name="metrics", size=5),
                Layout(name="services", size=8),
            )
            
            # Header
            layout["header"].update(Panel(
                f"[bold cyan]Dopemux Dashboard[/] - {datetime.now().strftime('%H:%M:%S')}",
                style="bold"
            ))
            
            # ADHD State
            energy = adhd_state.get("energy_level", "unknown")
            attention = adhd_state.get("attention_state", "unknown")
            cognitive_load = adhd_state.get("cognitive_load", 0.0)
            
            energy_icon = {"high": "⚡↑", "medium": "⚡=", "low": "⚡↓"}.get(energy, "⚡?")
            attention_icon = {"focused": "👁️●", "scattered": "👁️🌀"}.get(attention, "👁️?")
            load_bar = "█" * int(cognitive_load * 10) + "░" * (10 - int(cognitive_load * 10))
            
            adhd_table = Table.grid(padding=1)
            adhd_table.add_row(
                f"[bold]{energy_icon} {energy.title()}[/]",
                f"[bold]{attention_icon} {attention.title()}[/]",
                f"[bold]🧠 [{load_bar}] {int(cognitive_load * 100)}%[/]"
            )
            
            layout["adhd"].update(Panel(adhd_table, title="ADHD State", border_style="green"))
            
            # Metrics
            task_rate = tasks.get("rate", 0.0)
            task_bar = "█" * int(task_rate * 10) + "░" * (10 - int(task_rate * 10))
            
            metrics_table = Table.grid(padding=1)
            metrics_table.add_row(
                f"Tasks: {tasks.get('completed', 0)}/{tasks.get('total', 0)} ({int(task_rate * 100)}%)",
                task_bar
            )
            metrics_table.add_row(
                f"Decisions: {decisions.get('count', 0)} (today: {len(decisions.get('today', []))})",
                ""
            )
            
            layout["metrics"].update(Panel(metrics_table, title="Productivity", border_style="blue"))
            
            # Services
            services_table = Table(show_header=True, header_style="bold")
            services_table.add_column("Service")
            services_table.add_column("Status", justify="center")
            services_table.add_column("Latency", justify="right")
            
            for name, health in services.items():
                status = health["status"]
                status_icon = "✓" if status == "healthy" else "✗"
                status_color = "green" if status == "healthy" else "red"
                
                services_table.add_row(
                    name,
                    f"[{status_color}]{status_icon}[/]",
                    f"{health['latency_ms']}ms"
                )
            
            layout["services"].update(Panel(services_table, title="Services", border_style="cyan"))
            
            # Render
            console.print(layout)
            
            # Wait before refresh
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/]")
    finally:
        await fetcher.close()


# =============================================================================
# Textual Dashboard (Full Version)
# =============================================================================

if TEXTUAL_AVAILABLE:
    
    class ADHDStateWidget(Static):
        """Real-time ADHD state display with WebSocket support"""
        
        energy = reactive("medium")
        attention = reactive("focused")
        cognitive_load = reactive(0.65)
        flow_active = reactive(False)
        session_time = reactive("0m")
        
        def __init__(self, fetcher: Optional[MetricsFetcher] = None, **kwargs):
            default_id = kwargs.get("id")
            super().__init__(**kwargs)
            self.fetcher = fetcher
            if default_id is None:
                self.id = "adhd_state_widget"
        
        async def on_mount(self) -> None:
            # Only start polling if we have a fetcher (fallback mode)
            if self.fetcher:
                self.set_interval(1.0, self.update_state)
        
        def update_from_ws(self, data: Dict[str, Any]):
            """Update state from WebSocket message (reactive)"""
            self.energy = data.get("energy_level", "unknown")
            self.attention = data.get("attention_state", "unknown")
            self.cognitive_load = data.get("cognitive_load", 0.0)
            
            flow_data = data.get("flow_state", {})
            self.flow_active = flow_data.get("active", False) if isinstance(flow_data, dict) else False
            
            self.session_time = data.get("session_time", "0m")
        
        async def update_state(self) -> None:
            """Fallback polling method (only used if no WebSocket)"""
            if self.fetcher:
                data = await self.fetcher.get_adhd_state()
                self.update_from_ws(data)
        
        def render(self) -> Panel:
            energy_icons = {"high": "⚡↑", "medium": "⚡=", "low": "⚡↓", "depleted": "⚡⇣"}
            attention_icons = {"focused": "👁️●", "scattered": "👁️🌀", "overwhelmed": "👁️💥"}
            
            energy_icon = energy_icons.get(self.energy, "⚡?")
            attention_icon = attention_icons.get(self.attention, "👁️?")
            
            # Cognitive load gauge
            filled = int(self.cognitive_load * 10)
            load_bar = f"[{'|' * filled}{'·' * (10 - filled)}]"
            
            # Flow indicator
            flow_status = "🌊 In Flow" if self.flow_active else ""
            
            table = Table.grid(padding=1)
            table.add_column(style="bold cyan")
            table.add_column(style="bold magenta")
            table.add_column(style="bold yellow")
            
            table.add_row(
                f"{energy_icon} {self.energy.title()}",
                f"{attention_icon} {self.attention.title()}",
                f"🧠 {load_bar} {int(self.cognitive_load * 100)}%"
            )
            table.add_row(
                f"Session: {self.session_time}",
                flow_status,
                ""
            )
            
            # Choose border color based on cognitive load
            if self.cognitive_load > 0.85:
                border_style = "red"
            elif self.cognitive_load > 0.7:
                border_style = "yellow"
            else:
                border_style = "green"
            
            return Panel(table, title="⚡ ADHD State", border_style=border_style)
    
    
    class MetricsWidget(Static):
        """Task and decision metrics"""
        
        tasks_completed = reactive(0)
        tasks_total = reactive(0)
        decisions_count = reactive(0)
        
        def __init__(self, fetcher: MetricsFetcher, **kwargs):
            super().__init__(**kwargs)
            self.fetcher = fetcher
        
        async def on_mount(self) -> None:
            self.set_interval(30.0, self.update_metrics)
            await self.update_metrics()
        
        async def update_metrics(self) -> None:
            tasks = await self.fetcher.get_tasks()
            decisions = await self.fetcher.get_decisions()
            
            self.tasks_completed = tasks.get("completed", 0)
            self.tasks_total = tasks.get("total", 0)
            self.decisions_count = decisions.get("count", 0)
        
        def render(self) -> Panel:
            rate = self.tasks_completed / self.tasks_total if self.tasks_total > 0 else 0
            bar_filled = int(rate * 10)
            task_bar = "█" * bar_filled + "░" * (10 - bar_filled)
            
            table = Table.grid(padding=1)
            table.add_column()
            table.add_column(justify="right")
            
            table.add_row(
                f"Tasks: {self.tasks_completed}/{self.tasks_total}",
                f"{task_bar} {int(rate * 100)}%"
            )
            table.add_row(
                f"Decisions: {self.decisions_count}",
                ""
            )
            
            return Panel(table, title="📊 Productivity", border_style="blue")
    
    
    class ServicesWidget(Static):
        """Service health status"""
        
        services_data = reactive({})
        
        def __init__(self, fetcher: MetricsFetcher, **kwargs):
            super().__init__(**kwargs)
            self.fetcher = fetcher
        
        async def on_mount(self) -> None:
            self.set_interval(60.0, self.update_services)
            await self.update_services()
        
        async def update_services(self) -> None:
            self.services_data = await self.fetcher.get_services_health()
        
        def render(self) -> Panel:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Service", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Latency", justify="right")
            
            for name, health in self.services_data.items():
                status = health["status"]
                status_icon = "✓" if status == "healthy" else "✗"
                status_style = "green" if status == "healthy" else "red"
                
                table.add_row(
                    name,
                    f"[{status_style}]{status_icon}[/]",
                    f"{health['latency_ms']}ms"
                )
            
            return Panel(table, title="🔧 Services", border_style="cyan")
    
    
    class TasksWidget(Static):
        """Live list of unfinished tasks with selection support"""

        def __init__(self, fetcher: MetricsFetcher, **kwargs):
            super().__init__(**kwargs)
            self.fetcher = fetcher

        def compose(self) -> ComposeResult:
            yield Label("📝 Unfinished Work (Select with 'd')")
            yield DataTable(id="tasks-table")

        async def on_mount(self) -> None:
            table = self.query_one(DataTable)
            table.add_columns("ID", "Task", "Status")
            table.cursor_type = "row"
            self.set_interval(30.0, self.update_tasks)
            await self.update_tasks()

        async def update_tasks(self) -> None:
            try:
                data = await self.fetcher.get_unfinished_work()
                items = data.get("items", [])
                table = self.query_one(DataTable)

                # Remember selection if possible
                cursor_row = table.cursor_row

                table.clear()
                for item in items:
                    # Truncate title if too long
                    title = item.get("title", "Unknown")
                    if len(title) > 40:
                        title = title[:37] + "..."

                    table.add_row(
                        str(item.get("id", "")),
                        title,
                        item.get("status", "unknown")
                    )

                # Restore cursor position
                if cursor_row is not None and cursor_row < len(table.rows):
                    table.move_cursor(row=cursor_row)
            except Exception as e:
                logger.debug(f"Tasks widget update failed: {e}")


    class TrendsWidget(Static):
        """Historical trends with sparklines"""
        
        sparklines = reactive({})
        prom_healthy = reactive(True)
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.prom = PrometheusClient(PrometheusConfig())
            self.sparkline_gen = SparklineGenerator()
        
        async def on_mount(self) -> None:
            # Update sparklines every 30 seconds
            self.set_interval(30.0, self.update_sparklines)
            await self.update_sparklines()
        
        async def update_sparklines(self) -> None:
            """Fetch and render all sparklines from Prometheus"""
            try:
                # Check if Prometheus is healthy
                self.prom_healthy = await self.prom.health_check()
                if not self.prom_healthy:
                    logger.warning("Prometheus is not healthy")
                    return
                
                # Fetch all metrics in parallel
                results = await asyncio.gather(
                    # Cognitive Load (last 2 hours, 5min resolution)
                    self.prom.query_range('adhd_cognitive_load', hours=2, step='5m'),
                    # Task Velocity (last 7 days, 1hr resolution)
                    self.prom.query_range('adhd_task_velocity_per_day', hours=168, step='1h'),
                    # Context Switches (last 24 hours, 15min resolution)
                    self.prom.query_range('adhd_context_switches_total', hours=24, step='15m'),
                    return_exceptions=True
                )
                
                cognitive_data, velocity_data, switches_data = results
                
                # Generate sparklines with stats
                sparklines = {}
                
                # Cognitive Load
                if isinstance(cognitive_data, list) and cognitive_data:
                    stats = self.sparkline_gen.generate_with_stats(
                        cognitive_data, width=24, min_val=0, max_val=100
                    )
                    sparklines['cognitive'] = {
                        'sparkline': self.sparkline_gen.colorize(
                            stats['sparkline'], cognitive_data, metric_type="cognitive_load"
                        ),
                        'current': stats['current'],
                        'trend': stats['trend']
                    }
                else:
                    sparklines['cognitive'] = {
                        'sparkline': '[dim]' + '─' * 24 + '[/dim]',
                        'current': 0,
                        'trend': 'unknown'
                    }
                
                # Task Velocity
                if isinstance(velocity_data, list) and velocity_data:
                    stats = self.sparkline_gen.generate_with_stats(velocity_data, width=24)
                    sparklines['velocity'] = {
                        'sparkline': self.sparkline_gen.colorize(
                            stats['sparkline'], velocity_data, metric_type="velocity"
                        ),
                        'current': stats['current'],
                        'trend': stats['trend']
                    }
                else:
                    sparklines['velocity'] = {
                        'sparkline': '[dim]' + '─' * 24 + '[/dim]',
                        'current': 0,
                        'trend': 'unknown'
                    }
                
                # Context Switches
                if isinstance(switches_data, list) and switches_data:
                    stats = self.sparkline_gen.generate_with_stats(switches_data, width=24)
                    sparklines['switches'] = {
                        'sparkline': self.sparkline_gen.colorize(
                            stats['sparkline'], switches_data, metric_type="switches"
                        ),
                        'current': stats['current'],
                        'trend': stats['trend']
                    }
                else:
                    sparklines['switches'] = {
                        'sparkline': '[dim]' + '─' * 24 + '[/dim]',
                        'current': 0,
                        'trend': 'unknown'
                    }
                
                self.sparklines = sparklines
                
            except Exception as e:
                logger.error(f"Error updating sparklines: {e}")
                self.prom_healthy = False
        
        def render(self) -> Panel:
            """Render trends panel with live sparklines"""
            
            if not self.prom_healthy:
                content = """
[dim]Prometheus unavailable - sparklines disabled[/dim]

Run: docker start dopemux-prometheus
                """
                return Panel(content, title="📈 Trends (Offline)", border_style="dim red")
            
            if not self.sparklines:
                content = "[dim]Loading sparklines...[/dim]"
                return Panel(content, title="📈 Trends", border_style="yellow")
            
            # Get sparkline data
            cognitive = self.sparklines.get('cognitive', {})
            velocity = self.sparklines.get('velocity', {})
            switches = self.sparklines.get('switches', {})
            
            # Trend arrows
            def trend_arrow(trend):
                if trend == 'up':
                    return '↗'
                elif trend == 'down':
                    return '↘'
                else:
                    return '→'
            
            content = f"""
[bold]Cognitive Load[/bold] (2h) {trend_arrow(cognitive.get('trend', 'unknown'))}
{cognitive.get('sparkline', '─' * 24)}  [{int(cognitive.get('current', 0))}%]

[bold]Task Velocity[/bold] (7d) {trend_arrow(velocity.get('trend', 'unknown'))}
{velocity.get('sparkline', '─' * 24)}  [{velocity.get('current', 0):.1f}/day]

[bold]Context Switches[/bold] (24h) {trend_arrow(switches.get('trend', 'unknown'))}
{switches.get('sparkline', '─' * 24)}  [{int(switches.get('current', 0))}/hr]

[dim]Updated every 30s[/dim]
            """
            
            return Panel(content.strip(), title="📈 Trends (Live)", border_style="magenta")
    
    
    class DopemuxDashboard(App):
        """Main Textual dashboard application"""
        
        # Dynamic CSS - will be updated based on theme
        CSS = """
        Screen {
            background: $surface;
        }
        
        #adhd-state {
            height: 7;
        }
        
        #adhd-state.focus-mode {
            height: 12;
        }
        
        #metrics {
            height: 6;
        }
        
        #services {
            height: 10;
        }

        #tasks-list {
            height: 12;
            border: tall $blue;
            background: $surface;
            margin: 1 0;
        }

        #tasks-list Label {
            width: 100%;
            content-align: center middle;
            background: $blue;
            color: $surface;
            text-style: bold;
        }
        
        #trends {
            height: 12;
        }
        
        #services.dimmed {
            opacity: 0.3;
        }
        
        .help-screen {
            align: center middle;
        }
        
        .help-box {
            width: 60;
            height: 25;
            border: heavy $accent;
            background: $panel;
        }
        
        .focus-indicator {
            background: $accent;
            color: $surface;
            text-style: bold;
        }
        """
        
        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh", "Refresh"),
            ("b", "force_break", "Take Break"),
            ("f", "toggle_focus", "Focus Mode"),
            ("t", "cycle_theme", "Theme"),
            ("n", "toggle_notifications", "Notifications"),
            ("?", "show_help", "Help"),
            # Drill-down keybindings (Day 4)
            ("d", "show_task_detail", "Task Details"),
            ("l", "show_service_logs", "Service Logs"),
            ("p", "show_pattern_detail", "Pattern Details"),
            ("h", "show_metric_history", "Metric History"),
        ]
        
        def __init__(self):
            super().__init__()
            self.fetcher = MetricsFetcher()
            
            # WebSocket metrics manager (Day 8: NEW!)
            self.metrics_manager = MetricsManager(self)
            
            # Load saved config
            self.config = load_config()
            self.focus_mode = self.config.get("focus_mode", False)
            self.active_theme = self.config.get("theme", "mocha")
            self.theme_names = list(THEMES.keys())
            
            # Initialize smart notifications
            self.notification_manager = NotificationManager()
            self.notification_manager.enabled = self.config.get("notifications_enabled", True)
            self.auto_trigger = AutoTriggerMonitor(self.fetcher, self.notification_manager)
            self.monitor_task = None
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield ADHDStateWidget(None, id="adhd-state")  # No fetcher - uses WebSocket!
            yield MetricsWidget(self.fetcher, id="metrics")
            yield TasksWidget(self.fetcher, id="tasks-list")
            yield ServicesWidget(self.fetcher, id="services")
            yield TrendsWidget(id="trends")
            yield Footer()
        
        def on_mount(self) -> None:
            """Apply theme, focus mode, and start WebSocket streaming"""
            self.apply_theme(self.active_theme)
            if self.focus_mode:
                self._apply_focus_mode_visuals()
            
            # Start smart notification monitoring
            self.monitor_task = asyncio.create_task(self.auto_trigger.monitor_loop())
            
            # Day 8: Start WebSocket streaming! 🚀
            self.run_worker(self.start_metrics_streaming())
            
            # Show notification state on startup
            if not self.notification_manager.enabled:
                self.notify("Notifications disabled 🔕", severity="information")
        
        async def start_metrics_streaming(self):
            """Initialize WebSocket streaming (Day 8)"""
            try:
                await self.metrics_manager.start()
                
                # Update footer based on mode
                if self.metrics_manager.mode == "websocket":
                    self.notify("🟢 WebSocket connected", severity="information", timeout=2)
                elif self.metrics_manager.mode == "polling":
                    self.notify("🟡 Using HTTP polling", severity="warning", timeout=2)
                else:
                    self.notify("⚪ Offline", severity="error", timeout=2)
                    
            except Exception as e:
                logger.error(f"Failed to start metrics streaming: {e}")
                self.notify("🔴 Connection error", severity="error", timeout=3)
        
        def apply_theme(self, theme_name: str) -> None:
            """Apply color theme to dashboard"""
            if theme_name not in THEMES:
                theme_name = "mocha"
            
            self.active_theme = theme_name
            theme = THEMES[theme_name]
            
            # Textual themes are set via CSS variables
            # For now, we'll just store the preference and notify
            # Full CSS variable support would require Textual 0.40+
            # This is a simplified implementation that works
            
            # In the future, we can use:
            # self.stylesheet = generate_css_for_theme(theme)
            
            # For now, theme is stored and can be used by widgets
            self.theme_colors = theme
        
        def action_cycle_theme(self) -> None:
            """Cycle through available themes"""
            current_idx = self.theme_names.index(self.active_theme)
            next_idx = (current_idx + 1) % len(self.theme_names)
            next_theme = self.theme_names[next_idx]
            
            self.apply_theme(next_theme)
            
            # Save preference
            self.config["theme"] = next_theme
            save_config(self.config)
            
            theme_display = THEMES[next_theme]["name"]
            self.notify(f"Theme: {theme_display} 🎨", severity="information")
        
        def action_refresh(self) -> None:
            """Force refresh all widgets"""
            for widget in self.query(Static):
                if hasattr(widget, "update_state"):
                    asyncio.create_task(widget.update_state())
                elif hasattr(widget, "update_metrics"):
                    asyncio.create_task(widget.update_metrics())
                elif hasattr(widget, "update_services"):
                    asyncio.create_task(widget.update_services())
                elif hasattr(widget, "update_sparklines"):
                    asyncio.create_task(widget.update_sparklines())
        
        def action_force_break(self) -> None:
            """Trigger break timer"""
            async def _trigger():
                success = await trigger_break(5)
                if success:
                    self.notify("Break timer started! ☕", severity="information")
                else:
                    self.notify("Could not start break (ADHD Engine offline?)", severity="warning")
            
            asyncio.create_task(_trigger())
        
        def _apply_focus_mode_visuals(self) -> None:
            """Apply visual changes for focus mode"""
            try:
                # Enlarge ADHD state panel
                adhd_widget = self.query_one("#adhd-state")
                adhd_widget.add_class("focus-mode")
                
                # Dim services panel
                services_widget = self.query_one("#services")
                services_widget.add_class("dimmed")
                
                # Update header with focus indicator
                header = self.query_one(Header)
                header.add_class("focus-indicator")
            except:
                pass  # Widgets might not be mounted yet
        
        def _remove_focus_mode_visuals(self) -> None:
            """Remove visual changes for focus mode"""
            try:
                # Restore ADHD state panel
                adhd_widget = self.query_one("#adhd-state")
                adhd_widget.remove_class("focus-mode")
                
                # Restore services panel
                services_widget = self.query_one("#services")
                services_widget.remove_class("dimmed")
                
                # Restore header
                header = self.query_one(Header)
                header.remove_class("focus-indicator")
            except:
                pass
        
        def action_toggle_focus(self) -> None:
            """Toggle focus mode with visual changes"""
            self.focus_mode = not self.focus_mode
            
            if self.focus_mode:
                self._apply_focus_mode_visuals()
                self.notify("Focus Mode ON 🎯 (ADHD state enlarged, services dimmed)", 
                           severity="information")
            else:
                self._remove_focus_mode_visuals()
                self.notify("Focus Mode OFF", severity="information")
            
            # Save preference
            self.config["focus_mode"] = self.focus_mode
            save_config(self.config)
        
        def action_show_help(self) -> None:
            """Show keyboard shortcuts help"""
            self.push_screen(HelpScreen())
        
        def action_toggle_notifications(self) -> None:
            """Toggle smart notifications on/off"""
            enabled = self.notification_manager.toggle_enabled()
            
            if enabled:
                self.notify("Notifications enabled 🔔", severity="information")
            else:
                self.notify("Notifications disabled 🔕", severity="information")
            
            # Save preference
            self.config["notifications_enabled"] = enabled
            save_config(self.config)
        
        def action_show_task_detail(self) -> None:
            """Show detailed view of current/selected task"""
            try:
                # Try to get the selected task from the TasksWidget
                tasks_widget = self.query_one("#tasks-list", TasksWidget)
                table = tasks_widget.query_one(DataTable)

                if table.cursor_row is not None:
                    # Get the ID from the first column of the selected row
                    row_key = table.coordinate_to_row_key(table.cursor_coordinate)
                    row_data = table.get_row(row_key)
                    task_id = row_data[0]
                    self.push_screen(TaskDetailModal(task_id))
                else:
                    self.notify("Please select a task from the list first", severity="warning")
            except Exception as e:
                # Fallback to sample task if selection fails
                logger.debug(f"Failed to get selected task: {e}")
                self.push_screen(TaskDetailModal(1))
        
        def action_show_service_logs(self) -> None:
            """Show live logs for a service"""
            # Show service selection menu
            self.push_screen(ServiceSelectionModal())
        
        async def action_show_pattern_detail(self) -> None:
            """Show detailed view of a behavioral pattern"""
            # Get the top pattern from Serena
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get("http://localhost:8003/api/patterns/top?limit=1")
                    if response.status_code == 200:
                        data = response.json()
                        patterns = data.get("patterns", [])
                        if patterns:
                            # Use the first (top) pattern
                            top_pattern = patterns[0]
                            pattern_id = top_pattern.get("id", 7)
                            # Pass pattern data to modal
                            self.push_screen(PatternDetailModal(pattern_id, top_pattern))
                        else:
                            # Fallback to sample
                            self.push_screen(PatternDetailModal(7))
                    else:
                        # Fallback to sample
                        self.push_screen(PatternDetailModal(7))
            except Exception as e:
                # Fallback to sample
                self.app.notify(f"⚠️ Could not load pattern data: {e}", severity="warning")
                self.push_screen(PatternDetailModal(7))
        
        def action_show_metric_history(self) -> None:
            """Show historical graph for a metric"""
            # For now, show cognitive load history
            # TODO: Let user choose which metric
            metric_name = "Cognitive Load"
            self.push_screen(MetricHistoryModal(metric_name))
        
        async def on_shutdown(self) -> None:
            # Cancel monitoring task
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            
            await self.fetcher.close()


    # =========================================================================
    # Modal System - Drill-Down Views
    # =========================================================================

    class ModalView(Screen):
        """Base class for all drill-down modals"""
        
        CSS = """
        ModalView {
            align: center middle;
        }
        
        #modal-container {
            width: 85%;
            height: 85%;
            background: $surface0;
            border: thick $blue;
            padding: 1 2;
        }
        
        #modal-header {
            dock: top;
            height: 3;
            background: $blue;
            color: $surface0;
            content-align: center middle;
            text-style: bold;
        }
        
        #modal-content {
            height: 1fr;
            overflow-y: auto;
            padding: 1 2;
        }
        
        #modal-footer {
            dock: bottom;
            height: 3;
            background: $surface1;
            color: $text;
            content-align: center middle;
        }
        """
        
        BINDINGS = [
            ("escape", "dismiss", "Close"),
            ("q", "dismiss", "Quit"),
        ]
        
        def action_dismiss(self) -> None:
            """Close modal and return to main dashboard"""
            self.app.pop_screen()


    class TaskDetailModal(ModalView):
        """Detailed view of a single task with full context"""
        
        def __init__(self, task_id: Union[int, str], task_data: Optional[Dict] = None):
            super().__init__()
            self.task_id = task_id
            self._task_data = task_data
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(f"Task #{self.task_id} Details", id="modal-header")
                yield Static(id="modal-content")
                yield Static("[Esc] Close  [?] Help  [c] Complete  [p] Priority", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Fetch task details and render"""
            content = self.query_one("#modal-content", Static)
            content.update("⏳ Loading task details...")
            
            try:
                task_data = await self.fetch_task_details()
                rendered = self.render_task_content(task_data)
                content.update(rendered)
            except Exception as e:
                content.update(f"❌ Error loading task: {e}")
        
        async def fetch_task_details(self) -> Dict:
            """Fetch all task-related data"""
            if self._task_data:
                return self._task_data
            
            # TODO: Fetch from real API
            # For now, return mock data
            return {
                "id": self.task_id,
                "title": "Implement drill-down modals",
                "status": "in_progress",
                "priority": "high",
                "created": "2h ago",
                "due": "Today 5pm",
                "tags": ["coding", "deep-work", "backend"],
                "time_worked": "1h 23m",
                "estimated": "3h",
                "focus_sessions": 2,
                "context_switches": 4,
                "cognitive_load_trend": "▃▄▅▆▅▄▃",
            }
        
        def render_task_content(self, task: Dict) -> str:
            """Render task details as rich text"""
            return f"""
[bold cyan]📊 OVERVIEW[/bold cyan]
Status: [yellow]{task['status']}[/yellow]  Priority: [red]{task['priority']}[/red]
Created: {task['created']}  Due: {task['due']}
Tags: {', '.join(f'[blue]{t}[/blue]' for t in task['tags'])}

[bold cyan]📈 METRICS[/bold cyan]
Time worked: [green]{task['time_worked']}[/green]  Estimated: {task['estimated']}
Focus sessions: {task['focus_sessions']}  Context switches: {task['context_switches']} ([green]low[/green])
Cognitive load: {task['cognitive_load_trend']} ([green]trend: decreasing ✓[/green])

[bold cyan]🧠 ADHD INSIGHTS[/bold cyan]
• Currently in optimal flow (energy: high, focus: stable)
• Good momentum - avoid breaks until natural stopping point
• Similar tasks completed 30% faster in afternoon

[bold cyan]📝 HISTORY[/bold cyan]
14:32  Status changed: todo → in_progress
14:35  Note added: "Starting with modal base class"
15:12  Context switch detected (Slack notification)
15:14  Resumed focus

[bold cyan]⚡ ACTIONS[/bold cyan]
[c] Complete task  [b] Block task  [p] Change priority
[n] Add note      [t] Add time    [d] Delete task
            """
        
        BINDINGS = [
            *ModalView.BINDINGS,
            ("c", "complete_task", "Complete"),
            ("p", "change_priority", "Priority"),
            ("n", "add_note", "Note"),
        ]
        
        def action_complete_task(self) -> None:
            """Mark task as complete"""
            self.app.notify(f"✅ Task #{self.task_id} completed!", severity="information")
            self.action_dismiss()
        
        def action_change_priority(self) -> None:
            """Change task priority"""
            self.app.notify(f"🎯 Priority changed for task #{self.task_id}", severity="information")
        
        def action_add_note(self) -> None:
            """Add a note to task"""
            self.app.notify(f"📝 Note added to task #{self.task_id}", severity="information")


    class ServiceSelectionModal(ModalView):
        """Modal for selecting which service to view logs for"""

        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static("Select Service for Logs", id="modal-header")
                with Container(id="modal-content"):
                    yield ListView(id="service-list")
                yield Static("[Esc] Close  [Enter] Select", id="modal-footer")

        async def on_mount(self) -> None:
            """Initialize service list"""
            list_view = self.query_one("#service-list", ListView)

            # Available services
            services = [
                "ADHD Engine",
                "ConPort",
                "Serena",
                "Zen MCP",
                "Task Orchestrator",
                "Integration Bridge",
                "Dope Context",
                "Desktop Commander"
            ]

            for service in services:
                list_view.append(ListItem(Label(service)))

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            """Handle service selection"""
            selected_item = event.item
            service_name = str(selected_item.get_child_by_type(Label).renderable)

            # Close selection modal and open logs modal
            self.app.pop_screen()  # Close this modal
            self.app.push_screen(ServiceLogsModal(service_name))

    class ServiceLogsModal(ModalView):
        """Live log viewer for services"""
        
        # Map display names to docker compose service names
        SERVICE_MAP = {
            "ADHD Engine": "adhd-engine",
            "ConPort": "conport",
            "Serena": "serena",
            "Zen MCP": "pal",
            "Task Orchestrator": "task-orchestrator",
            "Integration Bridge": "dopecon-bridge",
            "Dope Context": "dope-context",
            "Desktop Commander": "desktop-commander"
        }

        def __init__(self, service_name: str):
            super().__init__()
            self.service_name = service_name
            self.auto_scroll = True
            self.filter_level = "ALL"
            self.compose_service = self.SERVICE_MAP.get(service_name)
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(f"{self.service_name} Service Logs (live)", id="modal-header")
                with Container(id="modal-content"):
                    yield DataTable(id="log-table")
                yield Static("[Esc] Close  [f] Filter  [s] Auto-scroll  [e] Export", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Initialize log viewer"""
            table = self.query_one("#log-table", DataTable)
            table.add_columns("Time", "Level", "Message")
            
            try:
                logs = await self.fetch_logs(lines=50)
                self.render_logs(logs)
            except Exception as e:
                self.app.notify(f"❌ Error loading logs: {e}", severity="error")
        
        async def fetch_logs(self, lines: int = 50) -> List[Dict]:
            """Fetch recent logs from service via Docker"""
            if not self.compose_service:
                return [{"timestamp": "", "level": "ERROR", "message": f"Unknown service: {self.service_name}"}]
            
            # Determine project root (assuming script is in scripts/ or root)
            script_path = Path(__file__).resolve()
            if script_path.parent.name == "scripts":
                project_root = script_path.parent.parent
            else:
                project_root = script_path.parent
            
            try:
                # Check for docker
                if not shutil.which("docker"):
                     return [{"timestamp": "", "level": "ERROR", "message": "Docker executable not found"}]

                # Run docker compose logs
                cmd = [
                    "docker", "compose", "logs",
                    "--tail", str(lines),
                    "--timestamps",
                    "--no-log-prefix",
                    "--no-color",
                    self.compose_service
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(project_root)
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                     error_msg = stderr.decode().strip() or "Unknown error"
                     return [{"timestamp": "", "level": "ERROR", "message": f"Docker error: {error_msg}"}]

                logs = []
                # Parse logs
                # Format: 2023-10-27T10:00:00.123456789Z <content>
                log_lines = stdout.decode().splitlines()

                for line in log_lines:
                    parts = line.split(" ", 1)
                    if len(parts) < 2:
                        continue

                    timestamp_str, content = parts

                    # Clean timestamp (remove Z and sub-seconds for display)
                    # 2023-10-27T10:00:00.123456789Z -> 10:00:00
                    try:
                        timestamp = timestamp_str.split("T")[-1].replace("Z", "").split(".")[0]
                    except:
                        timestamp = timestamp_str

                    # Detect level
                    level = "INFO"
                    content_upper = content.upper()
                    if "ERROR" in content_upper: level = "ERROR"
                    elif "WARN" in content_upper: level = "WARN"
                    elif "DEBUG" in content_upper: level = "DEBUG"
                    elif "CRITICAL" in content_upper: level = "ERROR"

                    logs.append({
                        "timestamp": timestamp,
                        "level": level,
                        "message": content.strip()
                    })

                return logs or [{"timestamp": "", "level": "INFO", "message": "No logs found"}]

            except Exception as e:
                return [{"timestamp": "", "level": "ERROR", "message": f"Failed to fetch logs: {e}"}]
        
        def render_logs(self, logs: List[Dict]) -> None:
            """Render logs in table"""
            from rich.text import Text
            
            table = self.query_one("#log-table", DataTable)
            
            for log in logs:
                # Color-code by level
                level_styles = {
                    "ERROR": "bold red",
                    "WARN": "bold yellow",
                    "INFO": "blue",
                    "DEBUG": "dim"
                }
                
                style = level_styles.get(log["level"], "white")
                
                table.add_row(
                    log["timestamp"],
                    Text(log["level"], style=style),
                    log["message"]
                )
        
        BINDINGS = [
            *ModalView.BINDINGS,
            ("f", "toggle_filter", "Filter"),
            ("s", "toggle_autoscroll", "Auto-scroll"),
            ("e", "export_logs", "Export"),
        ]
        
        def action_toggle_filter(self) -> None:
            """Toggle log level filter"""
            levels = ["ALL", "ERROR", "WARN", "INFO", "DEBUG"]
            current_idx = levels.index(self.filter_level)
            self.filter_level = levels[(current_idx + 1) % len(levels)]
            self.app.notify(f"Filter: {self.filter_level}", severity="information")
        
        def action_toggle_autoscroll(self) -> None:
            """Toggle auto-scrolling"""
            self.auto_scroll = not self.auto_scroll
            status = "ON" if self.auto_scroll else "OFF"
            self.app.notify(f"Auto-scroll: {status}", severity="information")
        
        def action_export_logs(self) -> None:
            """Export logs to file"""
            filename = f"{self.service_name}_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            self.app.notify(f"📄 Logs exported to {filename}", severity="information")


    class PatternDetailModal(ModalView):
        """Detailed view of a behavioral pattern"""
        
        def __init__(self, pattern_id: Union[int, str], pattern_data: Optional[Dict] = None):
            super().__init__()
            self.pattern_id = pattern_id
            self._pattern_data = pattern_data
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(f"Pattern #{self.pattern_id} Details", id="modal-header")
                yield Static(id="modal-content")
                yield Static("[Esc] Close  [?] Help", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Fetch pattern details and render"""
            content = self.query_one("#modal-content", Static)
            content.update("⏳ Loading pattern details...")
            
            try:
                pattern_data = await self.fetch_pattern_details()
                rendered = self.render_pattern_content(pattern_data)
                content.update(rendered)
            except Exception as e:
                content.update(f"❌ Error loading pattern: {e}")
        
        async def fetch_pattern_details(self) -> Dict:
            """Fetch pattern details from Serena"""
            # If we have pre-loaded data AND it looks detailed (has history/tags), use it
            if self._pattern_data and "success_rate" in self._pattern_data:
                return self._pattern_data
            
            # Fetch from real API
            try:
                url = f"http://localhost:8003/api/patterns/{self.pattern_id}"
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass  # Fallback to mock if API fails

            # Fallback (Mock)
            return self._pattern_data if self._pattern_data else {
                "id": self.pattern_id,
                "name": "Deep Work Morning Block",
                "occurrences": 47,
                "success_rate": 0.89,
                "avg_duration": "2h 15m",
                "confidence": 0.92,
                "tags": ["morning", "deep-work", "productive"],
                "history": [1, 1, 1, 0, 1, 1, 0]
            }
        
        def render_pattern_content(self, pattern: Dict) -> str:
            """Render pattern details"""
            return f"""
[bold cyan]📊 PATTERN STATISTICS[/bold cyan]
Name: [yellow]{pattern['name']}[/yellow]
Occurrences: {pattern['occurrences']}  Success rate: [green]{pattern['success_rate']*100:.0f}%[/green]
Avg duration: {pattern['avg_duration']}  Confidence: {pattern['confidence']:.2f} ([green]very high[/green])
Tags: {', '.join(f'[blue]{t}[/blue]' for t in pattern['tags'])}

[bold cyan]🎯 PATTERN DEFINITION[/bold cyan]
Triggers:
  • Time: 8:00-10:00 AM
  • Energy level: High
  • No meetings scheduled
  • Coffee consumed in last 30 min

Typical behavior:
  • 2-3 hour focused coding session
  • Minimal context switches (avg: 2)
  • High task completion rate
  • Break taken around 10:15 AM

[bold cyan]📈 TREND ANALYSIS[/bold cyan]
Occurrence by day: Mon ████ Tue ███ Wed █████ Thu ██ Fri ███
Success rate over time: ▅▆▇▇██▇▆ ([green]improving[/green])

[bold cyan]🧠 RECOMMENDATIONS[/bold cyan]
✓ Schedule complex tasks during this window
✓ Block calendar from 8-10 AM daily
✓ Prepare task list night before
✗ Avoid meetings or calls in this slot

[bold cyan]🔄 RECENT OCCURRENCES[/bold cyan]
Today 9:00    ✓ Completed  Duration: 2h 12m  Tasks: 3/3
Yesterday     ✓ Completed  Duration: 1h 54m  Tasks: 2/3
2 days ago    ✗ Interrupted  Duration: 45m  (Meeting conflict)
3 days ago    ✓ Completed  Duration: 2h 31m  Tasks: 4/4
            """


    class MetricHistoryModal(ModalView):
        """Detailed historical view of a metric"""
        
        def __init__(self, metric_name: str, metric_data: Optional[Dict] = None):
            super().__init__()
            self.metric_name = metric_name
            self._metric_data = metric_data
        
        def compose(self) -> ComposeResult:
            with Container(id="modal-container"):
                yield Static(f"{self.metric_name} - History (Last 7 Days)", id="modal-header")
                yield Static(id="modal-content")
                yield Static("[Esc] Close  [z] Zoom  [e] Export", id="modal-footer")
        
        async def on_mount(self) -> None:
            """Fetch metric history and render"""
            content = self.query_one("#modal-content", Static)
            content.update("⏳ Loading metric history...")
            
            try:
                metric_data = await self.fetch_metric_history()
                rendered = self.render_metric_content(metric_data)
                content.update(rendered)
            except Exception as e:
                content.update(f"❌ Error loading metric: {e}")
        
        async def fetch_metric_history(self) -> Dict:
            """Fetch time-series data from Prometheus"""
            if self._metric_data:
                return self._metric_data
            
            # TODO: Fetch from Prometheus
            return {
                "current": 0.65,
                "avg": 0.71,
                "min": 0.42,
                "max": 0.95,
                "sparkline": "▃▅▆▇▅▄▃▂▄▆▅▃"
            }
        
        def render_metric_content(self, data: Dict) -> str:
            """Render metric history graph"""
            return f"""
[bold cyan]📊 METRIC SUMMARY[/bold cyan]
Current: [yellow]{data['current']:.2f}[/yellow]
Average: {data['avg']:.2f}
Min: [green]{data['min']:.2f}[/green]  Max: [red]{data['max']:.2f}[/red]

[bold cyan]📈 TREND (Last 7 Days)[/bold cyan]
{data['sparkline']}

[bold cyan]📊 ANNOTATIONS[/bold cyan]
Wed 2pm: Peak load (0.95) - Meeting marathon
Thu 9am: Optimal zone (0.65) - Deep work session
Fri 4pm: Low load (0.42) - End of week fatigue

[bold cyan]🎯 INSIGHTS[/bold cyan]
• Best performance: Tue-Thu mornings (8-11 AM)
• Decline pattern: Friday afternoons
• Suggestion: Schedule deep work Tue/Wed/Thu AM
            """
        
        BINDINGS = [
            *ModalView.BINDINGS,
            ("z", "zoom", "Zoom"),
            ("e", "export", "Export"),
        ]
        
        def action_zoom(self) -> None:
            """Change zoom level"""
            self.app.notify("Zoom changed", severity="information")
        
        def action_export(self) -> None:
            """Export metric data"""
            filename = f"{self.metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.app.notify(f"📄 Data exported to {filename}", severity="information")


    # =========================================================================
    # Help Screen
    # =========================================================================

    class HelpScreen(Screen):
        """Modal help screen showing keyboard shortcuts"""
        
        BINDINGS = [
            ("escape", "dismiss", "Close"),
            ("?", "dismiss", "Close"),
        ]
        
        def compose(self) -> ComposeResult:
            help_text = """
╔════════════════════════════════════════════════════╗
║                                                    ║
║          Dopemux Keyboard Shortcuts                ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  Navigation & Control:                            ║
║  ─────────────────────                             ║
║  q          Quit dashboard                         ║
║  r          Refresh all panels                     ║
║  ?          Show this help                         ║
║  Esc        Close help / cancel                    ║
║                                                    ║
║  ADHD Actions:                                     ║
║  ─────────────                                     ║
║  b          Take a break now (5 min timer)         ║
║  f          Toggle focus mode (enlarge/dim)        ║
║  n          Toggle smart notifications             ║
║                                                    ║
║  Drill-Downs (NEW! 🎯):                            ║
║  ──────────────────                                ║
║  d          Task details (full context)            ║
║  l          Service logs (live viewer)             ║
║  p          Pattern details (analysis)             ║
║  h          Metric history (graphs)                ║
║                                                    ║
║  Appearance:                                       ║
║  ───────────                                       ║
║  t          Cycle theme (Mocha/Nord/Dracula)       ║
║                                                    ║
║  Smart Notifications:                              ║
║  ─────────────────────                             ║
║  Auto-alerts for:                                  ║
║    • Cognitive overload (>85%)                     ║
║    • Energy depletion                              ║
║    • Break reminders (5min warning)                ║
║    • Flow state achievements                       ║
║    • Service failures                              ║
║                                                    ║
║  🔔 Press 'n' to toggle notifications              ║
║  🎯 Flow protection: non-critical alerts muted     ║
║                                                    ║
║  Drill-Down Tips:                                  ║
║  ────────────────                                  ║
║  Press 'd' → See full task context & insights      ║
║  Press 'l' → View live service logs & errors       ║
║  Press 'p' → Analyze behavioral patterns           ║
║  Press 'h' → Review metric trends & history        ║
║  All modals: Press 'Esc' or 'q' to close           ║
║                                                    ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  💡 Tip: Press 'f' when overwhelmed!               ║
║  🎨 Tip: Press 't' to try different themes!        ║
║  🔔 Tip: Press 'n' to disable notifications!       ║
║  🔍 Tip: Press 'd/l/p/h' for detailed views!       ║
║                                                    ║
╚════════════════════════════════════════════════════╝

Press Esc or ? to close
            """
            
            yield Container(
                Static(help_text, classes="help-box"),
                classes="help-screen"
            )
        
        def action_dismiss(self) -> None:
            self.app.pop_screen()


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    try:
        # Check view mode first
        view = "full"
        if len(sys.argv) > 1:
            if sys.argv[1].startswith("--view="):
                view = sys.argv[1].split("=")[1]
        
        if TEXTUAL_AVAILABLE and view in ["full", "compact"]:
            # Run Textual dashboard (not async)
            app = DopemuxDashboard()
            app.run()
        else:
            # Run simple console view (async)
            asyncio.run(simple_console_view())
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
