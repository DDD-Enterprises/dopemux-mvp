"""
ADHD Output Dispatcher - Routes findings to notification channels.

Phase 7: Full I/O Wiring

Channels:
- Console (stdout with ANSI colors)
- Tmux Status (tmux set-option status-right)
- Tmux Popup (tmux display-popup for urgent)
- Voice (macOS say command)
- Dashboard (WebSocket, optional)
- Push (Ntfy, optional)
"""

import asyncio
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass, field
from datetime import datetime

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


class OutputChannel(ABC):
    """Abstract base class for output channels."""
    
    @abstractmethod
    async def send(self, finding: ADHDFinding) -> bool:
        """Send finding to this channel. Returns True if successful."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name for logging."""
        pass


class ConsoleChannel(OutputChannel):
    """Print findings to stdout with ANSI colors."""
    
    COLORS = {
        "low": "\033[32m",      # Green
        "medium": "\033[33m",   # Yellow
        "high": "\033[91m",     # Red
        "critical": "\033[95m", # Magenta
    }
    RESET = "\033[0m"
    
    ICONS = {
        "low": "ℹ️ ",
        "medium": "⚠️ ",
        "high": "🚨",
        "critical": "🆘",
    }
    
    @property
    def name(self) -> str:
        return "console"
    
    async def send(self, finding: ADHDFinding) -> bool:
        try:
            color = self.COLORS.get(finding.severity, "")
            icon = self.ICONS.get(finding.severity, "")
            print(f"{color}[ADHD {icon}] {finding.message}{self.RESET}")
            return True
        except Exception as e:
            logger.warning(f"Console channel error: {e}")
            return False


