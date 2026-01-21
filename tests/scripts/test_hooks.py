#!/usr/bin/env python3
"""
Quick test of Dopemux hook system.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dopemux.hooks.hook_manager import HookManager

async def test_hooks():
    """Test basic hook functionality."""
    manager = HookManager()

    print("🧪 Testing Hook Manager...")

    # Test hook status
    status = manager.get_hook_status()
    assert 'save' in status['hooks']
    assert status['quiet_mode'] == True
    print("✅ Hook status test passed")

    # Test hook enabling/disabling
    manager.disable_hook('save')
    assert not manager.is_hook_enabled('save')
    manager.enable_hook('save')
    assert manager.is_hook_enabled('save')
    print("✅ Hook toggle test passed")

    # Test hook triggering (should not block)
    await manager.trigger_hook('save', {'file': 'test.py', 'language': 'python'})
    print("✅ Hook trigger test passed")

    print("🎉 Hook system tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_hooks())