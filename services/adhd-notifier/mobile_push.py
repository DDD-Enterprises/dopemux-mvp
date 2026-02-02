"""
Mobile Push Notifications for ADHD Services

Supports multiple providers:
- Ntfy (https://ntfy.sh) - free, open-source
- Pushover - paid, reliable
- Happy - existing integration

ADHD Benefit: Break reminders reach you even when away from computer
"""
import aiohttp
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class PushConfig:
    """Configuration for mobile push provider."""
    provider: str  # "ntfy", "pushover", "happy"
    
    # Ntfy config
    ntfy_topic: Optional[str] = None
    ntfy_server: str = "https://ntfy.sh"
    
    # Pushover config
    pushover_api_key: Optional[str] = None
    pushover_user_key: Optional[str] = None
    
    # Happy config  
    happy_webhook_url: Optional[str] = None
    
    # Common settings
    enabled: bool = True


class MobilePushNotifier:
    """
    Send push notifications to mobile devices.
    
    Multi-provider support for maximum compatibility.
    """
    
    def __init__(self, config: PushConfig):
        """
        Initialize mobile push notifier.
        
        Args:
            config: Push notification configuration
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def send_break_reminder(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        title: str = "ADHD Break Reminder"
    ) -> bool:
        """
        Send break reminder to mobile device.
        
        Args:
            message: Notification message
            priority: Notification priority
            title: Notification title
        
        Returns:
            True if sent successfully
        """
        if not self.config.enabled:
            logger.info(f"📱 [Notifications disabled] {title}: {message}")
            return False
        
        if self.config.provider == "ntfy":
            return await self._send_ntfy(title, message, priority)
        elif self.config.provider == "pushover":
            return await self._send_pushover(title, message, priority)
        elif self.config.provider == "happy":
            return await self._send_happy(title, message, priority)
        else:
            logger.error(f"Unknown provider: {self.config.provider}")
            return False
    
    async def send_energy_alert(
        self,
        energy_level: str,
        recommendation: str
    ) -> bool:
        """
        Send energy level alert.
        
        Args:
            energy_level: Current energy level
            recommendation: Recommended action
        
        Returns:
            True if sent successfully
        """
        title = f"Energy: {energy_level.title()}"
        message = recommendation
        
        priority = (
            NotificationPriority.HIGH if energy_level == "very_low"
            else NotificationPriority.NORMAL
        )
        
        return await self.send_break_reminder(message, priority, title)
    
    async def send_focus_alert(
        self,
        attention_state: str,
        suggestion: str
    ) -> bool:
        """
        Send focus/attention alert.
        
        Args:
            attention_state: Current attention state
            suggestion: Suggested action
        
        Returns:
            True if sent successfully
        """
        title = f"Focus: {attention_state.title()}"
        message = suggestion
        
        priority = (
            NotificationPriority.HIGH if attention_state == "scattered"
            else NotificationPriority.NORMAL
        )
        
        return await self.send_break_reminder(message, priority, title)
    
    async def _send_ntfy(
        self,
        title: str,
        message: str,
        priority: NotificationPriority
    ) -> bool:
        """Send notification via Ntfy."""
        if not self.config.ntfy_topic:
            logger.error("Ntfy topic not configured")
            return False
        
        try:
            url = f"{self.config.ntfy_server}/{self.config.ntfy_topic}"
            
            # Map priority
            ntfy_priority = {
                NotificationPriority.LOW: "low",
                NotificationPriority.NORMAL: "default",
                NotificationPriority.HIGH: "high",
                NotificationPriority.URGENT: "urgent"
            }[priority]
            
            headers = {
                "Title": title,
                "Priority": ntfy_priority,
                "Tags": "hourglass"  # Icon
            }
            
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            async with self._session.post(url, data=message, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"📱 Ntfy sent: {title}")
                    return True
                else:
                    logger.error(f"Ntfy failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ntfy send failed: {e}")
            return False
    
    async def _send_pushover(
        self,
        title: str,
        message: str,
        priority: NotificationPriority
    ) -> bool:
        """Send notification via Pushover."""
        if not self.config.pushover_api_key or not self.config.pushover_user_key:
            logger.error("Pushover API keys not configured")
            return False
        
        try:
            url = "https://api.pushover.net/1/messages.json"
            
            # Map priority (Pushover: -2 to 2)
            pushover_priority = {
                NotificationPriority.LOW: -1,
                NotificationPriority.NORMAL: 0,
                NotificationPriority.HIGH: 1,
                NotificationPriority.URGENT: 2
            }[priority]
            
            data = {
                "token": self.config.pushover_api_key,
                "user": self.config.pushover_user_key,
                "title": title,
                "message": message,
                "priority": pushover_priority
            }
            
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            async with self._session.post(url, data=data) as response:
                if response.status == 200:
                    logger.info(f"📱 Pushover sent: {title}")
                    return True
                else:
                    logger.error(f"Pushover failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Pushover send failed: {e}")
            return False
    
    async def _send_happy(
        self,
        title: str,
        message: str,
        priority: NotificationPriority
    ) -> bool:
        """Send notification via Happy webhook."""
        if not self.config.happy_webhook_url:
            logger.error("Happy webhook URL not configured")
            return False
        
        try:
            payload = {
                "title": title,
                "message": message,
                "priority": priority.value
            }
            
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            async with self._session.post(
                self.config.happy_webhook_url,
                json=payload
            ) as response:
                if response.status in (200, 201, 202):
                    logger.info(f"📱 Happy sent: {title}")
                    return True
                else:
                    logger.error(f"Happy failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Happy send failed: {e}")
            return False


# Convenience function
async def send_adhd_notification(
    message: str,
    priority: str = "normal",
    title: str = "ADHD Engine",
    provider: str = "ntfy",
    **provider_config
) -> bool:
    """
    Send ADHD notification (convenience function).
    
    Args:
        message: Notification message
        priority: "low", "normal", "high", or "urgent"
        title: Notification title
        provider: "ntfy", "pushover", or "happy"
        **provider_config: Provider-specific config (topic, API keys, etc.)
    
    Returns:
        True if sent successfully
    """
    priority_enum = NotificationPriority(priority)
    
    config = PushConfig(
        provider=provider,
        ntfy_topic=provider_config.get('ntfy_topic'),
        pushover_api_key=provider_config.get('pushover_api_key'),
        pushover_user_key=provider_config.get('pushover_user_key'),
        happy_webhook_url=provider_config.get('happy_webhook_url')
    )
    
    async with MobilePushNotifier(config) as notifier:
        return await notifier.send_break_reminder(message, priority_enum, title)
