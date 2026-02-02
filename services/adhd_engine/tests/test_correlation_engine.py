import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from services.adhd_engine.correlation_engine import CrossServiceCorrelator, CorrelationInsight

class TestCrossServiceCorrelator:
    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def correlator(self, mock_redis):
        return CrossServiceCorrelator(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_correlate_energy_complexity(self, correlator):
        """Test energy-complexity correlation logic."""
        # Mock internal data fetchers
        with patch.object(correlator, '_fetch_energy_history', return_value=[{'val': 1}]), \
             patch.object(correlator, '_fetch_complexity_history', return_value=[{'val': 1}]), \
             patch.object(correlator, '_correlate_energy_complexity_success', return_value=0.8):
            
            insight = await correlator.correlate_energy_complexity("user1")
            
            assert isinstance(insight, CorrelationInsight)
            assert insight.insight_type == "task_matching"
            assert insight.confidence == 0.8
            assert "Strong correlation" in insight.description

    @pytest.mark.asyncio
    async def test_correlate_attention_switches_distraction(self, correlator):
        """Test distraction pattern detection."""
        # Mock finding a high switch count pattern
        mock_pattern = {
            'pattern': 'high_switch_scatter',
            'switch_count': 10,
            'confidence': 0.75
        }
        
        with patch.object(correlator, '_fetch_attention_history', return_value=[]), \
             patch.object(correlator, '_fetch_switch_history', return_value=[]), \
             patch.object(correlator, '_identify_distraction_pattern', return_value=mock_pattern):
            
            insight = await correlator.correlate_attention_switches("user1")
            
            assert insight.insight_type == "distraction_pattern"
            assert insight.confidence == 0.75
            assert "High context switching" in insight.description
            assert "Distraction spiral detected" in insight.recommendation

    @pytest.mark.asyncio
    async def test_correlate_break_productivity(self, correlator):
        """Test break optimization correlation."""
        mock_timing = {'optimal_minutes': 50, 'confidence': 0.9}
        
        with patch.object(correlator, '_fetch_break_history', return_value=[]), \
             patch.object(correlator, '_fetch_productivity_history', return_value=[]), \
             patch.object(correlator, '_identify_optimal_break_timing', return_value=mock_timing):
            
            insight = await correlator.correlate_break_productivity("user1")
            
            assert insight.insight_type == "break_optimization"
            assert insight.confidence == 0.9
            assert "every 50 minutes" in insight.description

    def test_identify_distraction_pattern(self, correlator):
        """Test the logic for identifying distraction patterns."""
        now = datetime.now()
        
        # Scenario: User was scattered 5 mins ago
        attention_data = [
            {'state': 'scattered', 'timestamp': now - timedelta(minutes=5)}
        ]
        
        # Scenario: 6 switches happened around that time
        switch_data = [
            {'timestamp': now - timedelta(minutes=5, seconds=i*10)} 
            for i in range(6)
        ]
        
        result = correlator._identify_distraction_pattern(attention_data, switch_data)
        
        assert result['pattern'] == 'high_switch_scatter'
        assert result['switch_count'] == 6
        assert result['confidence'] == 0.7

    def test_identify_optimal_break_timing(self, correlator):
        """Test logic for calculating optimal break time."""
        # Scenario: User accepts breaks after working 55, 60, and 50 minutes
        break_data = [
            {'accepted': True, 'minutes_since_last_break': 55},
            {'accepted': True, 'minutes_since_last_break': 60},
            {'accepted': True, 'minutes_since_last_break': 50},
            {'accepted': False, 'minutes_since_last_break': 25} # Ignored
        ]
        
        result = correlator._identify_optimal_break_timing(break_data, [])
        
        # Avgerage of 55, 60, 50 is 55
        assert result['optimal_minutes'] == 55
        assert result['confidence'] == 0.8
