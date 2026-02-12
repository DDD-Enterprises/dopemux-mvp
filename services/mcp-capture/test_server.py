#!/usr/bin/env python3
"""
Quick test for MCP Capture Server functionality.

Tests the core emit_capture_event() integration without full MCP protocol.
"""

import sys
from pathlib import Path

# Add dopemux to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from dopemux.memory.capture_client import emit_capture_event, CaptureError


def test_emit():
    """Test basic event emission."""
    event = {
        "event_type": "mcp-test:capture:emit",
        "session_id": "test-session-001",
        "payload": {
            "test": True,
            "source": "mcp-capture-server-test",
        },
    }

    try:
        result = emit_capture_event(event, mode="mcp")
        print(f"✓ Event emitted successfully")
        print(f"  event_id: {result.event_id[:16]}...")
        print(f"  inserted: {result.inserted}")
        print(f"  mode: {result.mode}")
        print(f"  event_type: {result.event_type}")
        print(f"  ledger_path: {result.ledger_path}")
        return True
    except CaptureError as e:
        print(f"✗ Capture error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_deduplication():
    """Test content-addressed deduplication."""
    event = {
        "event_type": "mcp-test:dedup",
        "session_id": "dedup-test-001",
        "payload": {"value": 123},
    }

    # First emission
    result1 = emit_capture_event(event, mode="mcp")
    print(f"\n✓ First emission: inserted={result1.inserted}, event_id={result1.event_id[:16]}...")

    # Second emission (should be deduplicated)
    result2 = emit_capture_event(event, mode="mcp")
    print(f"✓ Second emission: inserted={result2.inserted}, event_id={result2.event_id[:16]}...")

    # Verify same event_id
    if result1.event_id == result2.event_id:
        print(f"✓ Event IDs match (content-addressed deduplication works)")
        if result1.inserted and not result2.inserted:
            print(f"✓ Deduplication successful (first inserted, second skipped)")
            return True
        else:
            print(f"⚠ Unexpected insertion pattern")
            return False
    else:
        print(f"✗ Event IDs don't match!")
        return False


if __name__ == "__main__":
    print("Testing MCP Capture Server functionality...\n")
    print("=" * 60)
    print("Test 1: Basic Event Emission")
    print("=" * 60)
    test1 = test_emit()

    print("\n" + "=" * 60)
    print("Test 2: Content-Addressed Deduplication")
    print("=" * 60)
    test2 = test_deduplication()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
