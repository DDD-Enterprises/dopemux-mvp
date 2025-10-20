#!/usr/bin/env python3
"""
Leantime-Bridge MCP Token Limit Fix - Validation Tests

Tests the MCP boundary enforcement implementation to ensure:
1. Token estimation is accurate
2. Under-budget TextContent passes through unchanged
3. Over-budget TextContent is truncated correctly
4. Metadata is added for transparency
"""

import sys
sys.path.insert(0, './leantime_bridge')
from server import estimate_tokens, enforce_token_budget_on_text_content, SAFE_TOKEN_BUDGET
from mcp import types

def test_token_estimation():
    """Test token estimation accuracy"""
    print("=" * 60)
    print("Test 1: Token Estimation")
    print("=" * 60)

    text_1k = "x" * 4000  # 4000 chars = ~1000 tokens
    estimated = estimate_tokens(text_1k)

    print(f"Input: 4000 characters")
    print(f"Expected: ~1000 tokens")
    print(f"Estimated: {estimated} tokens")

    assert 900 <= estimated <= 1100, f"Token estimation out of range: {estimated}"
    print("✅ PASS: Token estimation accurate\n")

def test_under_budget():
    """Test TextContent under budget passes through unchanged"""
    print("=" * 60)
    print("Test 2: Under-Budget Pass-Through")
    print("=" * 60)

    small_text = "Projects: " + str([
        {"id": i, "name": f"Project {i}", "status": "active"}
        for i in range(5)
    ])

    small_content = [types.TextContent(type="text", text=small_text)]
    original_tokens = estimate_tokens(small_text)

    result = enforce_token_budget_on_text_content(small_content, 'list_projects')
    result_tokens = estimate_tokens(result[0].text)

    print(f"Original: {original_tokens} tokens")
    print(f"Budget: {SAFE_TOKEN_BUDGET} tokens")
    print(f"Under budget: {original_tokens < SAFE_TOKEN_BUDGET}")

    assert "_Original tokens:" not in result[0].text, "Should not have truncation metadata"
    assert result[0].text == small_text, "Text should be unchanged"
    print("✅ PASS: Under-budget TextContent passes through unchanged\n")

def test_over_budget_truncation():
    """Test over-budget TextContent gets truncated correctly"""
    print("=" * 60)
    print("Test 3: Over-Budget Truncation")
    print("=" * 60)

    # Create large project list that will exceed 9K tokens
    large_text = "Projects: " + str([
        {
            "id": i,
            "name": f"Project {i}",
            "description": "x" * 500,  # 500 chars per project
            "status": "active",
            "created": "2025-01-01",
            "tickets": [
                {
                    "id": j,
                    "title": f"Ticket {j}",
                    "description": "x" * 200
                }
                for j in range(10)
            ]
        }
        for i in range(100)  # 100 projects with lots of data
    ])

    large_content = [types.TextContent(type="text", text=large_text)]
    original_tokens = estimate_tokens(large_text)

    result = enforce_token_budget_on_text_content(large_content, 'list_projects')
    truncated_tokens = estimate_tokens(result[0].text)

    print(f"Original: {original_tokens} tokens (OVER BUDGET)")
    print(f"Budget: {SAFE_TOKEN_BUDGET} tokens")
    print(f"Truncated: {truncated_tokens} tokens")
    print(f"Reduction: {original_tokens - truncated_tokens} tokens ({100 * (1 - truncated_tokens/original_tokens):.1f}%)")

    # Verify truncation occurred
    assert truncated_tokens < SAFE_TOKEN_BUDGET, f"Truncated result still over budget: {truncated_tokens}"
    assert "[truncated to fit MCP 10K token budget]" in result[0].text, "Should have truncation message"
    assert "_Original tokens:" in result[0].text, "Should track original size"
    assert "_Truncated tokens:" in result[0].text, "Should track truncated size"

    print(f"\nTruncation Metadata:")
    print(f"  Truncation message: Present ✅")
    print(f"  Original tokens tracked: Present ✅")
    print(f"  Truncated tokens tracked: Present ✅")

    # Verify text was actually truncated
    assert len(result[0].text) < len(large_text), "Text should be shorter after truncation"

    print("\n✅ PASS: Over-budget TextContent truncated correctly\n")

def test_empty_content():
    """Test empty TextContent is handled correctly"""
    print("=" * 60)
    print("Test 4: Empty Content Handling")
    print("=" * 60)

    empty_content = []
    result = enforce_token_budget_on_text_content(empty_content, 'test_tool')

    print(f"Input: Empty list")
    print(f"Output: {result}")

    assert result == [], "Empty content should return empty list"
    print("✅ PASS: Empty content handled correctly\n")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Leantime-Bridge MCP Token Limit Fix - Validation Tests")
    print("=" * 60)
    print()

    try:
        test_token_estimation()
        test_under_budget()
        test_over_budget_truncation()
        test_empty_content()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Leantime-Bridge token limit fix validated successfully.")
        print("=" * 60)
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
