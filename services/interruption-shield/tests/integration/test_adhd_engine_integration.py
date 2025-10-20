"""
Integration tests for ADHD Engine client.

Tests the ADHDEngineClient against a mock ADHD Engine server
to validate HTTP polling, state changes, and callback invocation.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from interruption_shield.integrations import ADHDEngineClient, AttentionState


class MockADHDEngine:
    """Mock ADHD Engine HTTP server for testing."""

    def __init__(self):
        self.current_state = AttentionState.SCATTERED
        self.request_count = 0
        self.responses = []

    async def get_current_state(self):
        """Simulate ADHD Engine /api/v1/state/current endpoint."""
        self.request_count += 1
        return {"attention_state": self.current_state.value, "timestamp": datetime.now().isoformat()}

    def set_state(self, state: AttentionState):
        """Change the mocked attention state."""
        self.current_state = state
        self.responses.append(state)


@pytest.fixture
def mock_adhd_engine():
    """Create mock ADHD Engine for testing."""
    return MockADHDEngine()


@pytest_asyncio.fixture
async def adhd_client():
    """Create ADHD Engine client with fast polling for tests."""
    client = ADHDEngineClient(base_url="http://localhost:8095", poll_interval=0.1)  # 100ms for tests
    yield client
    await client.stop()


class TestADHDEngineClient:
    """Test ADHDEngineClient integration."""

    @pytest.mark.asyncio
    async def test_client_start_and_stop(self, adhd_client, mock_adhd_engine):
        """Test client can start and stop cleanly."""
        # Mock aiohttp.ClientSession.get
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=await mock_adhd_engine.get_current_state())
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response

            # Start client
            await adhd_client.start()

            # Allow initial poll
            await asyncio.sleep(0.15)

            # Verify client started
            assert adhd_client.session is not None
            assert adhd_client.polling_task is not None
            assert adhd_client.current_state == AttentionState.SCATTERED

            # Stop client
            await adhd_client.stop()

            # Verify client stopped
            assert adhd_client.polling_task.cancelled()

    @pytest.mark.asyncio
    async def test_state_change_detection(self, adhd_client, mock_adhd_engine):
        """Test client detects attention state changes."""
        state_changes = []

        async def on_state_change(new_state: AttentionState, user_id: str):
            state_changes.append((new_state, user_id))

        await adhd_client.subscribe_attention_state(on_state_change)

        # Mock state changes
        with patch("aiohttp.ClientSession.get") as mock_get:
            # First poll: SCATTERED
            mock_response_1 = AsyncMock()
            mock_response_1.json.return_value = {"attention_state": "scattered"}
            mock_response_1.raise_for_status.return_value = None

            # Second poll: FOCUSED
            mock_response_2 = AsyncMock()
            mock_response_2.json.return_value = {"attention_state": "focused"}
            mock_response_2.raise_for_status.return_value = None

            # Third poll: HYPERFOCUS
            mock_response_3 = AsyncMock()
            mock_response_3.json.return_value = {"attention_state": "hyperfocus"}
            mock_response_3.raise_for_status.return_value = None

            mock_get.return_value.__aenter__.side_effect = [
                mock_response_1,
                mock_response_2,
                mock_response_3,
            ]

            await adhd_client.start()

            # Wait for 3 polls (0.3 seconds with 0.1s interval)
            await asyncio.sleep(0.35)

            await adhd_client.stop()

        # Verify state changes detected
        assert len(state_changes) >= 2  # At least FOCUSED and HYPERFOCUS
        assert any(state == AttentionState.FOCUSED for state, _ in state_changes)

    @pytest.mark.asyncio
    async def test_multiple_callbacks(self, adhd_client, mock_adhd_engine):
        """Test multiple callbacks are invoked on state change."""
        callback1_called = []
        callback2_called = []

        async def callback1(state: AttentionState, user_id: str):
            callback1_called.append(state)

        async def callback2(state: AttentionState, user_id: str):
            callback2_called.append(state)

        await adhd_client.subscribe_attention_state(callback1)
        await adhd_client.subscribe_attention_state(callback2)

        # Mock state change
        with patch("aiohttp.ClientSession.get") as mock_get:
            # First: SCATTERED
            mock_response_1 = AsyncMock()
            mock_response_1.json.return_value = {"attention_state": "scattered"}
            mock_response_1.raise_for_status.return_value = None

            # Second: FOCUSED
            mock_response_2 = AsyncMock()
            mock_response_2.json.return_value = {"attention_state": "focused"}
            mock_response_2.raise_for_status.return_value = None

            mock_get.return_value.__aenter__.side_effect = [mock_response_1, mock_response_2]

            await adhd_client.start()
            await asyncio.sleep(0.25)  # 2 polls
            await adhd_client.stop()

        # Both callbacks should be invoked
        assert len(callback1_called) >= 1
        assert len(callback2_called) >= 1
        assert callback1_called == callback2_called  # Same states received

    @pytest.mark.asyncio
    async def test_error_recovery(self, adhd_client):
        """Test client recovers from ADHD Engine API errors."""
        state_changes = []

        async def on_state_change(state: AttentionState, user_id: str):
            state_changes.append(state)

        await adhd_client.subscribe_attention_state(on_state_change)

        with patch("aiohttp.ClientSession.get") as mock_get:
            # First poll: Network error
            mock_get.return_value.__aenter__.side_effect = Exception("Network error")

            await adhd_client.start()
            await asyncio.sleep(0.15)  # 1 poll (error)

            # Client should still be polling (not crashed)
            assert not adhd_client.polling_task.cancelled()

            # Second poll: Success (FOCUSED)
            mock_response = AsyncMock()
            mock_response.json.return_value = {"attention_state": "focused"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value.__aenter__.side_effect = [mock_response]

            await asyncio.sleep(0.15)  # 1 more poll (success)
            await adhd_client.stop()

        # Verify recovery: state change detected after error
        assert len(state_changes) >= 1
        assert any(state == AttentionState.FOCUSED for state in state_changes)

    @pytest.mark.asyncio
    async def test_callback_exception_handling(self, adhd_client):
        """Test client handles exceptions in callbacks gracefully."""
        good_callback_called = []
        bad_callback_called = []

        async def good_callback(state: AttentionState, user_id: str):
            good_callback_called.append(state)

        async def bad_callback(state: AttentionState, user_id: str):
            bad_callback_called.append(state)
            raise Exception("Callback error")

        await adhd_client.subscribe_attention_state(good_callback)
        await adhd_client.subscribe_attention_state(bad_callback)

        with patch("aiohttp.ClientSession.get") as mock_get:
            # First: SCATTERED
            mock_response_1 = AsyncMock()
            mock_response_1.json.return_value = {"attention_state": "scattered"}
            mock_response_1.raise_for_status.return_value = None

            # Second: FOCUSED
            mock_response_2 = AsyncMock()
            mock_response_2.json.return_value = {"attention_state": "focused"}
            mock_response_2.raise_for_status.return_value = None

            mock_get.return_value.__aenter__.side_effect = [mock_response_1, mock_response_2]

            await adhd_client.start()
            await asyncio.sleep(0.25)  # 2 polls
            await adhd_client.stop()

        # Both callbacks should be attempted
        assert len(good_callback_called) >= 1
        assert len(bad_callback_called) >= 1  # Bad callback was called (but raised)

    @pytest.mark.asyncio
    async def test_get_current_state(self, adhd_client):
        """Test get_current_state returns current attention state."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"attention_state": "hyperfocus"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value.__aenter__.return_value = mock_response

            await adhd_client.start()
            await asyncio.sleep(0.15)  # 1 poll

            current = await adhd_client.get_current_state()
            assert current == AttentionState.HYPERFOCUS

            await adhd_client.stop()

    @pytest.mark.asyncio
    async def test_polling_interval(self, adhd_client):
        """Test client respects polling interval."""
        poll_times = []

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"attention_state": "scattered"}
            mock_response.raise_for_status.return_value = None

            async def record_poll(*args, **kwargs):
                poll_times.append(datetime.now())
                return mock_response

            mock_get.return_value.__aenter__ = record_poll

            await adhd_client.start()
            await asyncio.sleep(0.35)  # Should get ~3 polls (0.1s interval)
            await adhd_client.stop()

        # Verify polling happened at ~0.1s intervals
        assert len(poll_times) >= 2

        if len(poll_times) >= 2:
            intervals = [(poll_times[i + 1] - poll_times[i]).total_seconds() for i in range(len(poll_times) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            assert 0.08 <= avg_interval <= 0.15  # Allow 50ms tolerance


@pytest.mark.asyncio
async def test_full_integration_scenario():
    """
    Full integration test simulating real ADHD Engine interaction.

    Scenario:
    1. User starts in SCATTERED state
    2. Begins deep work → FOCUSED
    3. Enters flow state → HYPERFOCUS
    4. Takes break → FATIGUED
    5. Recovers → FOCUSED
    """
    state_sequence = []

    async def track_states(state: AttentionState, user_id: str):
        state_sequence.append(state)

    client = ADHDEngineClient(poll_interval=0.05)  # 50ms for fast test
    await client.subscribe_attention_state(track_states)

    with patch("aiohttp.ClientSession.get") as mock_get:
        # Simulate state progression
        responses = [
            {"attention_state": "scattered"},
            {"attention_state": "focused"},
            {"attention_state": "focused"},  # Stays focused
            {"attention_state": "hyperfocus"},
            {"attention_state": "hyperfocus"},  # Stays hyperfocus
            {"attention_state": "fatigued"},
            {"attention_state": "focused"},
        ]

        response_iter = iter(responses)

        async def next_response(*args, **kwargs):
            try:
                data = next(response_iter)
                mock_resp = AsyncMock()
                mock_resp.json.return_value = data
                mock_resp.raise_for_status.return_value = None
                return mock_resp
            except StopIteration:
                # Keep returning last state
                mock_resp = AsyncMock()
                mock_resp.json.return_value = {"attention_state": "focused"}
                mock_resp.raise_for_status.return_value = None
                return mock_resp

        mock_get.return_value.__aenter__ = next_response

        await client.start()
        await asyncio.sleep(0.4)  # 7-8 polls (0.05s interval)
        await client.stop()

    # Verify state transitions
    assert AttentionState.FOCUSED in state_sequence
    assert AttentionState.HYPERFOCUS in state_sequence
    assert AttentionState.FATIGUED in state_sequence

    # Verify sequence makes sense (SCATTERED → FOCUSED → HYPERFOCUS → FATIGUED → FOCUSED)
    focused_idx = state_sequence.index(AttentionState.FOCUSED)
    hyperfocus_idx = state_sequence.index(AttentionState.HYPERFOCUS)
    fatigued_idx = state_sequence.index(AttentionState.FATIGUED)

    assert focused_idx < hyperfocus_idx  # FOCUSED before HYPERFOCUS
    assert hyperfocus_idx < fatigued_idx  # HYPERFOCUS before FATIGUED
