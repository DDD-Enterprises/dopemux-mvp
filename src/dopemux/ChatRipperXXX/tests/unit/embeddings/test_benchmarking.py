"""Tests for embedding performance benchmarking framework."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from typing import List
import time

from chatx.embeddings.benchmarking import (
    BenchmarkRunner,
    BenchmarkConfig,
    BenchmarkResult,
    ModelComparison,
    create_test_corpus
)
from chatx.embeddings.base import BaseEmbeddingProvider, EmbeddingMetrics


class TestBenchmarkConfig:
    """Test BenchmarkConfig data class."""
    
    def test_default_config(self):
        """Test default benchmark configuration."""
        config = BenchmarkConfig()
        
        assert config.num_texts == 1000
        assert config.text_lengths == [50, 150, 300]
        assert config.batch_sizes == [1, 16, 32, 64]
        assert config.warmup_runs == 3
        assert config.measurement_runs == 5
        assert config.include_memory_profiling is True
    
    def test_custom_config(self):
        """Test custom benchmark configuration."""
        config = BenchmarkConfig(
            num_texts=500,
            text_lengths=[100, 200],
            batch_sizes=[8, 16],
            warmup_runs=2,
            measurement_runs=3,
            include_memory_profiling=False
        )
        
        assert config.num_texts == 500
        assert config.text_lengths == [100, 200]
        assert config.batch_sizes == [8, 16]
        assert config.warmup_runs == 2
        assert config.measurement_runs == 3
        assert config.include_memory_profiling is False


class TestBenchmarkResult:
    """Test BenchmarkResult data class."""
    
    def test_result_creation(self):
        """Test benchmark result with realistic data."""
        result = BenchmarkResult(
            model_name="stella-1.5b-v5",
            device="mps",
            avg_time_per_text=0.045,
            throughput_texts_per_second=22.2,
            peak_memory_mb=2800.5,
            batch_performance={16: 0.032, 32: 0.028, 64: 0.025},
            dimension=1024
        )
        
        assert result.model_name == "stella-1.5b-v5"
        assert result.device == "mps"
        assert result.avg_time_per_text == 0.045
        assert result.throughput_texts_per_second == 22.2
        assert result.peak_memory_mb == 2800.5
        assert result.batch_performance[32] == 0.028
        assert result.dimension == 1024


class TestCreateTestCorpus:
    """Test test corpus generation."""
    
    def test_create_test_corpus_default(self):
        """Test creating test corpus with default parameters."""
        corpus = create_test_corpus()
        
        assert len(corpus) == 1000
        assert all(isinstance(text, str) for text in corpus)
        assert all(len(text) > 0 for text in corpus)
    
    def test_create_test_corpus_custom_size(self):
        """Test creating test corpus with custom size."""
        corpus = create_test_corpus(num_texts=100)
        
        assert len(corpus) == 100
    
    def test_create_test_corpus_text_lengths(self):
        """Test test corpus has varied text lengths."""
        corpus = create_test_corpus(num_texts=300, text_lengths=[50, 150, 300])
        
        short_texts = [t for t in corpus if len(t) <= 80]
        medium_texts = [t for t in corpus if 80 < len(t) <= 200]
        long_texts = [t for t in corpus if len(t) > 200]
        
        # Should have variety in lengths
        assert len(short_texts) > 0
        assert len(medium_texts) > 0
        assert len(long_texts) > 0
    
    def test_create_test_corpus_chat_like_content(self):
        """Test corpus contains realistic chat-like messages."""
        corpus = create_test_corpus(num_texts=50)
        
        # Should contain some conversational patterns
        conversational_indicators = ["how", "what", "when", "!", "?", "thanks", "please"]
        found_indicators = 0
        
        for text in corpus[:20]:  # Sample first 20
            if any(indicator in text.lower() for indicator in conversational_indicators):
                found_indicators += 1
        
        assert found_indicators > 0  # Should have some conversational content


class TestBenchmarkRunner:
    """Test BenchmarkRunner functionality."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock embedding provider."""
        provider = Mock(spec=BaseEmbeddingProvider)
        provider.encode = AsyncMock()
        provider.encode_batch = AsyncMock()
        model_info_mock = Mock()
        model_info_mock.name = "test-model"
        model_info_mock.dimension = 384
        provider.get_model_info = Mock(return_value=model_info_mock)
        provider.get_embedding_dimension = Mock(return_value=384)
        return provider
    
    @pytest.fixture
    def benchmark_config(self):
        """Create a benchmark configuration for testing."""
        return BenchmarkConfig(
            num_texts=50,  # Small for fast tests
            text_lengths=[50, 100],
            batch_sizes=[1, 8],
            warmup_runs=1,
            measurement_runs=2,
            include_memory_profiling=False
        )
    
    def test_runner_initialization(self, benchmark_config):
        """Test BenchmarkRunner initialization."""
        runner = BenchmarkRunner(config=benchmark_config)
        
        assert runner.config == benchmark_config
        assert hasattr(runner, 'run_benchmark')
        assert hasattr(runner, 'compare_models')
    
    @pytest.mark.asyncio
    async def test_run_single_benchmark(self, mock_provider, benchmark_config):
        """Test running benchmark on single provider."""
        # Setup mock to return consistent timing
        mock_provider.encode.return_value = [0.1] * 384
        mock_provider.encode_batch.return_value = [[0.1] * 384] * 8
        
        runner = BenchmarkRunner(config=benchmark_config)
        result = await runner.run_benchmark(mock_provider, device="cpu")
        
        assert isinstance(result, BenchmarkResult)
        assert result.model_name == "test-model"
        assert result.device == "cpu"
        assert result.avg_time_per_text > 0
        assert result.throughput_texts_per_second > 0
        assert len(result.batch_performance) > 0
    
    @pytest.mark.asyncio
    async def test_benchmark_warmup_runs(self, mock_provider, benchmark_config):
        """Test that warmup runs are executed before measurement."""
        call_count = 0
        
        async def count_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return [0.1] * 384
        
        mock_provider.encode.side_effect = count_calls
        mock_provider.encode_batch.side_effect = lambda texts: [[0.1] * 384] * len(texts)
        
        runner = BenchmarkRunner(config=benchmark_config)
        await runner.run_benchmark(mock_provider, device="cpu")
        
        # Should have made calls for warmup + measurement
        assert call_count >= benchmark_config.warmup_runs
    
    @pytest.mark.asyncio
    async def test_batch_performance_measurement(self, mock_provider, benchmark_config):
        """Test batch performance is measured correctly."""
        times_called = []
        
        async def track_batch_calls(texts):
            start_time = time.time()
            await asyncio.sleep(0.001 * len(texts))  # Simulate batch processing time
            times_called.append((len(texts), time.time() - start_time))
            return [[0.1] * 384] * len(texts)
        
        mock_provider.encode_batch.side_effect = track_batch_calls
        
        runner = BenchmarkRunner(config=benchmark_config)
        result = await runner.run_benchmark(mock_provider, device="cpu")
        
        # Should have measured different batch sizes
        assert len(result.batch_performance) == len(benchmark_config.batch_sizes)
        
        # Larger batches should generally be more efficient per text
        batch_1 = result.batch_performance[1]
        batch_8 = result.batch_performance[8] 
        assert batch_8 <= batch_1  # More efficient per text