class TmuxStatusChannel(OutputChannel):
    """Update tmux status bar with current ADHD state."""
    
    ICONS = {
        "energy_low": "⚡↓",
        "hyperfocus_warning_90": "🔥90",
        "hyperfocus_warning_120": "🔥‼️",
        "hyperfocus_detected": "🔥",
        "overwhelm_detected": "😰",
        "overwhelm_critical": "🆘",
        "procrastination_detected": "🐇",
        "social_battery_low": "🔋↓",
        "context_restored": "📍",
        "task_completed": "✅",
    }
    
    @property
    def name(self) -> str:
        return "tmux_status"
    
    async def send(self, finding: ADHDFinding) -> bool:
        # Only update status for specific finding types
        if finding.finding_type not in self.ICONS:
            return False
        
        try:
            icon = self.ICONS.get(finding.finding_type, "📢")
            # Truncate message for status bar
            short_msg = finding.message[:30] + "..." if len(finding.message) > 30 else finding.message
            status_text = f"#{icon} {short_msg}"
            
            result = subprocess.run(
                ["tmux", "set-option", "-g", "status-right", status_text],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.debug("tmux not available")
            return False
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            logger.warning(f"Tmux status channel error: {e}")
            return False


class TmuxPopupChannel(OutputChannel):
    """Show tmux popup for urgent findings."""
    
    @property
    def name(self) -> str:
        return "tmux_popup"
    
    async def send(self, finding: ADHDFinding) -> bool:
        # Only show popup for high/critical severity
        if finding.severity not in ["high", "critical"]:
            return False
        
        try:
            # Build popup content
            actions_text = ""
            if finding.recommended_actions:
                actions_text = f"\n\nRecommended:\n• " + "\n• ".join(finding.recommended_actions[:3])
            
            popup_content = f"{finding.message}{actions_text}"
            
            # Use tmux display-popup
            result = subprocess.run(
                [
                    "tmux", "display-popup",
                    "-w", "60",  # Width
                    "-h", "12",  # Height
                    "-T", f"⚠️ ADHD Alert: {finding.finding_type}",
                    "-E",  # Close on any key
                    f"echo '{popup_content}'; read -n 1 -s"
                ],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.debug("tmux not available")
            return False
        except subprocess.TimeoutExpired:
            return True  # Popup is intentionally blocking
        except Exception as e:
            logger.warning(f"Tmux popup channel error: {e}")
            return False


class VoiceChannel(OutputChannel):
    """Speak findings using macOS say command (or compatible TTS)."""
    
    def __init__(self, voice: str = "Samantha", rate: int = 180, enabled: bool = True):
        """
        Initialize voice channel.
        
        Args:
            voice: macOS voice name (Samantha, Alex, etc.)
            rate: Words per minute (default 180)
            enabled: Whether voice is enabled (can be toggled)
        """
        self.voice = voice
        self.rate = rate
        self.enabled = enabled
        self._tts_available = self._check_tts()
    
    def _check_tts(self) -> bool:
        """Check if TTS is available."""
        try:
            result = subprocess.run(
                ["which", "say"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @property
    def name(self) -> str:
        return "voice"
    
    async def send(self, finding: ADHDFinding) -> bool:
        if not self.enabled or not self._tts_available:
            return False
        
        # Only speak for medium+ severity
        if finding.severity not in ["medium", "high", "critical"]:
            return False
        
        try:
            # Clean message for speech (remove emojis)
            message = finding.message
            for emoji in ["⚠️", "🎉", "🔥", "😰", "🆘", "✅", "📍", "⚡", "🐇", "🔋"]:
                message = message.replace(emoji, "")
            message = message.strip()
            
            # Add urgency for critical
            if finding.severity == "critical":
                message = f"Attention! {message}"
            
            # Fire-and-forget async speech
            proc = await asyncio.create_subprocess_exec(
                "say", "-v", self.voice, "-r", str(self.rate), message,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            # Don't wait - let it speak in background
            asyncio.create_task(self._wait_for_speech(proc))
            return True
        except Exception as e:
            logger.warning(f"Voice channel error: {e}")
            return False
    
    async def _wait_for_speech(self, proc):
        """Wait for speech subprocess to complete (background task)."""
        try:
            await asyncio.wait_for(proc.wait(), timeout=30)
        except asyncio.TimeoutError:
            proc.terminate()


class DashboardWebSocketChannel(OutputChannel):
    """Push findings to dashboard via WebSocket manager."""
    
    def __init__(self, ws_manager=None):
        """
        Initialize dashboard channel.
        
        Args:
            ws_manager: WebSocket connection manager with broadcast() method
        """
        self.ws_manager = ws_manager
    
    @property
    def name(self) -> str:
        return "dashboard"
    
    async def send(self, finding: ADHDFinding) -> bool:
        if not self.ws_manager:
            return False
        
        try:
            await self.ws_manager.broadcast({
                "type": "adhd_finding",
                "data": {
                    "finding_type": finding.finding_type,
                    "severity": finding.severity,
                    "message": finding.message,
                    "actions": finding.recommended_actions,
                    "timestamp": finding.timestamp,
                    "source": finding.source_event
                }
            })
            return True
        except Exception as e:
            logger.warning(f"Dashboard channel error: {e}")
            return False


class NtfyPushChannel(OutputChannel):
    """Send push notifications via Ntfy.sh."""
    
    def __init__(self, topic: str = "adhd-dopemux", enabled: bool = False):
        """
        Initialize Ntfy push channel.
        
        Args:
            topic: Ntfy topic name
            enabled: Whether push is enabled (disabled by default)
        """
        self.topic = topic
        self.base_url = "https://ntfy.sh"
        self.enabled = enabled
    
    @property
    def name(self) -> str:
        return "push"
    
    async def send(self, finding: ADHDFinding) -> bool:
        if not self.enabled:
            return False
        
        # Only push for high/critical
        if finding.severity not in ["high", "critical"]:
            return False
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                priority = "urgent" if finding.severity == "critical" else "high"
                await client.post(
                    f"{self.base_url}/{self.topic}",
                    headers={
                        "Title": f"ADHD: {finding.finding_type}",
                        "Priority": priority,
                        "Tags": "brain"
                    },
                    content=finding.message,
                    timeout=5
                )
            return True
        except ImportError:
            logger.debug("httpx not available for push notifications")
            return False
        except Exception as e:
            logger.warning(f"Ntfy push channel error: {e}")
            return False


class ADHDOutputDispatcher:
    """
    Central dispatcher for routing ADHD findings to output channels.
    
    Routing rules determine which channels receive each finding type.
    Channels can be enabled/disabled at runtime.
    """
    
    def __init__(
        self,
        enable_voice: bool = True,
        enable_push: bool = False,
        ws_manager=None
    ):
        """
        Initialize output dispatcher.
        
        Args:
            enable_voice: Enable voice output (default True)
            enable_push: Enable push notifications (default False)
            ws_manager: Optional WebSocket manager for dashboard
        """
        self.channels: Dict[str, OutputChannel] = {
            "console": ConsoleChannel(),
            "tmux_status": TmuxStatusChannel(),
            "tmux_popup": TmuxPopupChannel(),
            "voice": VoiceChannel(enabled=enable_voice),
            "dashboard": DashboardWebSocketChannel(ws_manager=ws_manager),
            "push": NtfyPushChannel(enabled=enable_push),
        }
        
        # Routing rules: finding_type -> list of channel names
        self.routing: Dict[str, List[str]] = {
            # Low severity - console only
            "context_restored": ["console"],
            "context_reminder": ["console"],
            "task_completed": ["console", "voice"],
            
            # Medium severity - console + selective voice
            "procrastination_detected": ["console", "tmux_status"],
            "energy_low": ["console", "voice", "tmux_status", "dashboard"],
            "hyperfocus_warning_90": ["console", "voice", "tmux_status"],
            "social_battery_low": ["console", "voice", "dashboard"],
            
            # High severity - more aggressive channels
            "hyperfocus_warning_120": ["console", "voice", "tmux_popup", "dashboard"],
            "hyperfocus_detected": ["console", "tmux_status", "dashboard"],
            "overwhelm_detected": ["console", "voice", "tmux_popup", "dashboard"],
            
            # Critical - everything including push
            "overwhelm_critical": ["console", "voice", "tmux_popup", "push", "dashboard"],
        }
        
        # Default routing for unknown finding types
        self.default_channels = ["console", "dashboard"]
        
        # Dispatch statistics
        self.stats = {
            "dispatched": 0,
            "by_channel": {},
            "by_severity": {},
            "failures": 0
        }
    
    async def dispatch(self, finding: ADHDFinding) -> int:
        """
        Dispatch finding to configured channels.
        
        Args:
            finding: ADHDFinding to dispatch
            
        Returns:
            Number of channels successfully notified
        """
        channels = self.routing.get(finding.finding_type, self.default_channels)
        
        notified = 0
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    if await channel.send(finding):
                        notified += 1
                        # Update stats
                        self.stats["by_channel"][channel_name] = \
                            self.stats["by_channel"].get(channel_name, 0) + 1
                except Exception as e:
                    logger.warning(f"Channel {channel_name} failed: {e}")
                    self.stats["failures"] += 1
        
        # Update global stats
        self.stats["dispatched"] += 1
        self.stats["by_severity"][finding.severity] = \
            self.stats["by_severity"].get(finding.severity, 0) + 1
        
        logger.debug(f"📢 Dispatched {finding.finding_type} to {notified}/{len(channels)} channels")
        return notified
    
    def enable_channel(self, channel_name: str, enabled: bool = True):
        """Enable or disable a channel at runtime."""
        channel = self.channels.get(channel_name)
        if hasattr(channel, 'enabled'):
            channel.enabled = enabled
            logger.info(f"Channel {channel_name} {'enabled' if enabled else 'disabled'}")
    
    def add_routing(self, finding_type: str, channels: List[str]):
        """Add or update routing for a finding type."""
        self.routing[finding_type] = channels
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatch statistics."""
        return self.stats.copy()


def create_output_dispatcher(
    enable_voice: bool = True,
    enable_push: bool = False,
    ws_manager=None
) -> ADHDOutputDispatcher:
    """
    Factory function to create configured output dispatcher.
    
    Args:
        enable_voice: Enable voice TTS output
        enable_push: Enable push notifications (requires ntfy setup)
        ws_manager: WebSocket manager for dashboard updates
        
    Returns:
        Configured ADHDOutputDispatcher
    """
    dispatcher = ADHDOutputDispatcher(
        enable_voice=enable_voice,
        enable_push=enable_push,
        ws_manager=ws_manager
    )
    logger.info("✅ ADHD Output Dispatcher initialized with channels: " + 
                ", ".join(dispatcher.channels.keys()))
    return dispatcher
