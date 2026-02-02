import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.adhd_notifier.mobile_push import (
    MobilePushNotifier,
    PushConfig,
    NotificationPriority,
    send_adhd_notification
)

class TestMobilePushNotifier:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        # Mock the context manager response of session.post
        mock_response = AsyncMock()
        mock_response.status = 200
        session.post.return_value.__aenter__.return_value = mock_response
        return session

    @pytest.mark.asyncio
    async def test_send_ntfy(self, mock_session):
        config = PushConfig(
            provider="ntfy",
            ntfy_topic="test_topic"
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with MobilePushNotifier(config) as notifier:
                success = await notifier.send_break_reminder(
                    "Take a break",
                    NotificationPriority.HIGH,
                    "Break Time"
                )
                
        assert success is True
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        assert "ntfy.sh/test_topic" in args[0]
        assert kwargs['headers']['Priority'] == 'high'
        assert kwargs['headers']['Title'] == 'Break Time'
        assert kwargs['data'] == "Take a break"

    @pytest.mark.asyncio
    async def test_send_pushover(self, mock_session):
        config = PushConfig(
            provider="pushover",
            pushover_api_key="api",
            pushover_user_key="user"
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with MobilePushNotifier(config) as notifier:
                success = await notifier.send_break_reminder(
                    "Msg", 
                    NotificationPriority.URGENT,
                    "Title"
                )
        
        assert success is True
        # Verify priority mapping (URGENT -> 2)
        args, kwargs = mock_session.post.call_args
        assert kwargs['data']['priority'] == 2
        assert kwargs['data']['token'] == "api"

    @pytest.mark.asyncio
    async def test_send_happy(self, mock_session):
        config = PushConfig(
            provider="happy",
            happy_webhook_url="http://happy.local/webhook"
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with MobilePushNotifier(config) as notifier:
                success = await notifier.send_break_reminder(
                    "Msg",
                    NotificationPriority.NORMAL,
                    "Title"
                )
                
        assert success is True
        args, kwargs = mock_session.post.call_args
        assert args[0] == "http://happy.local/webhook"
        assert kwargs['json']['priority'] == "normal"

    @pytest.mark.asyncio
    async def test_disabled_config(self, mock_session):
        config = PushConfig(provider="ntfy", enabled=False)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with MobilePushNotifier(config) as notifier:
                success = await notifier.send_break_reminder("Msg")
                
        assert success is False
        mock_session.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_config(self, mock_session):
        # Pushover without keys
        config = PushConfig(provider="pushover")
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            async with MobilePushNotifier(config) as notifier:
                success = await notifier.send_break_reminder("Msg")
                
        assert success is False
        # Should not attempt post if config missing
        mock_session.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_convenience_function(self, mock_session):
        with patch('aiohttp.ClientSession', return_value=mock_session):
            success = await send_adhd_notification(
                "Message",
                "high",
                "Title",
                provider="ntfy",
                ntfy_topic="my_topic"
            )
            
        assert success is True
        mock_session.post.assert_called()
        args, kwargs = mock_session.post.call_args
        assert "ntfy.sh/my_topic" in args[0]
