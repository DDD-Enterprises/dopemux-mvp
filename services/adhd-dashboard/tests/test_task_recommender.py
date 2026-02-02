"""
Tests for Task Recommender
"""
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
