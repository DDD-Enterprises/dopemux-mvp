#!/usr/bin/env python3
"""
Integration test for session management slash commands.

This script tests the full integration of session commands to ensure they work
properly with Claude Code slash command system.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add the necessary paths
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from slash_commands import SlashCommandProcessor, format_for_claude_code
from session_formatter import SessionFormatter


def test_integration():
    """Test session commands integration."""
    print("🧪 Testing Session Management Integration")
    print("=" * 50)

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        processor = SlashCommandProcessor(temp_path)

        # Initialize the context manager
        try:
            processor.context_manager.initialize()
            print("✅ Context manager initialized")
        except Exception as e:
            print(f"❌ Context manager initialization failed: {e}")
            return False

        # Test 1: Save a session
        print("\n📝 Testing session save...")
        try:
            result = processor.process_command("save", [
                "--message", "Testing session management implementation",
                "--tag", "testing",
                "--tag", "feature"
            ])

            if result["success"]:
                session_id = result["session_id"]
                print(f"✅ Session saved successfully: {session_id[:8]}")
                print("📋 Formatted output:")
                formatted = format_for_claude_code(result)
                print(f"   {formatted[:100]}...")
            else:
                print(f"❌ Session save failed: {result['error']}")
                return False
        except Exception as e:
            print(f"❌ Session save error: {e}")
            return False

        # Test 2: List sessions
        print("\n📚 Testing session listing...")
        try:
            result = processor.process_command("sessions", ["--limit", "5"])

            if result["success"]:
                session_count = len(result["sessions"])
                print(f"✅ Found {session_count} sessions")
                if session_count > 0:
                    print("📋 Session gallery:")
                    formatted = format_for_claude_code(result)
                    print(f"   {formatted[:150]}...")
            else:
                print(f"❌ Session listing failed: {result['error']}")
                return False
        except Exception as e:
            print(f"❌ Session listing error: {e}")
            return False

        # Test 3: Session details
        print(f"\n🔍 Testing session details for {session_id[:8]}...")
        try:
            result = processor.process_command("session-details", [session_id[:8]])

            if result["success"]:
                print("✅ Session details retrieved successfully")
                print("📋 Details:")
                formatted = format_for_claude_code(result)
                print(f"   {formatted[:150]}...")
            else:
                print(f"❌ Session details failed: {result['error']}")
                return False
        except Exception as e:
            print(f"❌ Session details error: {e}")
            return False

        # Test 4: Restore preview
        print(f"\n🔄 Testing session restore preview...")
        try:
            result = processor.process_command("restore", [session_id[:8], "--preview"])

            if result["success"]:
                print("✅ Session restore preview generated")
                print("📋 Preview:")
                formatted = format_for_claude_code(result)
                print(f"   {formatted[:150]}...")
            else:
                print(f"❌ Session restore preview failed: {result['error']}")
                return False
        except Exception as e:
            print(f"❌ Session restore preview error: {e}")
            return False

        # Test 5: Search functionality
        print("\n🔍 Testing session search...")
        try:
            result = processor.process_command("sessions", ["--search", "testing"])

            if result["success"]:
                print("✅ Session search completed")
                search_count = len(result["sessions"])
                print(f"   Found {search_count} sessions matching 'testing'")
            else:
                print(f"❌ Session search failed: {result['error']}")
                return False
        except Exception as e:
            print(f"❌ Session search error: {e}")
            return False

        # Test 6: Smart tagging and descriptions
        print("\n🏷️  Testing smart tagging features...")
        try:
            # Create a context with specific patterns to test tagging
            context_manager = processor.context_manager
            from dopemux.adhd.context_manager import ContextSnapshot

            test_context = ContextSnapshot(
                message="implement new authentication feature",
                git_state={"status": "M  auth.py\nA  login.py"},
                open_files=[{"path": "src/auth.py"}, {"path": "tests/test_auth.py"}]
            )

            # Test smart description
            description = context_manager.generate_smart_description(test_context)
            print(f"✅ Smart description: '{description}'")

            # Test auto-tagging
            tags = context_manager.auto_tag_session(test_context)
            print(f"✅ Auto-generated tags: {tags}")

            # Test session type detection
            session_type = context_manager.detect_session_type(test_context)
            print(f"✅ Detected session type: '{session_type}'")

        except Exception as e:
            print(f"❌ Smart tagging error: {e}")
            return False

    print("\n" + "=" * 50)
    print("🎉 All integration tests passed successfully!")
    print("\n💡 Next steps:")
    print("   1. Test with actual Claude Code using: python slash_commands.py save")
    print("   2. Add to your shell-command-mcp configuration")
    print("   3. Use /save, /restore, /sessions in Claude Code!")
    return True


def test_formatter_features():
    """Test SessionFormatter features independently."""
    print("\n🎨 Testing SessionFormatter Features")
    print("-" * 40)

    formatter = SessionFormatter()

    # Test session card formatting
    test_session = {
        "id": "test123456",
        "timestamp": "2024-01-15T14:30:00",
        "current_goal": "Implement ADHD-friendly session management",
        "open_files": [{"path": "session.py"}, {"path": "formatter.py"}],
        "git_branch": "feature/sessions",
        "focus_duration": 35,
        "message": "Adding colorful UI for sessions"
    }

    try:
        # Test individual session card
        card = formatter._format_session_card(test_session)
        print("✅ Session card generated:")
        print(f"   {str(card)[:100]}...")

        # Test time grouping
        sessions = [test_session]
        grouped = formatter._group_sessions_by_time(sessions)
        print(f"✅ Time grouping: {list(grouped.keys())}")

        # Test session gallery
        gallery = formatter.format_session_gallery(sessions)
        print("✅ Session gallery generated")

        # Test relative time formatting
        relative_time = formatter._format_relative_time(test_session["timestamp"])
        print(f"✅ Relative time: '{relative_time}'")

        print("🎨 SessionFormatter tests completed!")
        return True

    except Exception as e:
        print(f"❌ SessionFormatter error: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Starting Dopemux Session Management Integration Tests")
    print("Created for ADHD developers - making development accessible! 🧠✨\n")

    success = True

    # Test core integration
    if not test_integration():
        success = False

    # Test formatter features
    if not test_formatter_features():
        success = False

    if success:
        print("\n🎊 All tests completed successfully!")
        print("Your ADHD-friendly session management system is ready to use! 🎯")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()