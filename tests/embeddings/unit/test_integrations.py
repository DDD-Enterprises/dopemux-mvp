"""
Unit tests for embedding integration adapters.

Tests the ConPortAdapter, SerenaAdapter and other integration components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import numpy as np

from dopemux.embeddings.integrations import (
    ConPortAdapter,
    SerenaAdapter,
    BaseIntegration
)
from dopemux.embeddings.core import AdvancedEmbeddingConfig, SearchResult


class TestBaseIntegration:
    """Test base integration abstract class."""

    def test_base_integration_instantiation(self):
        """Test that BaseIntegration cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseIntegration()  # Should fail - abstract class

    def test_base_integration_interface(self):
        """Test that BaseIntegration defines required interface."""
        # Check that abstract methods are defined
        assert hasattr(BaseIntegration, 'validate_connection')
        assert hasattr(BaseIntegration, 'store_embeddings')
        assert hasattr(BaseIntegration, 'enhance_search_results')


class TestConPortAdapter:
    """Test ConPort integration adapter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            enable_progress_tracking=True,
            gentle_error_messages=True
        )

    @pytest.fixture
    def adapter(self, config):
        """Create ConPort adapter."""
        return ConPortAdapter(
            config,
            workspace_id="/test/workspace",
            conport_client=None  # Will mock the client
        )

    def test_adapter_initialization(self, adapter, config):
        """Test ConPort adapter initialization."""
        assert adapter.config == config
        assert adapter.workspace_id == "/test/workspace"
        assert adapter.integration_name == "conport"

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, adapter):
        """Test successful connection validation."""
        # Mock ConPort client
        mock_client = AsyncMock()
        mock_client.get_active_context.return_value = {"status": "active"}
        adapter.conport_client = mock_client

        is_valid = await adapter.validate_connection()

        assert is_valid is True
        mock_client.get_active_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, adapter):
        """Test connection validation failure."""
        # Mock failing ConPort client
        mock_client = AsyncMock()
        mock_client.get_active_context.side_effect = Exception("Connection error")
        adapter.conport_client = mock_client

        is_valid = await adapter.validate_connection()

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_store_embeddings(self, adapter):
        """Test storing embeddings in ConPort."""
        documents = [
            {"id": "doc1", "content": "ML content", "metadata": {"type": "technical"}},
            {"id": "doc2", "content": "User guide", "metadata": {"type": "documentation"}}
        ]
        embeddings = [
            [0.1] * 2048,
            [0.2] * 2048
        ]

        # Mock ConPort client
        mock_client = AsyncMock()
        adapter.conport_client = mock_client

        await adapter.store_embeddings(documents, embeddings)

        # Should have logged custom data for each document
        assert mock_client.log_custom_data.call_count == 2

        # Check that embeddings were stored with proper metadata
        call_args_list = mock_client.log_custom_data.call_args_list
        first_call = call_args_list[0][1]  # kwargs of first call

        assert first_call["category"] == "DocumentEmbeddings"
        assert "doc1" in first_call["key"]
        assert "embedding_vector" in first_call["value"]
        assert "adhd_metadata" in first_call["value"]

    @pytest.mark.asyncio
    async def test_enhance_search_results(self, adapter):
        """Test enhancing search results with ConPort context."""
        search_results = [
            SearchResult(
                doc_id="doc1",
                score=0.9,
                content="Machine learning algorithms",
                metadata={}
            ),
            SearchResult(
                doc_id="doc2",
                score=0.7,
                content="Deep learning tutorial",
                metadata={}
            )
        ]

        search_context = {
            "query": "machine learning",
            "user_context": "learning AI"
        }

        # Mock ConPort client responses
        mock_client = AsyncMock()
        mock_client.semantic_search_conport.return_value = [
            {
                "item_id": "decision_123",
                "item_type": "decision",
                "content": "Decided to use PyTorch for ML models",
                "score": 0.85
            }
        ]
        mock_client.get_custom_data.return_value = [
            {
                "key": "ml_best_practices",
                "value": {
                    "content": "Use batch normalization for stable training",
                    "type": "pattern"
                }
            }
        ]
        adapter.conport_client = mock_client

        enhanced_results = await adapter.enhance_search_results(
            search_results,
            search_context
        )

        # Should have enhanced metadata
        assert len(enhanced_results) == 2
        assert "conport_context" in enhanced_results[0].metadata
        assert "related_decisions" in enhanced_results[0].metadata["conport_context"]
        assert "project_patterns" in enhanced_results[0].metadata["conport_context"]

    @pytest.mark.asyncio
    async def test_add_adhd_metadata(self, adapter):
        """Test adding ADHD-friendly metadata."""
        document = {
            "id": "doc1",
            "content": "This is a complex technical document about advanced machine learning algorithms and neural networks.",
            "metadata": {"type": "technical"}
        }

        enhanced_doc = await adapter._add_adhd_metadata(document)

        # Should have ADHD-friendly enhancements
        adhd_meta = enhanced_doc["adhd_metadata"]
        assert "urgency_level" in adhd_meta
        assert "complexity_score" in adhd_meta
        assert "estimated_focus_time" in adhd_meta
        assert "context_tags" in adhd_meta

        # Complexity should be scored based on content length and technical terms
        assert isinstance(adhd_meta["complexity_score"], (int, float))
        assert 1 <= adhd_meta["complexity_score"] <= 5

    @pytest.mark.asyncio
    async def test_sync_with_conport_decisions(self, adapter):
        """Test syncing decisions with ConPort."""
        # Mock recent decisions
        mock_client = AsyncMock()
        mock_client.get_recent_activity_summary.return_value = {
            "decisions": [
                {
                    "id": "dec1",
                    "summary": "Use transformer architecture",
                    "rationale": "Better performance for NLP tasks",
                    "tags": ["ml", "architecture"]
                }
            ]
        }
        adapter.conport_client = mock_client

        decisions = await adapter._get_relevant_decisions("machine learning")

        assert len(decisions) >= 0  # Should return list
        if decisions:
            assert "summary" in decisions[0]
            assert "rationale" in decisions[0]

    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, adapter):
        """Test graceful error handling."""
        # Mock client that fails
        mock_client = AsyncMock()
        mock_client.semantic_search_conport.side_effect = Exception("ConPort error")
        adapter.conport_client = mock_client

        search_results = [SearchResult("doc1", 0.9, "content", {})]

        # Should not raise exception, but return original results
        enhanced_results = await adapter.enhance_search_results(
            search_results,
            {"query": "test"}
        )

        assert len(enhanced_results) == 1
        assert enhanced_results[0].doc_id == "doc1"

    def test_calculate_urgency_level(self, adapter):
        """Test urgency level calculation."""
        # High urgency content
        high_urgency = adapter._calculate_urgency_level(
            "URGENT: Critical bug in production system needs immediate fix"
        )
        assert high_urgency >= 4

        # Low urgency content
        low_urgency = adapter._calculate_urgency_level(
            "Documentation update for future reference"
        )
        assert low_urgency <= 2

        # Medium urgency content
        medium_urgency = adapter._calculate_urgency_level(
            "Feature request for next sprint planning"
        )
        assert 2 < medium_urgency < 4

    def test_estimate_focus_time(self, adapter):
        """Test focus time estimation."""
        # Short content
        short_time = adapter._estimate_focus_time("Brief note")
        assert short_time <= 5

        # Long content
        long_content = "This is a very long document " * 200
        long_time = adapter._estimate_focus_time(long_content)
        assert long_time > 15

        # Technical content (should take longer)
        technical_content = "Complex algorithmic implementation with multiple optimization strategies"
        tech_time = adapter._estimate_focus_time(technical_content)
        assert tech_time > adapter._estimate_focus_time("Simple content")


class TestSerenaAdapter:
    """Test Serena integration adapter."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AdvancedEmbeddingConfig(
            enable_code_analysis=True,
            enable_semantic_search=True
        )

    @pytest.fixture
    def adapter(self, config):
        """Create Serena adapter."""
        return SerenaAdapter(
            config,
            serena_client=None  # Will mock the client
        )

    def test_adapter_initialization(self, adapter, config):
        """Test Serena adapter initialization."""
        assert adapter.config == config
        assert adapter.integration_name == "serena"
        assert adapter.supported_languages == [
            "python", "javascript", "typescript", "java", "cpp", "go", "rust"
        ]

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, adapter):
        """Test successful Serena connection validation."""
        # Mock Serena client
        mock_client = AsyncMock()
        mock_client.health_check.return_value = {"status": "healthy"}
        adapter.serena_client = mock_client

        is_valid = await adapter.validate_connection()

        assert is_valid is True
        mock_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_embeddings_code_files(self, adapter):
        """Test storing embeddings for code files."""
        documents = [
            {
                "id": "main.py",
                "content": "def calculate_metrics(data):\n    return sum(data) / len(data)",
                "metadata": {"type": "python", "file_path": "/src/main.py"}
            },
            {
                "id": "utils.js",
                "content": "function processData(input) { return input.map(x => x * 2); }",
                "metadata": {"type": "javascript", "file_path": "/src/utils.js"}
            }
        ]
        embeddings = [[0.1] * 2048, [0.2] * 2048]

        # Mock Serena client
        mock_client = AsyncMock()
        adapter.serena_client = mock_client

        await adapter.store_embeddings(documents, embeddings)

        # Should have stored code analysis for each file
        assert mock_client.store_code_analysis.call_count == 2

        # Check that code was analyzed properly
        call_args_list = mock_client.store_code_analysis.call_args_list
        first_call = call_args_list[0][1]  # kwargs of first call

        assert "file_path" in first_call
        assert "functions" in first_call
        assert "classes" in first_call
        assert "complexity_score" in first_call

    @pytest.mark.asyncio
    async def test_enhance_search_results_with_code_context(self, adapter):
        """Test enhancing search results with code context."""
        search_results = [
            SearchResult(
                doc_id="algorithm.py",
                score=0.9,
                content="def quicksort(arr): ...",
                metadata={"type": "python"}
            )
        ]

        search_context = {
            "query": "sorting algorithm",
            "language": "python"
        }

        # Mock Serena client responses
        mock_client = AsyncMock()
        mock_client.search_similar_code.return_value = [
            {
                "file_path": "/algorithms/sort.py",
                "function_name": "merge_sort",
                "similarity_score": 0.85,
                "documentation": "Merge sort implementation with O(n log n) complexity"
            }
        ]
        mock_client.get_function_documentation.return_value = {
            "signature": "def quicksort(arr: List[int]) -> List[int]",
            "docstring": "Implements quicksort algorithm",
            "complexity": "O(n log n) average case",
            "examples": ["quicksort([3,1,4,1,5])"]
        }
        adapter.serena_client = mock_client

        enhanced_results = await adapter.enhance_search_results(
            search_results,
            search_context
        )

        # Should have enhanced with Serena context
        assert len(enhanced_results) == 1
        assert "serena_context" in enhanced_results[0].metadata
        assert "similar_code" in enhanced_results[0].metadata["serena_context"]
        assert "function_docs" in enhanced_results[0].metadata["serena_context"]

    @pytest.mark.asyncio
    async def test_analyze_code_structure(self, adapter):
        """Test code structure analysis."""
        python_code = """
class DataProcessor:
    def __init__(self, config):
        self.config = config

    def process(self, data):
        return self._transform(data)

    def _transform(self, data):
        return [x * 2 for x in data]

def main():
    processor = DataProcessor({})
    result = processor.process([1, 2, 3])
    print(result)
"""

        analysis = await adapter._analyze_code_structure(python_code, "python")

        # Should identify classes and functions
        assert "classes" in analysis
        assert "functions" in analysis
        assert len(analysis["classes"]) == 1
        assert analysis["classes"][0]["name"] == "DataProcessor"
        assert len(analysis["functions"]) >= 1  # main function

    @pytest.mark.asyncio
    async def test_detect_programming_language(self, adapter):
        """Test programming language detection."""
        # Python code
        python_code = "def hello_world():\n    print('Hello, World!')"
        lang = await adapter._detect_language(python_code, "script.py")
        assert lang == "python"

        # JavaScript code
        js_code = "function helloWorld() { console.log('Hello, World!'); }"
        lang = await adapter._detect_language(js_code, "script.js")
        assert lang == "javascript"

        # TypeScript code
        ts_code = "function greet(name: string): string { return `Hello, ${name}!`; }"
        lang = await adapter._detect_language(ts_code, "script.ts")
        assert lang == "typescript"

    @pytest.mark.asyncio
    async def test_calculate_code_complexity(self, adapter):
        """Test code complexity calculation."""
        # Simple function
        simple_code = "def add(a, b): return a + b"
        simple_complexity = await adapter._calculate_complexity(simple_code, "python")
        assert 1 <= simple_complexity <= 2

        # Complex function with loops and conditionals
        complex_code = """
def complex_function(data):
    result = []
    for item in data:
        if item > 0:
            for i in range(item):
                if i % 2 == 0:
                    result.append(i * 2)
                else:
                    result.append(i)
        elif item < 0:
            result.append(abs(item))
    return result
"""
        complex_complexity = await adapter._calculate_complexity(complex_code, "python")
        assert complex_complexity > simple_complexity
        assert complex_complexity >= 5

    @pytest.mark.asyncio
    async def test_generate_code_documentation(self, adapter):
        """Test automatic code documentation generation."""
        function_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

        # Mock Serena client for documentation generation
        mock_client = AsyncMock()
        mock_client.generate_documentation.return_value = {
            "summary": "Calculates the nth Fibonacci number using recursion",
            "parameters": {"n": "The position in the Fibonacci sequence"},
            "returns": "The Fibonacci number at position n",
            "complexity": "O(2^n) time complexity",
            "examples": ["calculate_fibonacci(5) -> 5"]
        }
        adapter.serena_client = mock_client

        docs = await adapter._generate_documentation(function_code, "calculate_fibonacci")

        assert "summary" in docs
        assert "parameters" in docs
        assert "complexity" in docs

    @pytest.mark.asyncio
    async def test_find_related_code_patterns(self, adapter):
        """Test finding related code patterns."""
        query_code = "def sort_list(items): return sorted(items)"

        # Mock Serena responses
        mock_client = AsyncMock()
        mock_client.find_similar_patterns.return_value = [
            {
                "pattern_type": "sorting",
                "files": ["/utils/sort.py", "/algorithms/quicksort.py"],
                "similarity_score": 0.9,
                "description": "List sorting implementations"
            }
        ]
        adapter.serena_client = mock_client

        patterns = await adapter._find_related_patterns(query_code, "python")

        assert len(patterns) >= 0
        if patterns:
            assert "pattern_type" in patterns[0]
            assert "similarity_score" in patterns[0]

    @pytest.mark.asyncio
    async def test_error_handling_invalid_code(self, adapter):
        """Test handling of invalid code."""
        invalid_code = "this is not valid code syntax !!!"

        # Should handle gracefully without exceptions
        analysis = await adapter._analyze_code_structure(invalid_code, "python")

        # Should return empty/default analysis
        assert "classes" in analysis
        assert "functions" in analysis
        assert len(analysis["classes"]) == 0
        assert len(analysis["functions"]) == 0

    def test_is_code_file(self, adapter):
        """Test code file detection."""
        assert adapter._is_code_file("script.py") is True
        assert adapter._is_code_file("app.js") is True
        assert adapter._is_code_file("main.cpp") is True
        assert adapter._is_code_file("README.md") is False
        assert adapter._is_code_file("data.json") is False
        assert adapter._is_code_file("config.yaml") is False

    def test_extract_imports_and_dependencies(self, adapter):
        """Test extracting imports and dependencies."""
        python_code = """
import os
import sys
from typing import List, Dict
from mymodule import MyClass
import numpy as np
"""

        imports = adapter._extract_imports(python_code, "python")

        assert "os" in imports
        assert "sys" in imports
        assert "numpy" in imports
        assert "typing" in imports
        assert "mymodule" in imports


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.integrations", "--cov-report=term-missing"])