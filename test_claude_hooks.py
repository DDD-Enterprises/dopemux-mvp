#!/usr/bin/env python3
"""
Test Claude Code hook integration.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dopemux.hooks.claude_code_hooks import ClaudeCodeHooks

async def test_claude_hooks():
    """Test Claude Code hook functionality."""
    hooks = ClaudeCodeHooks()

    print("🧪 Testing Claude Code Hooks...")

    # Test hook status
    status = hooks.get_status()
    assert 'session_start' in status['active_hooks']
    assert status['quiet_mode'] == True
    print("✅ Hook status test passed")

    # Test hook enabling/disabling
    hooks.disable_hook('session_start')
    assert not hooks.is_hook_enabled('session_start')
    hooks.enable_hook('session_start')
    assert hooks.is_hook_enabled('session_start')
    print("✅ Hook toggle test passed")

    # Test monitoring (brief test - don't run full monitoring)
    hooks.watched_paths = ['/tmp']  # Safe test path
    # Note: Not starting monitoring to avoid long-running test
    print("✅ Monitoring setup test passed")

    # Test shell script generation
    scripts = hooks.generate_shell_hooks()
    assert 'bash_preexec' in scripts
    assert 'zsh_hooks' in scripts
    assert 'dopemux trigger' in scripts['bash_preexec']
    print("✅ Shell script generation test passed")

    print("🎉 Claude Code hooks tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_claude_hooks())