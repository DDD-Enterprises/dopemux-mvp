import asyncio
from mobile_push import MobilePushNotifier, PushConfig, NotificationPriority

async def test_push():
    config = PushConfig(
        provider="ntfy",
        ntfy_topic="adhd-alerts-test",
        enabled=True
    )
    
    async with MobilePushNotifier(config) as pusher:
        print("🚀 Sending test break reminder...")
        success = await pusher.send_break_reminder(
            message="Test message: Time for a break! (Phase 10 Verification)",
            priority=NotificationPriority.NORMAL
        )
        if success:
            print("✅ Push notification sent successfully (via ntfy.sh/adhd-alerts-test)")
        else:
            print("❌ Failed to send push notification")

if __name__ == "__main__":
    asyncio.run(test_push())
