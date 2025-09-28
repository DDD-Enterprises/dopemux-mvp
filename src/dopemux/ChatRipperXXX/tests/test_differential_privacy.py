"""Tests for differential privacy mechanisms."""

import pytest
from src.chatx.privacy.differential_privacy import (
    DifferentialPrivacyEngine, 
    PrivacyBudget, 
    StatisticalQuery
)
from src.chatx.redaction.policy_shield import PolicyShield, PrivacyPolicy


class TestDifferentialPrivacy:
    """Test differential privacy functionality."""
    
    def test_privacy_budget_validation(self):
        """Test privacy budget parameter validation."""
        # Valid budget
        budget = PrivacyBudget(epsilon=1.0, delta=1e-6, sensitivity=1.0)
        assert budget.epsilon == 1.0
        
        # Invalid epsilon
        with pytest.raises(ValueError, match="Epsilon must be positive"):
            PrivacyBudget(epsilon=-1.0)
        
        # Invalid delta
        with pytest.raises(ValueError, match="Delta must be in"):
            PrivacyBudget(delta=2.0)
    
    def test_dp_engine_initialization(self):
        """Test differential privacy engine initialization."""
        engine = DifferentialPrivacyEngine(random_seed=42)
        assert engine.rng is not None
        assert len(engine._budget_tracker) == 0
    
    def test_count_query_basic(self):
        """Test basic count query functionality."""
        engine = DifferentialPrivacyEngine(random_seed=42)
        budget = PrivacyBudget(epsilon=1.0)
        
        test_data = [
            {'id': 1, 'category': 'A'},
            {'id': 2, 'category': 'B'},
            {'id': 3, 'category': 'A'}
        ]
        
        query = StatisticalQuery('count', 'id')
        result = engine.count_query(test_data, query, budget)
        
        # Should be close to true count (3) but with noise
        assert isinstance(result.value, float)
        assert result.value >= 0  # Non-negative constraint
        assert result.privacy_cost.epsilon == 1.0
        assert 'count' in result.metadata['query_type']
    
    def test_sum_query_basic(self):
        """Test basic sum query functionality."""
        engine = DifferentialPrivacyEngine(random_seed=42)
        budget = PrivacyBudget(epsilon=1.0)
        
        test_data = [
            {'value': 10},
            {'value': 20},
            {'value': 30}
        ]
        
        query = StatisticalQuery('sum', 'value')
        result = engine.sum_query(test_data, query, budget)
        
        # Should be close to true sum (60) but with noise
        assert isinstance(result.value, float)
        assert result.privacy_cost.epsilon == 1.0
        assert result.metadata['true_sum'] == 60
    
    def test_histogram_query_basic(self):
        """Test basic histogram query functionality."""
        engine = DifferentialPrivacyEngine(random_seed=42)
        budget = PrivacyBudget(epsilon=1.0)
        
        test_data = [
            {'score': 85},
            {'score': 90},
            {'score': 75},
            {'score': 95}
        ]
        
        query = StatisticalQuery(
            'histogram', 
            'score',
            bin_config={'num_bins': 3}
        )
        result = engine.histogram_query(test_data, query, budget)
        
        # Should return list of noisy bin counts
        assert isinstance(result.value, list)
        assert len(result.value) == 3
        assert all(count >= 0 for count in result.value)  # Non-negative
    
    def test_generate_privacy_safe_summary_basic(self):
        """Test basic privacy-safe summary generation with differential privacy."""
        policy = PrivacyPolicy(enable_differential_privacy=True, dp_epsilon=1.0)
        shield = PolicyShield(policy=policy)
        
        test_chunks = [
            {'chunk_id': '1', 'text': 'Hello world', 'meta': {'labels_coarse': ['friendly', 'positive']}},
            {'chunk_id': '2', 'text': 'Test message', 'meta': {'labels_coarse': ['neutral']}},
            {'chunk_id': '3', 'text': 'Another test', 'meta': {'labels_coarse': ['friendly', 'informative']}},
        ]
        
        # Test privacy-safe summary generation
        summary = shield.generate_privacy_safe_summary(test_chunks, include_label_distribution=True)
        
        # Verify basic structure
        assert summary['privacy_method'] == 'differential_privacy'
        assert summary['privacy_parameters']['epsilon'] == 1.0
        assert summary['privacy_parameters']['delta'] == 1e-6
        assert summary['privacy_parameters']['noise_calibrated'] == True
        
        # Verify statistical fields
        assert 'total_chunks' in summary
        assert 'avg_chunk_length' in summary
        assert 'timestamp' in summary
        assert isinstance(summary['total_chunks'], float)
        assert isinstance(summary['avg_chunk_length'], float)
        
        # Verify label distribution is included
        assert 'label_distribution' in summary
        assert isinstance(summary['label_distribution'], dict)
        
        # Verify privacy guarantees - values should be noisy but reasonable
        assert 2.0 <= summary['total_chunks'] <= 4.0  # Should be close to 3 with noise
        assert summary['avg_chunk_length'] > 0
    
    def test_generate_privacy_safe_summary_no_labels(self):
        """Test privacy-safe summary generation without label distribution."""
        policy = PrivacyPolicy(enable_differential_privacy=True, dp_epsilon=0.5)
        shield = PolicyShield(policy=policy)
        
        test_chunks = [
            {'chunk_id': '1', 'text': 'Short text'},
            {'chunk_id': '2', 'text': 'Another message'},
        ]
        
        # Test without label distribution
        summary = shield.generate_privacy_safe_summary(test_chunks, include_label_distribution=False)
        
        # Verify basic structure
        assert summary['privacy_method'] == 'differential_privacy'
        assert summary['privacy_parameters']['epsilon'] == 0.5
        
        # Should not include label distribution
        assert 'label_distribution' not in summary
        assert 'total_chunks' in summary
        assert isinstance(summary['total_chunks'], float)
        
        # Verify privacy parameters
        assert summary['privacy_parameters']['epsilon'] == 0.5
        assert summary['privacy_parameters']['delta'] == 1e-6
    
    def test_generate_privacy_safe_summary_empty_data(self):
        """Test privacy-safe summary generation with empty data."""
        policy = PrivacyPolicy(enable_differential_privacy=True, dp_epsilon=1.0)
        shield = PolicyShield(policy=policy)
        
        # Test with empty chunks
        summary = shield.generate_privacy_safe_summary([])
        
        # Should return empty but valid structure
        assert summary['privacy_method'] == 'differential_privacy'
        assert summary['total_chunks'] == 0.0
        assert summary['avg_chunk_length'] == 0.0
        assert 'label_distribution' not in summary
    
    def test_generate_privacy_safe_summary_dp_disabled(self):
        """Test privacy-safe summary generation when differential privacy is disabled."""
        policy = PrivacyPolicy(enable_differential_privacy=False)
        shield = PolicyShield(policy=policy)
        
        test_chunks = [
            {'chunk_id': '1', 'text': 'Test message', 'meta': {'labels_coarse': ['test']}},
        ]
        
        # Test with DP disabled
        summary = shield.generate_privacy_safe_summary(test_chunks)
        
        # Should use fallback method
        assert summary['privacy_method'] == 'none'
        assert summary['total_chunks'] == 1  # Exact count when DP disabled
        assert 'warning' in summary
        assert summary['warning'] == 'Differential privacy not enabled'
        
        # Should not include privacy parameters
        assert 'privacy_parameters' not in summary
    
    def test_generate_privacy_safe_summary_deterministic(self):
        """Test that privacy-safe summary generation is deterministic with fixed seed."""
        # Create two shields with same salt for deterministic behavior
        policy = PrivacyPolicy(enable_differential_privacy=True, dp_epsilon=1.0)
        
        test_chunks = [
            {'chunk_id': '1', 'text': 'Deterministic test', 'meta': {'labels_coarse': ['test']}},
            {'chunk_id': '2', 'text': 'Another test', 'meta': {'labels_coarse': ['test', 'demo']}},
        ]
        
        # Test with same salt for deterministic results
        shield1 = PolicyShield(policy=policy)
        shield2 = PolicyShield(policy=policy)
        
        summary1 = shield1.generate_privacy_safe_summary(test_chunks)
        summary2 = shield2.generate_privacy_safe_summary(test_chunks)
        
        # Results should be very similar (allowing for minor floating point differences)
        assert abs(summary1['total_chunks'] - summary2['total_chunks']) < 0.1
        assert summary1['privacy_method'] == summary2['privacy_method']
        assert summary1['privacy_parameters']['epsilon'] == summary2['privacy_parameters']['epsilon']
    
    def test_privacy_budget_tracking(self):
        """Test privacy budget tracking functionality."""
        engine = DifferentialPrivacyEngine(random_seed=42)
        budget = PrivacyBudget(epsilon=0.5)
        
        test_data = [{'id': 1}, {'id': 2}]
        query = StatisticalQuery('count', 'id')
        
        # Execute query
        engine.count_query(test_data, query, budget)
        
        # Check budget tracking
        budget_summary = engine.get_privacy_budget_summary()
        assert len(budget_summary) > 0
        
        # Budget usage should be recorded
        total_epsilon = sum(budget_summary.values())
        assert total_epsilon == 0.5
    
    def test_deterministic_noise_with_seed(self):
        """Test that noise generation is deterministic with fixed seed."""
        engine1 = DifferentialPrivacyEngine(random_seed=42)
        engine2 = DifferentialPrivacyEngine(random_seed=42)
        
        budget = PrivacyBudget(epsilon=1.0)
        test_data = [{'id': 1}, {'id': 2}, {'id': 3}]
        query = StatisticalQuery('count', 'id')
        
        result1 = engine1.count_query(test_data, query, budget)
        result2 = engine2.count_query(test_data, query, budget)
        
        # Results should be identical with same seed
        assert abs(result1.value - result2.value) < 1e-10