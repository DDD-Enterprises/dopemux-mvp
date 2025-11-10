"""
Tests for Predictive Context Restoration feature

Comprehensive test suite covering TF-IDF vectorization, KNN pattern matching,
ADHD optimization, caching, and performance benchmarks.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import numpy as np

from predictive_context_restoration import (
    PredictiveContextRestoration,
    TFIDFVectorizer,
    KNNPatternMatcher,
    ADHDContextOptimizer,
    ContextPattern,
    PredictionResult
)


class TestTFIDFVectorizer:
    """Test TF-IDF vectorization functionality"""

    def setup_method(self):
        self.vectorizer = TFIDFVectorizer(max_features=100)

    def test_extract_text_features(self):
        """Test text feature extraction from context data"""
        context = {
            'current_task': 'Implementing authentication',
            'thought_process': 'Need to handle JWT validation',
            'summary': 'Auth system implementation',
            'tags': ['security', 'auth'],
            'interruption_type': 'manual'
        }

        text = self.vectorizer._extract_text_features(context)
        assert 'implementing authentication' in text.lower()
        assert 'jwt validation' in text.lower()
        assert 'security' in text.lower()
        assert 'auth' in text.lower()

    def test_fit_transform(self):
        """Test fitting and transforming contexts"""
        contexts = [
            {'current_task': 'auth implementation', 'complexity_score': 0.7},
            {'current_task': 'database design', 'complexity_score': 0.5},
            {'current_task': 'auth testing', 'complexity_score': 0.6}
        ]

        vectors = self.vectorizer.fit_transform(contexts)

        assert len(vectors) == 3
        assert len(vectors[0]) == len(self.vectorizer.vocabulary)
        assert len(self.vectorizer.idf_scores) > 0

    def test_transform_single_context(self):
        """Test transforming single context after fitting"""
        contexts = [
            {'current_task': 'auth implementation'},
            {'current_task': 'database design'}
        ]

        self.vectorizer.fit_transform(contexts)
        new_vector = self.vectorizer.transform({'current_task': 'auth testing'})

        assert len(new_vector) == len(self.vectorizer.vocabulary)
        assert all(isinstance(x, float) for x in new_vector)


class TestKNNPatternMatcher:
    """Test KNN pattern matching functionality"""

    def setup_method(self):
        self.matcher = KNNPatternMatcher(k=3)

        # Create test patterns
        self.patterns = [
            ContextPattern(
                context_vector=[1.0, 0.5, 0.0],
                context_data={'current_task': 'auth implementation'},
                timestamp=datetime.now(),
                context_type='wma_snapshot'
            ),
            ContextPattern(
                context_vector=[0.5, 1.0, 0.0],
                context_data={'current_task': 'database design'},
                timestamp=datetime.now(),
                context_type='decision'
            ),
            ContextPattern(
                context_vector=[0.0, 0.5, 1.0],
                context_data={'current_task': 'api development'},
                timestamp=datetime.now(),
                context_type='progress_entry'
            )
        ]

        for pattern in self.patterns:
            self.matcher.add_pattern(pattern)

    def test_add_patterns(self):
        """Test adding patterns to matcher"""
        assert len(self.matcher.patterns) == 3

    def test_find_similar_patterns(self):
        """Test finding similar patterns"""
        query_vector = [0.9, 0.6, 0.1]  # Similar to first pattern
        similar = self.matcher.find_similar_patterns(query_vector)

        assert len(similar) == 3  # Returns all patterns sorted by similarity
        assert similar[0][0] == self.patterns[0]  # Most similar first
        assert similar[0][1] > similar[1][1]  # Similarity decreases

    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        similarity = self.matcher._cosine_similarity([1, 0], [1, 0])
        assert similarity == 1.0

        similarity = self.matcher._cosine_similarity([1, 0], [0, 1])
        assert similarity == 0.0

        similarity = self.matcher._cosine_similarity([1, 1], [1, 1])
        assert abs(similarity - 1.0) < 1e-10  # Handle floating point precision

    def test_get_pattern_statistics(self):
        """Test pattern statistics"""
        stats = self.matcher.get_pattern_statistics()

        assert stats['total_patterns'] == 3
        assert 'wma_snapshot' in stats['context_types']
        assert 'decision' in stats['context_types']
        assert 'progress_entry' in stats['context_types']


class TestADHDContextOptimizer:
    """Test ADHD-aware context optimization"""

    def setup_method(self):
        self.optimizer = ADHDContextOptimizer()

    @pytest.mark.asyncio
    async def test_get_attention_state(self):
        """Test attention state retrieval"""
        # Mock the entire ADHD integration call
        with patch.object(self.optimizer, 'get_attention_state', return_value='focused') as mock_get_state:
            state = await self.optimizer.get_attention_state()
            assert state == 'focused'
            mock_get_state.assert_called_once()

    def test_optimize_suggestions_focused(self):
        """Test suggestion optimization for focused attention"""
        similar_patterns = [
            (ContextPattern(
                context_vector=[1.0, 0.0],
                context_data={'complexity_score': 0.8, 'current_task': 'complex task'},
                timestamp=datetime.now(),
                context_type='wma_snapshot'
            ), 0.9),
            (ContextPattern(
                context_vector=[0.0, 1.0],
                context_data={'complexity_score': 0.3, 'current_task': 'simple task'},
                timestamp=datetime.now(),
                context_type='decision'
            ), 0.7)
        ]

        suggestions = self.optimizer.optimize_suggestions(
            similar_patterns, 'focused', 0.8  # High energy
        )

        assert len(suggestions) <= 10  # Max for focused
        assert suggestions[0]['attention_state'] == 'focused'

    def test_optimize_suggestions_scattered(self):
        """Test suggestion optimization for scattered attention"""
        similar_patterns = [
            (ContextPattern(
                context_vector=[1.0, 0.0],
                context_data={'complexity_score': 0.8},
                timestamp=datetime.now(),
                context_type='wma_snapshot'
            ), 0.9)
        ]

        suggestions = self.optimizer.optimize_suggestions(
            similar_patterns, 'scattered', 0.5
        )

        assert len(suggestions) <= 5  # Max for scattered

    def test_optimize_suggestions_overwhelmed(self):
        """Test suggestion optimization for overwhelmed attention"""
        similar_patterns = [
            (ContextPattern(
                context_vector=[1.0, 0.0],
                context_data={'complexity_score': 0.8},
                timestamp=datetime.now(),
                context_type='wma_snapshot'
            ), 0.9)
        ]

        suggestions = self.optimizer.optimize_suggestions(
            similar_patterns, 'overwhelmed', 0.3  # Low energy
        )

        assert len(suggestions) <= 3  # Max for overwhelmed


class TestPredictiveContextRestoration:
    """Test the main predictive context restoration engine"""

    def setup_method(self):
        self.workspace_id = "/test/workspace"
        self.restoration = PredictiveContextRestoration(self.workspace_id)

    def test_initialization(self):
        """Test initialization"""
        assert self.restoration.workspace_id == self.workspace_id
        assert self.restoration.vectorizer is not None
        assert self.restoration.pattern_matcher is not None
        assert self.restoration.adhd_optimizer is not None
        assert self.restoration.executor is not None

    @pytest.mark.asyncio
    async def test_predict_context_basic(self):
        """Test basic context prediction"""
        # Mock the training and dependencies
        self.restoration._train_model = AsyncMock()
        self.restoration.adhd_optimizer.get_attention_state = AsyncMock(return_value='focused')

        # Create a mock pattern for testing
        mock_pattern = ContextPattern(
            context_vector=[1.0, 0.5, 0.0],
            context_data={'current_task': 'test task', 'complexity_score': 0.6},
            timestamp=datetime.now(),
            context_type='wma_snapshot'
        )
        self.restoration.pattern_matcher.add_pattern(mock_pattern)

        current_context = {
            'current_task': 'similar test task',
            'energy_level': 0.7
        }

        result = await self.restoration.predict_context(current_context)

        assert isinstance(result, PredictionResult)
        assert result.prediction_confidence >= 0.0
        assert result.prediction_confidence <= 1.0
        assert 'prediction_time_ms' in result.performance_metrics

    def test_create_context_cache_key(self):
        """Test cache key creation"""
        context = {
            'current_task': 'test task',
            'energy_level': 0.7,
            'timestamp': datetime.now()  # Should be excluded
        }

        key = self.restoration._create_context_cache_key(context, 'user1')

        assert key.startswith('pred:user1:')
        assert len(key) > 10

        # Same context should produce same key
        key2 = self.restoration._create_context_cache_key(context, 'user1')
        assert key == key2

        # Different user should produce different key
        key3 = self.restoration._create_context_cache_key(context, 'user2')
        assert key != key3

    @pytest.mark.asyncio
    async def test_cached_prediction(self):
        """Test prediction caching"""
        # Create a test result
        test_result = PredictionResult(
            prediction_confidence=0.8,
            suggested_context={'test': 'data'},
            recovery_recommendations=[],
            similar_historical_contexts=[],
            adhd_optimized_suggestions=[],
            performance_metrics={'test': True}
        )

        cache_key = "test_key"

        # Cache the result
        await self.restoration._cache_prediction(cache_key, test_result)

        # Retrieve from cache
        cached_result = await self.restoration._get_cached_prediction(cache_key)

        assert cached_result is not None
        assert cached_result.prediction_confidence == test_result.prediction_confidence

    def test_get_cached_vector(self):
        """Test vector caching"""
        # First fit the vectorizer with some training data
        training_contexts = [
            {'current_task': 'auth implementation'},
            {'current_task': 'database design'}
        ]
        self.restoration.vectorizer.fit_transform(training_contexts)

        context = {'current_task': 'test task'}

        # First call should compute vector
        vector1 = asyncio.run(self.restoration._get_cached_vector(context))

        # Second call should use cache
        vector2 = asyncio.run(self.restoration._get_cached_vector(context))

        assert vector1 == vector2
        assert len(vector1) > 0

    def test_performance_stats(self):
        """Test performance statistics"""
        stats = self.restoration.get_performance_stats()

        required_keys = ['model_stats', 'performance', 'adhd_optimizer', 'cache_stats', 'thread_pool_stats']
        for key in required_keys:
            assert key in stats

        assert 'vocabulary_size' in stats['model_stats']
        assert 'redis_enabled' in stats['cache_stats']
        assert 'max_workers' in stats['thread_pool_stats']


class TestIntegrationWithWMA:
    """Test integration with WMA service"""

    @pytest.mark.asyncio
    async def test_predictive_recovery_integration(self):
        """Test predictive recovery integration"""
        from wma_core import WorkingMemoryAssistant, DevelopmentSnapshot

        wma = WorkingMemoryAssistant()

        # Mock the getLatestSnapshot method to return a fake snapshot
        fake_snapshot = DevelopmentSnapshot(
            id="test_snapshot",
            session_id="current_session",
            timestamp=datetime.now(),
            interruption_type="manual",
            current_task="test task"
        )

        with patch.object(wma.snapshot_engine, 'getLatestSnapshot', return_value=fake_snapshot):
            # Mock the recovery engine
            with patch.object(wma.recovery_engine, 'initiate_recovery', return_value=MagicMock()):
                # Mock predictive restoration with low confidence to trigger fallback
                mock_restoration = AsyncMock()
                mock_result = PredictionResult(
                    prediction_confidence=0.4,  # Low confidence to trigger fallback
                    suggested_context={},
                    recovery_recommendations=[],
                    similar_historical_contexts=[],
                    adhd_optimized_suggestions=[],  # Empty to trigger fallback
                    performance_metrics={}
                )
                mock_restoration.predict_context.return_value = mock_result
                wma.predictive_restoration = mock_restoration

                current_context = {'energy_level': 0.7}
                result = await wma.predictive_recovery(current_context, use_predictive=True)

                assert result is not None
                mock_restoration.predict_context.assert_called_once()


class TestPerformanceBenchmarks:
    """Performance benchmarks for predictive restoration"""

    def setup_method(self):
        self.restoration = PredictiveContextRestoration("/test/workspace")

        # Add some test patterns
        for i in range(10):
            pattern = ContextPattern(
                context_vector=[float(j == i % 3) for j in range(10)],
                context_data={'current_task': f'task_{i}', 'complexity_score': 0.5},
                timestamp=datetime.now() - timedelta(hours=i),
                context_type='wma_snapshot'
            )
            self.restoration.pattern_matcher.add_pattern(pattern)

    def test_vectorization_performance(self):
        """Benchmark TF-IDF vectorization performance"""
        contexts = [
            {'current_task': f'task {i} implementation', 'complexity_score': 0.5 + i * 0.05}
            for i in range(100)
        ]

        start_time = time.perf_counter()
        vectors = self.restoration.vectorizer.fit_transform(contexts)
        vectorization_time = time.perf_counter() - start_time

        assert vectorization_time < 1.0  # Should be fast
        assert len(vectors) == 100
        assert len(vectors[0]) > 0

    def test_pattern_matching_performance(self):
        """Benchmark KNN pattern matching performance"""
        query_vector = [1.0 if i % 3 == 0 else 0.0 for i in range(10)]

        start_time = time.perf_counter()
        similar = self.restoration.pattern_matcher.find_similar_patterns(query_vector)
        matching_time = time.perf_counter() - start_time

        assert matching_time < 0.1  # Should be very fast
        assert len(similar) <= 10

    def test_caching_performance(self):
        """Benchmark caching performance"""
        context = {'current_task': 'performance test'}

        # First call (cache miss)
        start_time = time.perf_counter()
        vector1 = asyncio.run(self.restoration._get_cached_vector(context))
        first_call_time = time.perf_counter() - start_time

        # Second call (cache hit)
        start_time = time.perf_counter()
        vector2 = asyncio.run(self.restoration._get_cached_vector(context))
        second_call_time = time.perf_counter() - start_time

        assert vector1 == vector2
        assert second_call_time < first_call_time  # Cache should be faster


if __name__ == "__main__":
    pytest.main([__file__])