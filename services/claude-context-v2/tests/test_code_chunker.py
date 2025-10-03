"""
Tests for Tree-sitter Code Chunker - Task 2
"""

import pytest
from pathlib import Path
from src.preprocessing.code_chunker import (
    ChunkingConfig,
    CodeChunk,
    CodeChunker,
)


@pytest.fixture
def chunker():
    """Create CodeChunker instance for testing."""
    config = ChunkingConfig(
        target_chunk_tokens=512,
        max_chunk_tokens=1024,
        min_chunk_tokens=128,
    )
    return CodeChunker(config=config)


def test_chunk_python_class(chunker):
    """Test chunking Python class."""
    code = '''
class UserService:
    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int):
        """Fetch user by ID."""
        return await self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?", user_id
        )
'''

    chunks = chunker.chunk_code_string(code, language="python")

    # Should produce chunks (Tree-sitter or fallback)
    assert len(chunks) >= 1

    # If Tree-sitter available, check semantic chunking
    if chunker.parsers:
        # First should be the class
        class_chunk = chunks[0]
        assert class_chunk.chunk_type == "class"
        assert class_chunk.symbol_name == "UserService"

        # Methods should have parent context
        method_chunks = [c for c in chunks if c.chunk_type == "method"]
        if method_chunks:
            assert all(c.parent_symbol == "UserService" for c in method_chunks)
    else:
        # Fallback mode - basic block chunks
        assert all(c.chunk_type == "block" for c in chunks)


def test_chunk_python_function(chunker):
    """Test chunking standalone Python function."""
    code = '''
def calculate_total(items: List[Item]) -> float:
    total = 0.0
    for item in items:
        if item.discount:
            total += item.price * (1 - item.discount)
        else:
            total += item.price
    return total
'''

    chunks = chunker.chunk_code_string(code, language="python")

    assert len(chunks) >= 1
    func_chunk = chunks[0]

    # Tree-sitter mode: semantic extraction
    if chunker.parsers:
        assert func_chunk.chunk_type == "function"
        assert func_chunk.symbol_name == "calculate_total"
        assert func_chunk.parent_symbol is None
    else:
        # Fallback mode: block chunks
        assert func_chunk.chunk_type == "block"


def test_complexity_scoring(chunker):
    """Test ADHD complexity scoring."""
    # Skip if Tree-sitter not available (fallback has no complexity scoring)
    if not chunker.parsers:
        pytest.skip("Tree-sitter not available - complexity scoring requires AST")

    # Simple function
    simple_code = '''
def add(a, b):
    return a + b
'''

    simple_chunks = chunker.chunk_code_string(simple_code, language="python")
    simple_complexity = simple_chunks[0].complexity if simple_chunks else 0.0

    # Complex function with nesting and branches
    complex_code = '''
def process_data(data):
    results = []
    for item in data:
        if item.valid:
            try:
                if item.type == "A":
                    for sub in item.children:
                        if sub.active:
                            results.append(process_sub(sub))
            except Exception:
                pass
    return results
'''

    complex_chunks = chunker.chunk_code_string(complex_code, language="python")
    complex_complexity = complex_chunks[0].complexity if complex_chunks else 0.0

    # Complex should have higher complexity score
    assert complex_complexity > simple_complexity
    assert 0.0 <= simple_complexity <= 1.0
    assert 0.0 <= complex_complexity <= 1.0


def test_chunk_javascript(chunker):
    """Test chunking JavaScript code."""
    code = '''
class DataService {
    constructor(config) {
        this.config = config;
    }

    async fetchData(id) {
        const response = await fetch(`/api/data/${id}`);
        return response.json();
    }
}

const processItems = (items) => {
    return items.map(item => item.value * 2);
};
'''

    chunks = chunker.chunk_code_string(code, language="javascript")

    # Should produce chunks
    assert len(chunks) >= 1

    # Tree-sitter mode: semantic chunking
    if chunker.parsers:
        class_chunks = [c for c in chunks if c.chunk_type == "class"]
        func_chunks = [c for c in chunks if c.chunk_type == "function"]

        assert len(class_chunks) >= 1
        assert len(func_chunks) >= 1
    else:
        # Fallback mode: block chunks
        assert all(c.chunk_type == "block" for c in chunks)


def test_token_estimation(chunker):
    """Test token count estimation."""
    code = '''
def test():
    pass
'''

    chunks = chunker.chunk_code_string(code, language="python")
    chunk = chunks[0]

    # Should have reasonable token estimate
    assert chunk.tokens_estimate > 0
    assert chunk.tokens_estimate < len(code)  # Should be less than char count


def test_line_numbers(chunker):
    """Test correct line number tracking."""
    code = '''# Line 0
def foo():  # Line 1
    pass    # Line 2
            # Line 3
def bar():  # Line 4
    pass    # Line 5
'''

    chunks = chunker.chunk_code_string(code, language="python")

    # Check line numbers make sense
    for chunk in chunks:
        assert chunk.start_line >= 0
        assert chunk.end_line >= chunk.start_line
        assert chunk.end_line < len(code.split("\n"))


def test_fallback_line_chunking(chunker):
    """Test fallback line-based chunking."""
    # Test with unsupported language
    code = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

    chunks = chunker.chunk_code_string(code, language="unsupported")

    # Should still produce chunks
    assert len(chunks) >= 1
    assert all(c.chunk_type == "block" for c in chunks)


def test_empty_code(chunker):
    """Test handling of empty code."""
    chunks = chunker.chunk_code_string("", language="python")

    # Should handle gracefully
    assert isinstance(chunks, list)


def test_chunk_preserves_content(chunker):
    """Test that chunking preserves code content."""
    code = '''
def example(x):
    return x * 2
'''

    chunks = chunker.chunk_code_string(code, language="python")

    # Chunk content should match original
    if chunks:
        chunk = chunks[0]
        assert "def example" in chunk.content
        assert "return x * 2" in chunk.content


def test_multiple_functions(chunker):
    """Test chunking file with multiple functions."""
    code = '''
def func1():
    pass

def func2():
    pass

def func3():
    pass
'''

    chunks = chunker.chunk_code_string(code, language="python")

    # Should produce chunks
    assert len(chunks) >= 1

    # Tree-sitter mode: extract individual functions
    if chunker.parsers:
        assert len(chunks) == 3
        assert all(c.chunk_type == "function" for c in chunks)
        assert chunks[0].symbol_name == "func1"
        assert chunks[1].symbol_name == "func2"
        assert chunks[2].symbol_name == "func3"
    else:
        # Fallback mode: one or more block chunks
        assert all(c.chunk_type == "block" for c in chunks)


def test_nested_classes(chunker):
    """Test handling of nested class structures."""
    code = '''
class Outer:
    class Inner:
        def method(self):
            pass

    def outer_method(self):
        pass
'''

    chunks = chunker.chunk_code_string(code, language="python")

    # Should produce chunks
    assert len(chunks) >= 1

    # Tree-sitter mode: extract class hierarchy
    if chunker.parsers:
        class_chunks = [c for c in chunks if c.chunk_type == "class"]
        assert len(class_chunks) >= 1
    else:
        # Fallback mode: block chunks work fine
        assert all(c.chunk_type == "block" for c in chunks)
