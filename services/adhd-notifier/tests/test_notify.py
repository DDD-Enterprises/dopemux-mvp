import pytest
from notify import Notifier

class TestNotifier:
    """Test suite for ADHD Notifier"""
    
    @pytest.mark.asyncio
    async def test_send_break_reminder(self):
        """Test sending break reminder"""
        notifier = Notifier()
        # Mocking or assuming it returns False on non-supported OS or True if supported
        # We just want to ensure method exists and runs without error
        try:
            result = notifier.send_break_reminder(duration_minutes=25, urgency="normal")
            assert result in [True, False]
        except Exception as e:
            pytest.fail(f"Notifier raised exception: {e}")

    @pytest.mark.asyncio
    async def test_send_hyperfocus_alert(self):
        """Test sending hyperfocus alert"""
        notifier = Notifier()
        try:
            result = notifier.send_hyperfocus_alert(duration_minutes=60)
            assert result in [True, False]
        except Exception as e:
            pytest.fail(f"Notifier raised exception: {e}")
