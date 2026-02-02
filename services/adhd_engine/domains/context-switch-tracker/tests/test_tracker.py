"""
Tests for Context Switch Tracker
"""
import pytest
from tracker import ContextSwitchTracker


class TestContextSwitchTracker:
    """Test suite for ContextSwitchTracker"""
    
    def test_initialization(self):
        """Test tracker can be initialized"""
        tracker = ContextSwitchTracker()
        assert tracker is not None
    
    @pytest.mark.asyncio
    async def test_track_switch(self):
        """Test tracking a context switch"""
        tracker = ContextSwitchTracker()
        result = await tracker.track_switch(
            from_context="file1.py",
            to_context="file2.py",
            user_id="test_user"
        )
        assert "from_context" in result
        assert "to_context" in result
        assert result["from_context"] == "file1.py"
        assert result["to_context"] == "file2.py"
    
    @pytest.mark.asyncio
    async def test_distraction_score_calculation(self):
        """Test distraction score calculation"""
        tracker = ContextSwitchTracker()
        # Simulate multiple switches
        await tracker.track_switch("a", "b", "test")
        await tracker.track_switch("b", "c", "test")
        await tracker.track_switch("c", "d", "test")
        
        score = await tracker.calculate_distraction_score("test")
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0
