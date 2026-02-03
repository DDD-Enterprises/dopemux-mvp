#!/usr/bin/env python3
"""
Test Response Parser - Comprehensive Validation
Tests all parser features with realistic AI output samples
"""

import sys
from src.response_parser import ResponseParser, parse_response, ErrorType, ParseResult


def test_claude_parsing():
    """Test Claude response parsing."""
    print("\n🧪 Test 1: Claude Parsing")
    print("-" * 60)

    # Realistic Claude output with ANSI codes
    claude_output = [
        "\x1b[2J\x1b[H\x1b[3J",  # ANSI clear screen
        "Claude Code v1.2.0",
        "Ready to assist!",
        "",
        "> What is 2+2?",
        "\x1b[0m",  # ANSI reset
        "2 + 2 = 4",
        "",
        "Simple arithmetic! The sum of 2 and 2 equals 4.",
        "",
        "> _",  # Next prompt
    ]

    result = parse_response(claude_output, provider='claude')

    assert result.success, "Should successfully parse Claude output"
    assert "2 + 2 = 4" in result.content, "Should extract actual response"
    assert "Simple arithmetic" in result.content, "Should include multi-line response"
    assert ">" not in result.content, "Should remove prompts"
    assert "\x1b" not in result.content, "Should strip ANSI codes"

    print(f"✅ Claude parsing successful")
    print(f"   Content: {result.content[:80]}...")
    print(f"   Lines: {result.metadata.get('content_lines')}")

    return True


def test_gemini_json_parsing():
    """Test Gemini JSON mode parsing."""
    print("\n🧪 Test 2: Gemini JSON Parsing")
    print("-" * 60)

    gemini_json = [
        '{',
        '  "candidates": [',
        '    {',
        '      "content": {',
        '        "parts": [',
        '          {"text": "Async Python uses asyncio for concurrent operations."}',
        '        ]',
        '      },',
        '      "finishReason": "STOP"',
        '    }',
        '  ]',
        '}'
    ]

    result = parse_response(gemini_json, provider='gemini')

    assert result.success, "Should successfully parse Gemini JSON"
    assert "Async Python" in result.content, "Should extract text from JSON"
    assert "candidates" not in result.content, "Should not include JSON structure"

    print(f"✅ Gemini JSON parsing successful")
    print(f"   Content: {result.content}")

    return True


def test_gemini_prose_parsing():
    """Test Gemini prose mode parsing."""
    print("\n🧪 Test 3: Gemini Prose Parsing")
    print("-" * 60)

    gemini_prose = [
        "Gemini CLI",
        "",
        "Authentication best practices include:",
        "1. Use OAuth 2.0 for third-party access",
        "2. Implement CSRF protection",
        "3. Store passwords with bcrypt",
        "",
        "These provide strong security."
    ]

    result = parse_response(gemini_prose, provider='gemini')

    assert result.success, "Should successfully parse Gemini prose"
    assert "OAuth 2.0" in result.content, "Should extract content"
    assert "Gemini CLI" not in result.content, "Should remove banner"

    print(f"✅ Gemini prose parsing successful")
    print(f"   Content lines: {len(result.content.split(chr(10)))}")

    return True


def test_empty_response():
    """Test empty response handling."""
    print("\n🧪 Test 4: Empty Response")
    print("-" * 60)

    result = parse_response([], provider='claude')

    assert not result.success, "Should fail on empty response"
    assert result.error_type == ErrorType.EMPTY, "Should categorize as EMPTY error"
    assert "empty" in result.error_message.lower(), "Should have clear error message"

    print(f"✅ Empty response handled correctly")
    print(f"   Error: {result.error_message}")

    return True


def test_timeout_scenario():
    """Test timeout error handling."""
    print("\n🧪 Test 5: Timeout Scenario")
    print("-" * 60)

    result = parse_response(
        [],
        provider='claude',
        timeout_occurred=True
    )

    assert not result.success, "Should fail on timeout"
    assert result.error_type == ErrorType.TIMEOUT, "Should categorize as TIMEOUT"

    print(f"✅ Timeout handled correctly")
    print(f"   Error: {result.error_message}")

    return True


def test_crash_scenario():
    """Test process crash handling."""
    print("\n🧪 Test 6: Process Crash")
    print("-" * 60)

    result = parse_response(
        ["partial output before crash"],
        provider='claude',
        process_alive=False
    )

    assert not result.success, "Should fail on crash"
    assert result.error_type == ErrorType.CRASH, "Should categorize as CRASH"
    assert result.raw_output, "Should preserve raw output for debugging"

    print(f"✅ Crash handled correctly")
    print(f"   Error: {result.error_message}")

    return True


