#!/usr/bin/env python3
"""
Happy CLI - Mobile Notification Service for Dopemux ADHD Engine
Provides mobile notifications for task updates, break suggestions, and energy alerts.
"""

import argparse
import asyncio
import httpx
import json
import os
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HappyCLI:
    """Happy CLI - Mobile notification service for ADHD Engine"""

    def __init__(self, adhd_engine_url: str = "http://localhost:8095"):
        self.adhd_engine_url = adhd_engine_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)
        # In a real implementation, this would connect to mobile push services
        # For now, we'll simulate notifications via console/logs
        self.mobile_clients = []  # Would store mobile device tokens/APNs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def notify_task_update(self, user_id: str, task_title: str, status: str) -> Dict[str, Any]:
        """Send notification for task status update"""
        message = f"Task '{task_title}' status changed to: {status}"

        # Get ADHD context for personalized messaging
        context = await self._get_adhd_context(user_id)

        notification = {
            "type": "task_update",
            "user_id": user_id,
            "title": "Task Update",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }

        # Simulate sending to mobile devices
        await self._send_mobile_notification(notification)
        logger.info(f"📱 Task notification sent: {message}")

        return {"status": "sent", "notification": notification}

    async def notify_break_suggestion(self, user_id: str, duration_minutes: int, activity: str) -> Dict[str, Any]:
        """Send break suggestion notification"""
        message = f"Time for a {duration_minutes}-minute break! Try: {activity}"

        context = await self._get_adhd_context(user_id)

        notification = {
            "type": "break_suggestion",
            "user_id": user_id,
            "title": "Break Time! ⏰",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "break_duration": duration_minutes,
            "suggested_activity": activity
        }

        await self._send_mobile_notification(notification)
        logger.info(f"📱 Break notification sent: {message}")

        return {"status": "sent", "notification": notification}

    async def notify_energy_alert(self, user_id: str, energy_level: str, suggestions: list) -> Dict[str, Any]:
        """Send energy level alert"""
        message = f"Your energy level is {energy_level}. Suggestions: {', '.join(suggestions[:2])}"

        context = await self._get_adhd_context(user_id)

        notification = {
            "type": "energy_alert",
            "user_id": user_id,
            "title": "Energy Update ⚡",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "energy_level": energy_level,
            "suggestions": suggestions
        }

        await self._send_mobile_notification(notification)
        logger.info(f"📱 Energy notification sent: {message}")

        return {"status": "sent", "notification": notification}

    async def _get_adhd_context(self, user_id: str) -> Dict[str, Any]:
        """Get ADHD context from engine for personalized notifications"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.adhd_engine_url}/api/v1/attention-state/{user_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Could not get ADHD context: {e}")

        return {"attention_state": "unknown", "focus_duration": 0}

    async def _send_mobile_notification(self, notification: Dict[str, Any]) -> None:
        """Send notification to mobile devices (simulated)"""
        # In a real implementation, this would:
        # 1. Push to Apple Push Notification service (APNs)
        # 2. Push to Firebase Cloud Messaging (FCM)
        # 3. Send SMS via Twilio
        # 4. Use Web Push API for web notifications

        # For now, simulate by logging and storing
        logger.info(f"📱 Mobile notification: {notification['title']} - {notification['message']}")

        # Would store in database for delivery tracking
        # await self._store_notification(notification)

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to ADHD Engine"""
        try:
            response = await self.client.get(f"{self.adhd_engine_url}/health")
            if response.status_code == 200:
                return {"status": "connected", "engine_health": response.json()}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Happy CLI - Mobile Notification Service")
    parser.add_argument("--adhd-engine-url", default="http://localhost:8095",
                       help="ADHD Engine URL")
    parser.add_argument("--user-id", default="default_user",
                       help="User ID for notifications")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Test connection
    subparsers.add_parser("test", help="Test ADHD Engine connection")

    # Task update notification
    task_parser = subparsers.add_parser("task-update", help="Send task update notification")
    task_parser.add_argument("task_title", help="Task title")
    task_parser.add_argument("status", help="New task status")

    # Break suggestion
    break_parser = subparsers.add_parser("break", help="Send break suggestion")
    break_parser.add_argument("--duration", type=int, default=5, help="Break duration in minutes")
    break_parser.add_argument("--activity", default="Light stretching", help="Suggested activity")

    # Energy alert
    energy_parser = subparsers.add_parser("energy", help="Send energy alert")
    energy_parser.add_argument("level", help="Energy level (high/medium/low)")
    energy_parser.add_argument("--suggestions", nargs="+", default=["Take a walk", "Drink water"],
                              help="Energy suggestions")

    args = parser.parse_args()

    async def run():
        async with HappyCLI(args.adhd_engine_url) as cli:
            if args.command == "test":
                result = await cli.test_connection()
                print(json.dumps(result, indent=2))

            elif args.command == "task-update":
                result = await cli.notify_task_update(args.user_id, args.task_title, args.status)
                print(f"✅ Task notification sent: {result['notification']['message']}")

            elif args.command == "break":
                result = await cli.notify_break_suggestion(args.user_id, args.duration, args.activity)
                print(f"✅ Break notification sent: {result['notification']['message']}")

            elif args.command == "energy":
                result = await cli.notify_energy_alert(args.user_id, args.level, args.suggestions)
                print(f"✅ Energy notification sent: {result['notification']['message']}")

    if args.command:
        asyncio.run(run())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()