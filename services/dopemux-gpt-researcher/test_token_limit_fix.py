#!/usr/bin/env python3
"""
GPT-Researcher MCP Token Limit Fix - Validation Tests

Tests the progressive truncation implementation to ensure:
1. Token estimation is accurate
2. Under-budget responses pass through unchanged
3. Over-budget responses are truncated correctly
4. Metadata is added for transparency
"""

import json
import sys
sys.path.insert(0, './mcp-server')
from server import estimate_tokens, enforce_token_budget, SAFE_TOKEN_BUDGET

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
    """Test result under budget passes through unchanged"""
    print("=" * 60)
    print("Test 2: Under-Budget Pass-Through")
    print("=" * 60)

    small_result = {
        'task_id': 'test-123',
        'status': 'completed',
        'research_type': 'quick',
        'summary': 'Short summary of research findings',
        'results': [
            {
                'question': 'Question 1',
                'answer': 'Short answer to question 1',
                'confidence': 0.85,
                'sources': ['https://example.com/source1']
            }
        ],
        'sources': ['https://example.com/source1'],
        'key_findings': ['Key finding 1'],
        'total_questions': 1,
        'confidence': 0.85
    }

    original_tokens = estimate_tokens(json.dumps(small_result, indent=2))
    truncated = enforce_token_budget(small_result, 'quick_search')

    print(f"Original: {original_tokens} tokens")
    print(f"Budget: {SAFE_TOKEN_BUDGET} tokens")
    print(f"Under budget: {original_tokens < SAFE_TOKEN_BUDGET}")

    assert '_token_budget_enforced' not in truncated, "Should not have truncation metadata"
    assert truncated == small_result, "Result should be unchanged"
    print("✅ PASS: Under-budget result passes through unchanged\n")

def test_over_budget_truncation():
    """Test over-budget result gets truncated correctly"""
    print("=" * 60)
    print("Test 3: Over-Budget Truncation")
    print("=" * 60)

    # Create large result that will exceed 9K tokens
    large_result = {
        'task_id': 'test-456',
        'status': 'completed',
        'research_type': 'deep',
        'topic': 'Test Topic',
        'summary': 'x' * 10000,  # 10K chars = 2.5K tokens
        'results': [
            {
                'question': f'Question {i}',
                'answer': 'x' * 5000,  # 5K chars each = 1.25K tokens each
                'confidence': 0.8,
                'sources': [f'https://example.com/source{j}' for j in range(20)]
            }
            for i in range(20)  # 20 results × 1.25K = 25K tokens
        ],
        'sources': [f'https://example.com/source{i}' for i in range(100)],
        'key_findings': ['Finding ' + 'x' * 1000 for i in range(20)],
        'total_questions': 20,
        'confidence': 0.8
    }

    original_tokens = estimate_tokens(json.dumps(large_result, indent=2))
    truncated = enforce_token_budget(large_result, 'deep_research')
    truncated_tokens = estimate_tokens(json.dumps(truncated, indent=2))

    print(f"Original: {original_tokens} tokens (OVER BUDGET)")
    print(f"Budget: {SAFE_TOKEN_BUDGET} tokens")
    print(f"Truncated: {truncated_tokens} tokens")
    print(f"Reduction: {original_tokens - truncated_tokens} tokens ({100 * (1 - truncated_tokens/original_tokens):.1f}%)")

    # Verify truncation occurred
    assert truncated_tokens < SAFE_TOKEN_BUDGET, f"Truncated result still over budget: {truncated_tokens}"
    assert truncated['_token_budget_enforced'] == True, "Should have truncation flag"
    assert truncated['_original_tokens'] == original_tokens, "Should track original size"

    # Verify field truncation
    print(f"\nField Truncation:")
    print(f"  Results: {len(large_result['results'])} → {len(truncated['results'])} (max 5)")
    print(f"  Sources: {len(large_result['sources'])} → {len(truncated['sources'])} (max 10)")
    print(f"  Key Findings: {len(large_result['key_findings'])} → {len(truncated['key_findings'])} (max 5)")

    assert len(truncated['results']) <= 5, "Results should be limited to 5"
    assert len(truncated['sources']) <= 10, "Sources should be limited to 10"
    assert len(truncated['key_findings']) <= 5, "Key findings should be limited to 5"

    # Verify essential fields preserved
    print(f"\nEssential Fields Preserved:")
    print(f"  task_id: {truncated['task_id']} ✅")
    print(f"  status: {truncated['status']} ✅")
    print(f"  research_type: {truncated['research_type']} ✅")

    assert truncated['task_id'] == large_result['task_id'], "task_id should be preserved"
    assert truncated['status'] == large_result['status'], "status should be preserved"
    assert truncated['research_type'] == large_result['research_type'], "research_type should be preserved"

    print("\n✅ PASS: Over-budget result truncated correctly\n")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("GPT-Researcher MCP Token Limit Fix - Validation Tests")
    print("=" * 60)
    print()

    try:
        test_token_estimation()
        test_under_budget()
        test_over_budget_truncation()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("GPT-Researcher token limit fix validated successfully.")
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
