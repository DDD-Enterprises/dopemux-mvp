#!/usr/bin/env python3
"""
Background daemon for Claude Code hook monitoring.

This script runs the monitoring loop in the background.
"""

import asyncio
import sys
import os

# Add the parent directory to Python path so we can import dopemux
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dopemux.hooks.claude_code_hooks import ClaudeCodeHooks

async def main():
    """Main monitoring loop."""
    hooks = ClaudeCodeHooks()

    # Configure watched paths from command line args if provided
    if len(sys.argv) > 1:
        hooks.watched_paths = [os.path.abspath(sys.argv[1])]
    else:
        # Default paths
        hooks.watched_paths = [
            os.getcwd(),
            os.path.expanduser('~/.claude'),
            os.path.expanduser('~/code')
        ]

    try:
        await hooks._monitor_activity()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Monitor daemon error: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())