"""
Tests for Break Suggestion Engine
"""
import pytest
from datetime import datetime, timedelta
from engine import BreakSuggestionEngine, BreakSuggestion, CognitiveLoadWindow


class TestBreakSuggestionEngine:
    """Test suite for BreakSuggestionEngine"""
    
    def test_initialization(self):
        """Test engine can be initialized"""
        engine = BreakSuggestionEngine()
        assert engine is not None
    
    def test_cognitive_load_window_creation(self):
        """Test cognitive load window tracking"""
        window = CognitiveLoadWindow(window_minutes=25)
        assert window.window_minutes == 25
    
    @pytest.mark.asyncio
    async def test_break_suggestion_generation(self):
        """Test break suggestion can be generated"""
        engine = BreakSuggestionEngine()
        # Simulate high cognitive load condition
        suggestion = await engine.should_suggest_break(
            user_id="test",
            current_cognitive_load=0.8,
            minutes_since_break=60
        )
        assert suggestion is not None
        if suggestion:  # Might be None if no break needed
            assert isinstance(suggestion, BreakSuggestion)
            assert suggestion.priority in ["low", "medium", "high", "critical"]
    
    @pytest.mark.asyncio
    async def test_no_break_needed_low_load(self):
        """Test no break suggested for low cognitive load"""
        engine = BreakSuggestionEngine()
        suggestion = await engine.should_suggest_break(
            user_id="test",
            current_cognitive_load=0.2,
            minutes_since_break=10
        )
        # Low load + recent break = no suggestion
        assert suggestion is None or suggestion.priority == "low"
