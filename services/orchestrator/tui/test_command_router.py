#!/usr/bin/env python3
"""
Test script for CommandRouter

Validates CLI detection and basic execution functionality.
Run from project root: python services/orchestrator/tui/test_command_router.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.orchestrator.tui.command_router import CommandRouter


async def test_cli_detection():
    """Test automatic CLI detection."""
    print("=" * 60)
    print("TEST 1: CLI Detection")
    print("=" * 60)

    router = CommandRouter()
    print(router.get_cli_status_report())
    print()

    available_ais = router.get_available_ais()
    print(f"Available AIs: {available_ais if available_ais else 'None'}")
    print()


async def test_command_execution():
    """Test command execution (only if CLIs are available)."""
    print("=" * 60)
    print("TEST 2: Command Execution")
    print("=" * 60)

    router = CommandRouter()

    # Test with a simple echo command (simulating AI response)
    test_command = "echo 'Test response from AI'"

    # Find first available AI
    available = router.get_available_ais()
    if not available:
        print("❌ No AI CLIs available to test execution")
        print("   Install claude, gemini-cli, or grok-cli to test")
        return

    ai = available[0]
    print(f"Testing with {ai} CLI...")

    output_lines = []

    def on_output(line: str):
        output_lines.append(line)
        print(f"  OUTPUT: {line}")

    def on_error(line: str):
        print(f"  ERROR: {line}")

    try:
        return_code, final_output = await router.execute_command(
            ai=ai,
            command="--version",  # Safe command for all CLIs
            output_callback=on_output,
            error_callback=on_error,
            timeout=10
        )

        print(f"\nReturn code: {return_code}")
        print(f"✅ Execution test {'passed' if return_code == 0 else 'failed'}")

    except asyncio.TimeoutError:
        print("⏰ Command timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()


async def test_unavailable_ai():
    """Test behavior with unavailable AI."""
    print("=" * 60)
    print("TEST 3: Unavailable AI Handling")
    print("=" * 60)

    router = CommandRouter()

    try:
        await router.execute_command(
            ai="fake-ai",
            command="test",
            timeout=1
        )
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CommandRouter Test Suite")
    print("=" * 60 + "\n")

    await test_cli_detection()
    await test_command_execution()
    await test_unavailable_ai()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
