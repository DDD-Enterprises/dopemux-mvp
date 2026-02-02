"""
Tests for Energy Visualizer
"""
import pytest
from visualizer import EnergyTrendVisualizer


class TestEnergyVisualizer:
    """Test suite for EnergyTrendVisualizer"""
    
    def test_initialization(self):
        """Test visualizer can be initialized"""
        viz = EnergyTrendVisualizer()
        assert viz is not None
        assert viz.adhd_engine_url == "http://localhost:8095"
    
    def test_initialization_with_params(self):
        """Test visualizer with custom parameters"""
        viz = EnergyTrendVisualizer(
            adhd_engine_url="http://custom:8080",
            user_id="test_user"
        )
        assert viz.adhd_engine_url == "http://custom:8080"
        assert viz.user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_get_current_energy_failure_handling(self):
        """Test energy level fetch handles failures"""
        viz = EnergyTrendVisualizer(adhd_engine_url="http://invalid:9999")
        result = await viz.get_current_energy()
        # Should return "unknown" on connection failure
        assert result == "unknown"
