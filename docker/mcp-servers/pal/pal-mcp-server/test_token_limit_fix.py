#!/usr/bin/env python3
"""
Test Zen MCP token limit fix.

Validates:
1. Token estimation utility
2. Budget enforcement on ToolOutput
3. Content truncation with metadata
4. Passthrough for under-budget responses
"""

import json
import sys
sys.path.insert(0, '.')

from mcp.types import TextContent


# Import the functions we added to server.py
from server import estimate_tokens, enforce_token_budget_on_tool_output, SAFE_TOKEN_BUDGET, MCP_MAX_TOKENS


def test_token_estimation():
    """Test token estimation matches pattern."""
    print("🔍 Test 1: Token Estimation")

    assert estimate_tokens("a" * 1000) == 250
    assert estimate_tokens("") == 0
    assert estimate_tokens(None) == 0

    print("  ✅ 1K chars = 250 tokens")
    print("  ✅ Empty/None handled correctly")


def test_under_budget_passthrough():
    """Test that under-budget responses pass through unchanged."""
    print("\n🔍 Test 2: Under-Budget Passthrough")

    # Create small ToolOutput
    tool_output = {
        "status": "success",
        "content": "This is a small response that fits easily within budget.",
        "content_type": "text",
        "metadata": {"tool_name": "test"}
    }

    result = [TextContent(type="text", text=json.dumps(tool_output))]
    original_text = result[0].text

    # Apply budget enforcement
    modified = enforce_token_budget_on_tool_output(result, "test_tool")

    assert len(modified) == 1
    assert modified[0].text == original_text
    assert "token_budget_truncated" not in json.loads(modified[0].text).get("metadata", {})

    print("  ✅ Small response passed through unchanged")


def test_over_budget_truncation():
    """Test that over-budget responses get truncated."""
    print("\n🔍 Test 3: Over-Budget Truncation")

    # Create large ToolOutput (40K chars = 10K tokens, exceeds 9K budget)
    large_content = "x" * 40000

    tool_output = {
        "status": "success",
        "content": large_content,
        "content_type": "text",
        "metadata": {"tool_name": "thinkdeep"}
    }

    result = [TextContent(type="text", text=json.dumps(tool_output))]
    original_tokens = estimate_tokens(result[0].text)

    print(f"  📊 Original: {original_tokens} tokens (exceeds {SAFE_TOKEN_BUDGET})")

    # Apply budget enforcement
    modified = enforce_token_budget_on_tool_output(result, "thinkdeep")

    assert len(modified) == 1

    # Parse modified output
    modified_output = json.loads(modified[0].text)
    modified_tokens = estimate_tokens(modified[0].text)

    print(f"  📊 Modified: {modified_tokens} tokens")

    # Verify truncation
    assert modified_tokens < SAFE_TOKEN_BUDGET, f"Expected < {SAFE_TOKEN_BUDGET}, got {modified_tokens}"
    assert modified_tokens < MCP_MAX_TOKENS, f"Must be under MCP limit {MCP_MAX_TOKENS}"
    assert "truncated" in modified_output['content'].lower(), "Should contain truncation notice"
    assert modified_output['metadata']['token_budget_truncated'] == True
    assert modified_output['metadata']['original_tokens'] == original_tokens

    print(f"  ✅ Truncated from {original_tokens} → {modified_tokens} tokens")
    print(f"  ✅ Truncation metadata added")
    print(f"  ✅ Under MCP 10K limit")


def test_multi_step_scenario():
    """Test realistic multi-step tool scenario."""
    print("\n🔍 Test 4: Multi-Step Tool Scenario")

    # Simulate thinkdeep step 10 with accumulated findings
    accumulated_findings = "\n".join([
        f"Step {i} findings: " + ("Important discovery. " * 100)
        for i in range(1, 11)
    ])

    tool_output = {
        "status": "pause_for_thinkdeep",
        "content": f"Analysis complete.\n\nFindings:\n{accumulated_findings}\n\nRecommendations: ...",
        "content_type": "text",
        "metadata": {
            "tool_name": "thinkdeep",
            "step_number": 10,
            "total_steps": 10
        }
    }

    result = [TextContent(type="text", text=json.dumps(tool_output))]
    original_tokens = estimate_tokens(result[0].text)

    print(f"  📊 Step 10 with accumulated findings: {original_tokens} tokens")

    # Apply budget enforcement
    modified = enforce_token_budget_on_tool_output(result, "thinkdeep")

    modified_output = json.loads(modified[0].text)
    modified_tokens = estimate_tokens(modified[0].text)

    print(f"  📊 After truncation: {modified_tokens} tokens")

    assert modified_tokens < SAFE_TOKEN_BUDGET
    if original_tokens > SAFE_TOKEN_BUDGET:
        assert modified_output['metadata']['token_budget_truncated'] == True
        print(f"  ✅ Multi-step response truncated successfully")
    else:
        print(f"  ✅ Multi-step response under budget (no truncation needed)")


def test_non_tooloutput_passthrough():
    """Test that non-ToolOutput content passes through."""
    print("\n🔍 Test 5: Non-ToolOutput Passthrough")

    # Create plain text content (not ToolOutput JSON)
    result = [TextContent(type="text", text="Plain text response")]

    # Apply budget enforcement
    modified = enforce_token_budget_on_tool_output(result, "test_tool")

    assert len(modified) == 1
    assert modified[0].text == "Plain text response"

    print("  ✅ Non-ToolOutput content passed through unchanged")


if __name__ == "__main__":
    print("=" * 60)
    print("Zen MCP Token Limit Fix - Validation Tests")
    print("=" * 60)

    try:
        test_token_estimation()
        test_under_budget_passthrough()
        test_over_budget_truncation()
        test_multi_step_scenario()
        test_non_tooloutput_passthrough()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n💡 Next: Restart Claude Code to load the fix")
        print("   Timeout handling: Already managed by model providers (no additional fix needed)")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
