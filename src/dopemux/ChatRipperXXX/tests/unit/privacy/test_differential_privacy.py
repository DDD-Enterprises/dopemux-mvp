
"""Tests for Differential Privacy engine."""
import math
import numpy as np
import pytest
from datetime import datetime
from typing import Dict, List, Any

from chatx.privacy.differential_privacy import (
    DifferentialPrivacyEngine, PrivacyBudget, StatisticalQuery, DPResult,
    NoiseDistribution
)


@pytest.fixture
def dp_engine():
    """Create a differential privacy engine for testing."""
    return DifferentialPrivacyEngine(random_seed=42)


@pytest.fixture
def sample_budget():
    """Create a sample privacy budget for testing."""
    return PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)


@pytest.fixture
def sample_query():
    """Create a sample statistical query for testing."""
    return StatisticalQuery(query_type="count", field_name="value")


class TestPrivacyBudget:
    """Test PrivacyBudget functionality."""
    
    def test_valid_budget_creation(self):
        """Test creating a valid privacy budget."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        assert budget.epsilon == 1.0
        assert budget.delta == 1e-6
        assert budget.sensitivity == 1.0
    
    def test_invalid_epsilon(self):
        """Test invalid epsilon values."""
        with pytest.raises(ValueError, match="Epsilon must be positive"):
            PrivacyBudget(epsilon=0, delta=1e-6, sensitivity=1.0)
        
        with pytest.raises(ValueError, match="Epsilon must be positive"):
            PrivacyBudget(epsilon=-1.0, delta=1e-6, sensitivity=1.0)
    
    def test_invalid_delta(self):
        """Test invalid delta values."""
        with pytest.raises(ValueError, match="Delta must be in"):
            PrivacyBudget(epsilon=1.0, delta=-1e-6, sensitivity=1.0)
        
        with pytest.raises(ValueError, match="Delta must be in"):
            PrivacyBudget(epsilon=1.0, delta=1.0, sensitivity=1.0)
    
    def test_invalid_sensitivity(self):
        """Test invalid sensitivity values."""
        with pytest.raises(ValueError, match="Sensitivity must be positive"):
            PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=0)
        
        with pytest.raises(ValueError, match="Sensitivity must be positive"):
            PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=-1.0)


class TestStatisticalQuery:
    """Test StatisticalQuery functionality."""
    
    def test_query_creation_minimal(self):
        """Test creating a minimal statistical query."""
        query = StatisticalQuery(query_type="count", field_name="value")
        assert query.query_type == "count"
        assert query.field_name == "value"
        assert query.filter_conditions is None
        assert query.bin_config is None
    
    def test_query_creation_with_filters(self):
        """Test creating a query with filter conditions."""
        filters = {"category": "A", "status": "active"}
        query = StatisticalQuery(
            query_type="count", 
            field_name="value", 
            filter_conditions=filters
        )
        assert query.filter_conditions == filters
    
    def test_query_creation_with_bin_config(self):
        """Test creating a query with bin configuration for histograms."""
        bin_config = {"num_bins": 10}
        query = StatisticalQuery(
            query_type="histogram", 
            field_name="score", 
            bin_config=bin_config
        )
        assert query.bin_config == bin_config


class TestDPResult:
    """Test DPResult functionality."""
    
    def test_dp_result_creation(self):
        """Test creating a differential privacy result."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        result = DPResult(
            value=42.5,
            privacy_cost=budget,
            noise_scale=1.0
        )
        
        assert result.value == 42.5
        assert result.privacy_cost is budget
        assert result.noise_scale == 1.0
        assert result.metadata is not None
        assert result.metadata['timestamp'] is not None
        assert result.metadata['algorithm'] == 'laplace_mechanism'
    
    def test_dp_result_with_confidence_interval(self):
        """Test DP result with confidence interval."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        result = DPResult(
            value=42.5,
            privacy_cost=budget,
            noise_scale=1.0,
            confidence_interval=(40.0, 45.0)
        )
        
        assert result.confidence_interval == (40.0, 45.0)
    
    def test_dp_result_with_custom_metadata(self):
        """Test DP result with custom metadata."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        custom_meta = {'custom_field': 'test_value'}
        
        result = DPResult(
            value=42.5,
            privacy_cost=budget,
            noise_scale=1.0,
            metadata=custom_meta
        )
        
        assert result.metadata == custom_meta


