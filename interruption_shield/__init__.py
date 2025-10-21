"""
Environmental Interruption Shield - Component 7
ADHD-optimized interruption management system that automatically activates
environmental shields during focused work sessions.

Core Logic:
- Parallel shield activation (DND + Slack + Notifications)
- False positive detection (15-minute productivity monitoring)
- ConPort event logging for shield state changes
- Comprehensive unit tests for coordinator functionality
"""

__version__ = "0.1.0"
__component__ = "Environmental Interruption Shield"

from .coordinator import ShieldCoordinator
from .shields import DNDShield, SlackShield, NotificationShield
from .monitor import ProductivityMonitor

__all__ = [
    "ShieldCoordinator",
    "DNDShield",
    "SlackShield",
    "NotificationShield",
    "ProductivityMonitor"
]