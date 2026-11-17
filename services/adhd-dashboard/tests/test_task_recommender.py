"""
Tests for Task Recommender
"""
from unittest.mock import patch

import pytest
from task_recommender import TaskRecommender


class TestTaskRecommender:
    """Test suite for TaskRecommender"""
    
    def test_initialization(self):
        """Test recommender can be initialized"""
        recommender = TaskRecommender(user_id="test_user")
        assert recommender is not None
        assert recommender.user_id == "test_user"
    
    def test_generate_recommendation_high_energy(self):
        """Test recommendation for high energy state"""
        recommender = TaskRecommender(user_id="test")
        result = recommender._generate_recommendation("high", "focused")
        assert result is not None
        assert "work_type" in result
        # High energy + focused should recommend complex work
        assert "complex" in result["work_type"].lower() or "coding" in result["work_type"].lower()
    
    def test_generate_recommendation_low_energy(self):
        """Test recommendation for low energy state"""
        recommender = TaskRecommender(user_id="test")
        result = recommender._generate_recommendation("low", "scattered")
        assert result is not None
        assert "work_type" in result
        # Low energy + scattered should recommend simple tasks
        assert "simple" in result["work_type"].lower() or "review" in result["work_type"].lower()
    
    def test_generate_recommendation_medium_energy(self):
        """Test recommendation for medium energy state"""
        recommender = TaskRecommender(user_id="test")
        result = recommender._generate_recommendation("medium", "focused")
        assert result is not None
        assert "work_type" in result
        # Medium energy should have balanced recommendations
        assert result["work_type"] is not None

    def test_headers_include_engine_api_key(self, monkeypatch):
        monkeypatch.setenv("ADHD_ENGINE_API_KEY", "expected-key")
        recommender = TaskRecommender(user_id="test")

        assert recommender._headers == {"X-API-Key": "expected-key"}

    @pytest.mark.asyncio
    async def test_get_current_recommendation_propagates_headers(self):
        captured_headers = []

        class FakeResponse:
            def __init__(self, payload):
                self.status = 200
                self._payload = payload

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def json(self):
                return self._payload

        class FakeSession:
            def __init__(self, *, headers=None, **_kwargs):
                captured_headers.append(headers)

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            def get(self, url):
                if "energy-level" in url:
                    return FakeResponse({"energy_level": "medium"})
                return FakeResponse({"attention_state": "focused"})

        recommender = TaskRecommender(user_id="test", api_key="expected-key")

        with patch("task_recommender.aiohttp.ClientSession", FakeSession):
            result = await recommender.get_current_recommendation()

        assert captured_headers == [{"X-API-Key": "expected-key"}]
        assert result["energy"] == "medium"
        assert result["attention"] == "focused"


class _FakeEngineResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._payload


def _fake_engine_session(energy, attention):
    """Build a ClientSession stand-in answering the two engine reads with (status, payload)."""

    class FakeSession:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        def get(self, url):
            status, payload = energy if "energy-level" in url else attention
            return _FakeEngineResponse(status, payload)

    return FakeSession


ENERGY_PATH = "/api/v1/energy-level/test"
ATTENTION_PATH = "/api/v1/attention-state/test"
UNAUTHORIZED = (401, {"detail": "Invalid API key"})
HIGH_ENERGY = (200, {"energy_level": "high"})
FOCUSED = (200, {"attention_state": "focused"})


class TestUnreadableEngineState:
    """The engine never reports "unknown"; an unreadable state must not become live advice."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "energy, attention, failing_endpoint, failing_detail",
        [
            (UNAUTHORIZED, UNAUTHORIZED, ENERGY_PATH, "HTTP 401"),
            (HIGH_ENERGY, (500, {}), ATTENTION_PATH, "HTTP 500"),
            ((404, {}), FOCUSED, ENERGY_PATH, "HTTP 404"),
            ((200, {}), FOCUSED, ENERGY_PATH, "no energy_level"),
            (HIGH_ENERGY, (200, {}), ATTENTION_PATH, "no attention_state"),
            (HIGH_ENERGY, (200, {"attention_state": None}), ATTENTION_PATH, "no attention_state"),
            ((200, ["not", "an", "object"]), FOCUSED, ENERGY_PATH, "no energy_level"),
        ],
    )
    async def test_unreadable_state_returns_error_not_live_advice(
        self, energy, attention, failing_endpoint, failing_detail
    ):
        recommender = TaskRecommender(user_id="test")

        with patch("task_recommender.aiohttp.ClientSession", _fake_engine_session(energy, attention)):
            result = await recommender.get_current_recommendation()

        assert "recommendation" not in result
        assert result.get("status_chip") != "LIVE"
        assert failing_endpoint in result["error"]
        assert failing_detail in result["error"]

    @pytest.mark.asyncio
    async def test_both_failures_are_named(self):
        recommender = TaskRecommender(user_id="test")
        session = _fake_engine_session((401, {}), (503, {}))

        with patch("task_recommender.aiohttp.ClientSession", session):
            result = await recommender.get_current_recommendation()

        assert "/api/v1/energy-level/test returned HTTP 401" in result["error"]
        assert "/api/v1/attention-state/test returned HTTP 503" in result["error"]

    @pytest.mark.asyncio
    async def test_readable_state_still_returns_live_advice(self):
        recommender = TaskRecommender(user_id="test")
        session = _fake_engine_session((200, {"energy_level": "high"}), (200, {"attention_state": "focused"}))

        with patch("task_recommender.aiohttp.ClientSession", session):
            result = await recommender.get_current_recommendation()

        assert "error" not in result
        assert result["status_chip"] == "LIVE"
        assert result["recommendation"]["work_type"] == "complex_coding"