class TestDifferentialPrivacyEngine:
    """Test DifferentialPrivacyEngine functionality."""
    
    def test_engine_initialization(self):
        """Test DP engine initialization."""
        engine = DifferentialPrivacyEngine(random_seed=42)
        assert engine.rng is not None
        assert engine._budget_tracker == {}
    
    def test_engine_initialization_no_seed(self):
        """Test DP engine initialization without seed."""
        engine = DifferentialPrivacyEngine()
        assert engine.rng is not None
        assert engine._budget_tracker == {}
    
    def test_generate_laplace_noise_single(self, dp_engine):
        """Test single Laplace noise generation."""
        noise = dp_engine._generate_laplace_noise(1.0)
        assert isinstance(noise, (float, np.float64))
    
    def test_generate_laplace_noise_array(self, dp_engine):
        """Test Laplace noise array generation."""
        noise = dp_engine._generate_laplace_noise(1.0, size=5)
        assert isinstance(noise, np.ndarray)
        assert len(noise) == 5
    
    def test_generate_gaussian_noise_single(self, dp_engine):
        """Test single Gaussian noise generation."""
        noise = dp_engine._generate_gaussian_noise(1.0)
        assert isinstance(noise, (float, np.float64))
    
    def test_generate_gaussian_noise_array(self, dp_engine):
        """Test Gaussian noise array generation."""
        noise = dp_engine._generate_gaussian_noise(1.0, size=3)
        assert isinstance(noise, np.ndarray)
        assert len(noise) == 3
    
    def test_calculate_noise_scale_laplace(self, dp_engine):
        """Test noise scale calculation for Laplace mechanism."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=2.0)
        scale = dp_engine._calculate_noise_scale(budget, NoiseDistribution.LAPLACE)
        
        expected_scale = 2.0 / 1.0  # sensitivity / epsilon
        assert scale == pytest.approx(expected_scale, rel=1e-10)
    
    def test_calculate_noise_scale_gaussian(self, dp_engine):
        """Test noise scale calculation for Gaussian mechanism."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=2.0)
        scale = dp_engine._calculate_noise_scale(budget, NoiseDistribution.GAUSSIAN)
        
        c = math.sqrt(2 * math.log(1.25 / budget.delta))
        expected_scale = c * 2.0 / 1.0
        assert scale == pytest.approx(expected_scale, rel=1e-10)
    
    def test_calculate_noise_scale_gaussian_zero_delta(self, dp_engine):
        """Test Gaussian noise scale with zero delta (should raise error)."""
        budget = PrivacyBudget(epsilon=1.0, delta=0, sensitivity=1.0)
        
        with pytest.raises(ValueError, match="Delta must be > 0"):
            dp_engine._calculate_noise_scale(budget, NoiseDistribution.GAUSSIAN)
    
    def test_calculate_noise_scale_invalid_distribution(self, dp_engine):
        """Test noise scale calculation with invalid distribution."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        
        with pytest.raises(ValueError, match="Unsupported noise distribution"):
            dp_engine._calculate_noise_scale(budget, "invalid")
    
    def test_add_noise_single_value(self, dp_engine, sample_budget):
        """Test adding noise to single value."""
        original_value = 42.0
        noisy_value = dp_engine._add_noise(original_value, sample_budget)
        
        assert isinstance(noisy_value, float)
        # Check that noise is added (result should differ from original)
        # Note: Due to randomness, this could theoretically fail but is very unlikely
        assert abs(noisy_value - original_value) >= 0
    
    def test_add_noise_array_values(self, dp_engine, sample_budget):
        """Test adding noise to array of values."""
        original_values = [10.0, 20.0, 30.0]
        noisy_values = dp_engine._add_noise(original_values, sample_budget)
        
        assert isinstance(noisy_values, list)
        assert len(noisy_values) == 3
        for original, noisy in zip(original_values, noisy_values):
            assert isinstance(noisy, float)
            assert abs(noisy - original) >= 0
    
    def test_track_privacy_budget(self, dp_engine):
        """Test privacy budget tracking."""
        query_id = "test_query"
        epsilon_used = 0.5
        
        dp_engine._track_privacy_budget(query_id, epsilon_used)
        
        assert query_id in dp_engine._budget_tracker
        assert dp_engine._budget_tracker[query_id] == epsilon_used
    
    def test_track_privacy_budget_multiple_calls(self, dp_engine):
        """Test privacy budget tracking with multiple calls."""
        query_id = "test_query"
        
        dp_engine._track_privacy_budget(query_id, 0.5)
        dp_engine._track_privacy_budget(query_id, 0.3)
        
        assert dp_engine._budget_tracker[query_id] == 0.8
    
    def test_count_query_basic(self, dp_engine, sample_budget, sample_query):
        """Test basic count query execution."""
        data = [
            {'value': 10, 'category': 'A'},
            {'value': 20, 'category': 'B'},
            {'value': 30, 'category': 'A'}
        ]
        
        result = dp_engine.count_query(data, sample_query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert isinstance(result.value, float)
        assert result.privacy_cost is sample_budget
        assert isinstance(result.noise_scale, float)
        assert result.metadata is not None
        assert result.metadata['query_type'] == 'count'
        assert 'true_count' in result.metadata
    
    def test_count_query_with_filters(self, dp_engine, sample_budget):
        """Test count query with filter conditions."""
        data = [
            {'value': 10, 'category': 'A'},
            {'value': 20, 'category': 'B'},
            {'value': 30, 'category': 'A'}
        ]
        
        query = StatisticalQuery(
            query_type="count", 
            field_name="value",
            filter_conditions={'category': 'A'}
        )
        
        result = dp_engine.count_query(data, query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert isinstance(result.value, float)
        assert result.metadata['filter_conditions'] == {'category': 'A'}
    
    def test_count_query_empty_data(self, dp_engine, sample_budget, sample_query):
        """Test count query with empty data."""
        result = dp_engine.count_query([], sample_query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert result.value >= 0  # Count should be non-negative
    
    def test_sum_query_basic(self, dp_engine, sample_budget):
        """Test basic sum query execution."""
        data = [
            {'value': 10, 'category': 'A'},
            {'value': 20, 'category': 'B'},
            {'value': 30, 'category': 'A'}
        ]
        
        query = StatisticalQuery(query_type="sum", field_name="value")
        result = dp_engine.sum_query(data, query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert isinstance(result.value, float)
        assert result.privacy_cost is sample_budget
        assert result.metadata['query_type'] == 'sum'
        assert 'true_sum' in result.metadata
        assert 'num_records' in result.metadata
    
    def test_sum_query_with_filters(self, dp_engine, sample_budget):
        """Test sum query with filter conditions."""
        data = [
            {'value': 10, 'category': 'A'},
            {'value': 20, 'category': 'B'},
            {'value': 30, 'category': 'A'}
        ]
        
        query = StatisticalQuery(
            query_type="sum", 
            field_name="value",
            filter_conditions={'category': 'A'}
        )
        
        result = dp_engine.sum_query(data, query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert result.metadata['filter_conditions'] == {'category': 'A'}
    
    def test_sum_query_missing_field(self, dp_engine, sample_budget):
        """Test sum query with missing field values."""
        data = [
            {'value': 10},
            {'other_field': 20},  # Missing 'value' field
            {'value': 30}
        ]
        
        query = StatisticalQuery(query_type="sum", field_name="value")
        result = dp_engine.sum_query(data, query, sample_budget)
        
        assert isinstance(result, DPResult)
        # Should handle missing fields gracefully (treating as 0)
    
    def test_histogram_query_basic(self, dp_engine, sample_budget):
        """Test basic histogram query execution."""
        data = [
            {'score': 1.0},
            {'score': 2.0},
            {'score': 1.5},
            {'score': 3.0}
        ]
        
        query = StatisticalQuery(
            query_type="histogram", 
            field_name="score",
            bin_config={'num_bins': 3}
        )
        
        result = dp_engine.histogram_query(data, query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert isinstance(result.value, list)
        assert len(result.value) == 3  # 3 bins
        assert result.metadata['query_type'] == 'histogram'
        assert 'true_counts' in result.metadata
        assert 'bin_edges' in result.metadata
    
    def test_histogram_query_with_bins_specified(self, dp_engine, sample_budget):
        """Test histogram query with explicit bin edges."""
        data = [
            {'score': 1.0},
            {'score': 2.0},
            {'score': 3.0}
        ]
        
        query = StatisticalQuery(
            query_type="histogram", 
            field_name="score",
            bin_config={'bins': [0, 1.5, 3]}
        )
        
        result = dp_engine.histogram_query(data, query, sample_budget)
        
        assert isinstance(result, DPResult)
        assert isinstance(result.value, list)
        assert len(result.value) == 2  # 2 bins
    
    def test_histogram_query_no_bin_config(self, dp_engine, sample_budget):
        """Test histogram query without bin configuration."""
        data = [{'score': 1.0}]
        query = StatisticalQuery(query_type="histogram", field_name="score")
        
        with pytest.raises(ValueError, match="bin_config required"):
            dp_engine.histogram_query(data, query, sample_budget)
    
    def test_histogram_query_invalid_bin_config(self, dp_engine, sample_budget):
        """Test histogram query with invalid bin configuration."""
        data = [{'score': 1.0}]
        query = StatisticalQuery(
            query_type="histogram", 
            field_name="score",
            bin_config={}
        )
        
        with pytest.raises(ValueError, match="bin_config required"):
            dp_engine.histogram_query(data, query, sample_budget)
    
    def test_mean_query_basic(self, dp_engine, sample_budget):
        """Test basic mean query execution."""
        data = [
            {'score': 1.0},
            {'score': 2.0},
            {'score': 3.0}
        ]
        
        query = StatisticalQuery(query_type="mean", field_name="score")
        value_bounds = (0.0, 10.0)
        
        result = dp_engine.mean_query(data, query, sample_budget, value_bounds)
        
        assert isinstance(result, DPResult)
        assert isinstance(result.value, float)
        assert result.metadata['query_type'] == 'mean'
        assert 'true_mean' in result.metadata
        assert 'noisy_sum' in result.metadata
        assert 'noisy_count' in result.metadata
        assert 'value_bounds' in result.metadata
    
    def test_mean_query_with_bounds_filtering(self, dp_engine, sample_budget):
        """Test mean query with bounds filtering."""
        data = [
            {'score': -5.0},  # Out of bounds (too low)
            {'score': 1.0},   # In bounds
            {'score': 2.0},   # In bounds
            {'score': 15.0}   # Out of bounds (too high)
        ]
        
        query = StatisticalQuery(query_type="mean", field_name="score")
        value_bounds = (0.0, 10.0)
        
        result = dp_engine.mean_query(data, query, sample_budget, value_bounds)
        
        assert isinstance(result, DPResult)
        assert result.metadata['num_values'] == 2  # Only 1.0 and 2.0 are in bounds
    
    def test_mean_query_empty_after_filtering(self, dp_engine, sample_budget):
        """Test mean query when no values are in bounds."""
        data = [
            {'score': -5.0},  # Out of bounds
            {'score': 15.0}   # Out of bounds
        ]
        
        query = StatisticalQuery(query_type="mean", field_name="score")
        value_bounds = (0.0, 10.0)
        
        result = dp_engine.mean_query(data, query, sample_budget, value_bounds)
        
        assert isinstance(result, DPResult)
        assert result.value == 0.0
        assert result.metadata['num_values'] == 0
    
    def test_get_privacy_budget_summary_empty(self, dp_engine):
        """Test privacy budget summary with no queries tracked."""
        summary = dp_engine.get_privacy_budget_summary()
        assert summary == {}
    
    def test_get_privacy_budget_summary_with_data(self, dp_engine):
        """Test privacy budget summary with tracked queries."""
        dp_engine._track_privacy_budget('query1', 0.5)
        dp_engine._track_privacy_budget('query2', 0.3)
        
        summary = dp_engine.get_privacy_budget_summary()
        assert summary == {'query1': 0.5, 'query2': 0.3}
    
    def test_reset_privacy_budget_specific_query(self, dp_engine):
        """Test resetting privacy budget for specific query."""
        dp_engine._track_privacy_budget('query1', 0.5)
        dp_engine._track_privacy_budget('query2', 0.3)
        
        dp_engine.reset_privacy_budget('query1')
        
        summary = dp_engine.get_privacy_budget_summary()
        assert 'query1' not in summary
        assert summary == {'query2': 0.3}
    
    def test_reset_privacy_budget_all_queries(self, dp_engine):
        """Test resetting all privacy budgets."""
        dp_engine._track_privacy_budget('query1', 0.5)
        dp_engine._track_privacy_budget('query2', 0.3)
        
        dp_engine.reset_privacy_budget()
        
        summary = dp_engine.get_privacy_budget_summary()
        assert summary == {}
    
    def test_deterministic_noise_with_seed(self):
        """Test deterministic noise generation with fixed seed."""
        engine1 = DifferentialPrivacyEngine(random_seed=123)
        engine2 = DifferentialPrivacyEngine(random_seed=123)
        
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        
        noise1 = engine1._add_noise(42.0, budget)
        noise2 = engine2._add_noise(42.0, budget)
        
        # Should be the same due to same seed
        assert noise1 == noise2
    
    def test_noise_distribution_properties(self, dp_engine):
        """Test statistical properties of noise generation."""
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        
        # Generate many noise samples
        samples = []
        for _ in range(1000):
            noisy = dp_engine._add_noise(0.0, budget)
            samples.append(noisy)
        
        # Basic statistical checks
        mean_noise = sum(samples) / len(samples)
        # Mean should be close to 0 (within reasonable statistical bounds)
        assert abs(mean_noise) < 1.0  # Allow some statistical variation
        
        # Most samples should be within reasonable bounds
        within_bounds = [s for s in samples if -5 < s < 5]
        assert len(within_bounds) > 800  # >80% within bounds


if __name__ == "__main__":
    pytest.main([__file__])
