"""
Integration tests for ADHD Engine FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Import app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from models import ADHDProfile, EnergyLevel, AttentionState


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_initialized_engine():
    """Mock initialized engine for API tests."""
    from main import engine as global_engine

    mock_engine = MagicMock()
    mock_engine.current_energy_levels = {"test_user": EnergyLevel.MEDIUM}
    mock_engine.current_attention_states = {"test_user": AttentionState.FOCUSED}
    mock_engine.user_profiles = {}
    mock_engine.accommodation_stats = {
        "recommendations_made": 0,
        "breaks_suggested": 0,
        "energy_optimizations": 0,
        "cognitive_load_reductions": 0,
        "context_switch_preventions": 0,
        "hyperfocus_protections": 0
    }
    mock_engine.monitoring_tasks = [MagicMock(done=MagicMock(return_value=False)) for _ in range(6)]

    # Mock assess_task_suitability
    mock_engine.assess_task_suitability = AsyncMock(return_value={
        "suitability_score": 0.85,
        "energy_match": 0.9,
        "attention_compatibility": 0.8,
        "cognitive_load": 0.6,
        "cognitive_load_level": "moderate",
        "recommendations": [],
        "accommodations_needed": [],
        "optimal_timing": {"is_optimal_time": True},
        "adhd_insights": {
            "hyperfocus_risk": "low",
            "distraction_risk": "low",
            "context_switch_impact": "medium"
        }
    })

    # Mock health check
    mock_engine.get_accommodation_health = AsyncMock(return_value={
        "overall_status": "✅ Ready",
        "components": {
            "redis_persistence": "🟢 Connected",
            "monitors_active": "6/6",
            "user_profiles": 0
        },
        "accommodation_stats": mock_engine.accommodation_stats,
        "current_state": {
            "energy_levels": {},
            "attention_states": {},
            "active_accommodations": {}
        },
        "effectiveness_metrics": {
            "accommodation_rate": "0.0 per user",
            "cognitive_load_reductions": 0,
            "break_compliance": "monitoring_active"
        }
    })

    return mock_engine


class TestRootEndpoint:
    """Test root and health endpoints."""

    def test_root_endpoint(self, client):
        """Root endpoint should return service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "ADHD Accommodation Engine"
        assert data["version"] == "1.0.0"
        assert "docs" in data


class TestTaskAssessment:
    """Test task assessment endpoint."""

    def test_assess_task_valid_request(self, client, mock_initialized_engine):
        """Should assess task and return suitability scores."""
        with patch('main.engine', mock_initialized_engine):
            response = client.post("/api/v1/assess-task", json={
                "user_id": "test_user",
                "task_id": "task_123",
                "task_data": {
                    "complexity_score": 0.6,
                    "estimated_minutes": 25,
                    "description": "implement authentication",
                    "dependencies": []
                }
            })

            assert response.status_code == 200
            data = response.json()

            assert "suitability_score" in data
            assert "energy_match" in data
            assert "cognitive_load" in data
            assert 0.0 <= data["suitability_score"] <= 1.0

    def test_assess_task_invalid_complexity(self, client):
        """Should reject invalid complexity score."""
        response = client.post("/api/v1/assess-task", json={
            "user_id": "test_user",
            "task_id": "task_123",
            "task_data": {
                "complexity_score": 1.5,  # Invalid: > 1.0
                "estimated_minutes": 25,
                "description": "task",
                "dependencies": []
            }
        })

        assert response.status_code == 422  # Validation error


class TestEnergyAndAttention:
    """Test energy level and attention state endpoints."""

    def test_get_energy_level(self, client, mock_initialized_engine):
        """Should return user's energy level."""
        with patch('main.engine', mock_initialized_engine):
            response = client.get("/api/v1/energy-level/test_user")

            assert response.status_code == 200
            data = response.json()

            assert data["energy_level"] == "medium"
            assert "last_updated" in data

    def test_get_attention_state(self, client, mock_initialized_engine):
        """Should return user's attention state."""
        with patch('main.engine', mock_initialized_engine):
            response = client.get("/api/v1/attention-state/test_user")

            assert response.status_code == 200
            data = response.json()

            assert data["attention_state"] == "focused"
            assert "indicators" in data


class TestBreakRecommendation:
    """Test break recommendation endpoint."""

    def test_recommend_break_needed(self, client, mock_initialized_engine):
        """Should recommend break after optimal duration."""
        with patch('main.engine', mock_initialized_engine):
            mock_initialized_engine.user_profiles = {
                "test_user": ADHDProfile(user_id="test_user", optimal_task_duration=25)
            }

            response = client.post("/api/v1/recommend-break", json={
                "user_id": "test_user",
                "work_duration": 30.0  # Over optimal duration
            })

            assert response.status_code == 200
            data = response.json()

            assert data["break_needed"] is True
            assert "suggestions" in data
            assert len(data["suggestions"]) > 0


class TestUserProfile:
    """Test user profile management."""

    def test_create_profile(self, client, mock_initialized_engine):
        """Should create user ADHD profile."""
        with patch('main.engine', mock_initialized_engine):
            response = client.post("/api/v1/user-profile", json={
                "user_id": "new_user",
                "hyperfocus_tendency": 0.8,
                "optimal_task_duration": 20
            })

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == "new_user"
            assert data["profile_created"] is True
