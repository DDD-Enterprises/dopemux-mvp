#!/usr/bin/env python3
"""
Test script to verify MCP token limit fix.

Tests:
1. Token estimation accuracy
2. Code truncation with budget enforcement
3. Docs truncation with budget enforcement
4. Large result sets stay under 10K tokens
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.token_budget import (
    estimate_tokens,
    truncate_text,
    truncate_code_results,
    truncate_docs_results,
    SAFE_TOKEN_BUDGET,
    MCP_MAX_TOKENS,
)


def test_token_estimation():
    """Test token estimation is conservative."""
    print("🔍 Test 1: Token Estimation")

    # Known examples
    text_1k_chars = "a" * 1000
    estimated = estimate_tokens(text_1k_chars)

    # Should be ~250 tokens (1000 chars / 4)
    assert 200 <= estimated <= 300, f"Expected ~250, got {estimated}"
    print(f"  ✅ 1K chars = {estimated} tokens (expected ~250)")

    # Empty text
    assert estimate_tokens("") == 0
    print(f"  ✅ Empty text = 0 tokens")


def test_text_truncation():
    """Test text truncation."""
    print("\n🔍 Test 2: Text Truncation")

    short_text = "Hello world"
    truncated, was_truncated = truncate_text(short_text, max_chars=100)
    assert not was_truncated
    assert truncated == short_text
    print(f"  ✅ Short text not truncated")

    long_text = "a" * 1000
    truncated, was_truncated = truncate_text(long_text, max_chars=100)
    assert was_truncated
    assert len(truncated) == 100
    assert "truncated" in truncated
    print(f"  ✅ Long text truncated: {len(long_text)} → {len(truncated)} chars")


def test_code_truncation():
    """Test code results truncation."""
    print("\n🔍 Test 3: Code Results Truncation")

    # Create fake code results with large code snippets
    large_results = [
        {
            "file_path": f"/path/to/file{i}.py",
            "function_name": f"function_{i}",
            "language": "py",
            "code": "def example():\n" + "    " + "x" * 5000,  # Large code
            "context": f"Context for function {i}",
            "score": 0.9 - (i * 0.05),
            "reranked": True,
        }
        for i in range(10)
    ]

    # Truncate with budget
    truncated, info = truncate_code_results(
        large_results,
        budget_tokens=SAFE_TOKEN_BUDGET,
        per_item_max_chars=2000,
    )

    print(f"  📊 Original: {info.original_count} results")
    print(f"  📊 Final: {info.final_count} results")
    print(f"  📊 Tokens: {info.estimated_tokens} / {SAFE_TOKEN_BUDGET}")
    print(f"  📊 Budget used: {info.budget_used_pct:.1f}%")

    assert info.estimated_tokens <= SAFE_TOKEN_BUDGET
    assert info.estimated_tokens < MCP_MAX_TOKENS
    print(f"  ✅ Stayed under token budget")

    # Check code was truncated
    for result in truncated:
        assert "code_truncated" in result
        if result["code_truncated"]:
            assert len(result["code"]) <= 2050  # 2000 + suffix
            print(f"  ✅ Code truncated in {result['file_path']}")


def test_docs_truncation():
    """Test docs results truncation."""
    print("\n🔍 Test 4: Docs Results Truncation")

    # Create fake doc results with large text
    large_docs = [
        {
            "source_path": f"/docs/doc{i}.md",
            "text": "# Documentation\n" + "Lorem ipsum " * 1000,  # Large text
            "score": 0.85 - (i * 0.05),
            "doc_type": "md",
        }
        for i in range(10)
    ]

    # Truncate with budget
    truncated, info = truncate_docs_results(
        large_docs,
        budget_tokens=SAFE_TOKEN_BUDGET,
        per_item_max_chars=2000,
    )

    print(f"  📊 Original: {info.original_count} results")
    print(f"  📊 Final: {info.final_count} results")
    print(f"  📊 Tokens: {info.estimated_tokens} / {SAFE_TOKEN_BUDGET}")
    print(f"  📊 Budget used: {info.budget_used_pct:.1f}%")

    assert info.estimated_tokens <= SAFE_TOKEN_BUDGET
    assert info.estimated_tokens < MCP_MAX_TOKENS
    print(f"  ✅ Stayed under token budget")


def test_realistic_scenario():
    """Test with realistic code search results."""
    print("\n🔍 Test 5: Realistic Search Results")

    # Simulate 10 results with moderate code sizes
    realistic_results = [
        {
            "file_path": f"/project/src/module{i}.py",
            "function_name": f"handle_request_{i}",
            "language": "py",
            "code": """def handle_request(data):
    '''Process incoming request with validation.'''
    if not validate_input(data):
        raise ValueError("Invalid input")

    result = process_data(data)
    cache.set(data['id'], result)

    return {
        'status': 'success',
        'data': result,
        'timestamp': datetime.now().isoformat()
    }
""" * 3,  # 3x repetition for realistic size
            "context": f"Request handler for endpoint /api/v1/resource{i}",
            "relevance_score": 0.75 - (i * 0.03),
            "original_rank": i + 1,
            "reranked": True,
        }
        for i in range(10)
    ]

    # Truncate
    truncated, info = truncate_code_results(
        realistic_results,
        budget_tokens=9000,
        per_item_max_chars=2000,
    )

    print(f"  📊 Results: {info.final_count}/{info.original_count}")
    print(f"  📊 Tokens: {info.estimated_tokens} ({info.budget_used_pct:.1f}% of budget)")
    print(f"  📊 Under MCP limit: {info.estimated_tokens < MCP_MAX_TOKENS}")

    assert info.estimated_tokens < MCP_MAX_TOKENS
    print(f"  ✅ Realistic scenario passed")


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Token Limit Fix - Validation Tests")
    print("=" * 60)

    try:
        test_token_estimation()
        test_text_truncation()
        test_code_truncation()
        test_docs_truncation()
        test_realistic_scenario()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n💡 Next step: Restart Claude Code to load the fix")
        print("   Then test with: mcp__dope-context__search_code(query='MCP token limit', top_k=10)")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
