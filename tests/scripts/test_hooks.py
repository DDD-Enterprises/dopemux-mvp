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

    # Test hook triggering (should return status)
    result = await manager.trigger_hook('save', {'file': 'test.py', 'language': 'python'})
    assert result['status'] == 'scheduled'
    assert result['task'] == 'indexing'
    print("✅ Hook trigger save test passed")

    # Test terminal-open trigger
    result = await manager.trigger_hook('terminal-open', {'name': 'test-terminal'})
    assert result['status'] == 'scheduled'
    assert result['task'] == 'context_load'
    print("✅ Hook trigger terminal-open test passed")

    # Enable git-commit for testing
    manager.enable_hook('git-commit')

    # Test git-commit blocking validation
    # 1. Success case
    result = await manager.trigger_hook('git-commit', {
        'message': 'feat: support ADHD-optimized hooks',
        'blocking': True
    })
    assert result['status'] == 'success'
    print("✅ Hook trigger git-commit success test passed")

    # 2. Warning case (placeholder found)
    result = await manager.trigger_hook('git-commit', {
        'message': 'WIP: fix TODO later',
        'blocking': True
    })
    assert result['status'] == 'warning'
    assert result['reason'] == 'placeholder_found'
    print("✅ Hook trigger git-commit warning test passed")

    # 3. Failure case (empty message)
    result = await manager.trigger_hook('git-commit', {
        'message': '',
        'blocking': True
    })
    assert result['status'] == 'failed'
    print("✅ Hook trigger git-commit failure test passed")

    print("🎉 Hook system tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_hooks())