def test_api_error_in_content():
    """Test detection of API errors in response."""
    print("\n🧪 Test 7: API Error in Content")
    print("-" * 60)

    output_with_error = [
        "> analyze this code",
        "Error: Rate limit exceeded. Please try again in 60 seconds.",
        "> _"
    ]

    result = parse_response(output_with_error, provider='claude')

    assert result.success, "Should be partial success (got content)"
    assert result.error_type == ErrorType.API_ERROR, "Should detect API error"
    assert "Rate limit" in result.content, "Should include error message in content"

    print(f"✅ API error detected (partial success)")
    print(f"   Content: {result.content}")
    print(f"   Error: {result.error_message}")

    return True


def test_ansi_stripping():
    """Test ANSI code removal."""
    print("\n🧪 Test 8: ANSI Code Stripping")
    print("-" * 60)

    output_with_ansi = [
        "\x1b[1mBold text\x1b[0m",
        "\x1b[31mRed text\x1b[0m",
        "\x1b[2J\x1b[HClear screen",
        "Normal text"
    ]

    parser = ResponseParser()
    cleaned = parser._strip_ansi(output_with_ansi)

    assert "\x1b" not in '\n'.join(cleaned), "Should remove all ANSI codes"
    assert "Bold text" in cleaned[0], "Should preserve text content"
    assert "Normal text" in cleaned[3], "Should preserve normal lines"

    # Count ANSI codes (outside f-string)
    before_count = len([l for l in output_with_ansi if '\x1b' in l])
    after_count = len([l for l in cleaned if '\x1b' in l])

    print(f"✅ ANSI stripping works correctly")
    print(f"   Before: {before_count} lines with ANSI")
    print(f"   After: {after_count} lines with ANSI")

    return True


def test_parser_stats():
    """Test parser statistics tracking."""
    print("\n🧪 Test 9: Parser Statistics")
    print("-" * 60)

    parser = ResponseParser()

    # Parse multiple responses (with more substantial content)
    parser.parse(["> test", "This is a real response line"], provider='claude')
    parser.parse([], provider='claude', timeout_occurred=True)
    parser.parse(['{"candidates": [{"content": {"parts": [{"text": "response"}]}}]}'], provider='gemini')

    stats = parser.get_stats()

    assert stats['total_parsed'] == 3, f"Should track total parses (got {stats['total_parsed']})"
    assert stats['successful'] == 2, f"Should count successes (got {stats['successful']})"
    assert stats['errors'] == 1, f"Should count errors (got {stats['errors']})"
    assert stats['avg_processing_ms'] > 0, "Should track processing time"

    print(f"✅ Statistics tracking works")
    print(f"   Total: {stats['total_parsed']}")
    print(f"   Success: {stats['successful']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Avg processing: {stats['avg_processing_ms']:.2f}ms")

    return True


def test_generic_fallback():
    """Test generic parser for unknown providers."""
    print("\n🧪 Test 10: Generic Fallback")
    print("-" * 60)

    unknown_output = [
        "Some AI Tool v2.0",
        "",
        "Here is my response:",
        "Line 1 of actual content",
        "Line 2 of actual content",
        "",
        "End of response"
    ]

    result = parse_response(unknown_output, provider='unknown_ai')

    assert result.success, "Should handle unknown provider"
    assert "Line 1" in result.content, "Should extract content"
    assert "Some AI Tool" not in result.content, "Should remove banner"

    print(f"✅ Generic fallback works")
    print(f"   Content: {result.content[:80]}...")

    return True


def run_all_tests():
    """Run all response parser tests."""
    print("🚀 Response Parser Test Suite")
    print("=" * 60)

    tests = [
        ("Claude Parsing", test_claude_parsing),
        ("Gemini JSON", test_gemini_json_parsing),
        ("Gemini Prose", test_gemini_prose_parsing),
        ("Empty Response", test_empty_response),
        ("Timeout", test_timeout_scenario),
        ("Crash", test_crash_scenario),
        ("API Error", test_api_error_in_content),
        ("ANSI Stripping", test_ansi_stripping),
        ("Statistics", test_parser_stats),
        ("Generic Fallback", test_generic_fallback),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} failed")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_name} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} error: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Total: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted")
        sys.exit(1)
