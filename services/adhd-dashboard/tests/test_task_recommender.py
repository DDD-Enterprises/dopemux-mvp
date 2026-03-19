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