class TestModelComparison:
    """Test model comparison functionality."""
    
    @pytest.fixture
    def benchmark_results(self):
        """Create sample benchmark results for comparison."""
        result1 = BenchmarkResult(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            avg_time_per_text=0.015,
            throughput_texts_per_second=66.7,
            peak_memory_mb=500.0,
            batch_performance={16: 0.012, 32: 0.010},
            dimension=384
        )
        
        result2 = BenchmarkResult(
            model_name="stella-1.5b-v5",
            device="mps",
            avg_time_per_text=0.045,
            throughput_texts_per_second=22.2,
            peak_memory_mb=2800.0,
            batch_performance={16: 0.032, 32: 0.028},
            dimension=1024
        )
        
        return [result1, result2]
    
    def test_model_comparison_creation(self, benchmark_results):
        """Test ModelComparison with multiple results."""
        comparison = ModelComparison(results=benchmark_results)
        
        assert len(comparison.results) == 2
        assert comparison.fastest_model == "all-MiniLM-L6-v2"
        assert comparison.highest_throughput == "all-MiniLM-L6-v2"
        assert comparison.lowest_memory == "all-MiniLM-L6-v2"
    
    def test_get_recommendation(self, benchmark_results):
        """Test getting model recommendation based on priorities."""
        comparison = ModelComparison(results=benchmark_results)
        
        # Speed priority should recommend faster model
        speed_rec = comparison.get_recommendation(priority="speed")
        assert speed_rec.model_name == "all-MiniLM-L6-v2"
        
        # Quality priority might recommend higher-dimensional model
        quality_rec = comparison.get_recommendation(priority="quality")
        assert quality_rec.model_name == "stella-1.5b-v5"  # Higher dimension
        
        # Memory priority should recommend lower memory model
        memory_rec = comparison.get_recommendation(priority="memory")
        assert memory_rec.model_name == "all-MiniLM-L6-v2"
    
    def test_generate_report(self, benchmark_results):
        """Test generating comparison report."""
        comparison = ModelComparison(results=benchmark_results)
        report = comparison.generate_report()
        
        assert isinstance(report, str)
        assert "all-MiniLM-L6-v2" in report
        assert "stella-1.5b-v5" in report
        assert "throughput" in report.lower()
        assert "memory" in report.lower()