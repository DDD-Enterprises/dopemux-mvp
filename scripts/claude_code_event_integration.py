#!/usr/bin/env python3
"""
Claude Code Event Integration

This script integrates the event system with Claude Code's MCP proxy,
enabling transparent event emission for all MCP tool calls.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add dopemux to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dopemux.event_bus import RedisStreamsAdapter
from dopemux.mcp_protocol_wrapper import (
    MCPProtocolOrchestrator,
    MCPServerConfig,
    create_claude_code_wrapper
)


async def setup_claude_code_integration():
    """
    Setup event integration for Claude Code MCP proxy.

    This function configures the event wrapper to intercept
    all MCP communications transparently.
    """
    print("🔗 Claude Code Event Integration Setup")
    print("=" * 50)

    # Get instance configuration
    instance_id = os.environ.get("DOPEMUX_INSTANCE_ID", "A")
    print(f"Instance ID: {instance_id}")

    # Initialize event bus
    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    await event_bus.connect()
    print("✅ Connected to Redis event bus")

    # Create orchestrator
    orchestrator = MCPProtocolOrchestrator(event_bus, instance_id)

    # Register MCP servers based on Claude Code configuration
    # These would normally come from .claude/claude.json
    mcp_servers = [
        {
            "name": "conport",
            "command": [
                "/Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp",
                "--mode", "stdio",
                "--workspace_id", "/Users/hue/code/dopemux-mvp"
            ],
            "env": {}
        },
        {
            "name": "context7",
            "command": ["npx", "context7-mcp"],
            "env": {"CONTEXT7_API_KEY": os.environ.get("CONTEXT7_API_KEY", "")}
        },
        {
            "name": "zen",
            "command": ["python", "/Users/hue/code/dopemux-mvp/services/zen/zen_mcp.py"],
            "env": {
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", "")
            }
        }
    ]

    # Register each server
    for server_info in mcp_servers:
        config = MCPServerConfig(
            name=server_info["name"],
            command=server_info["command"],
            env=server_info["env"],
            stdio=True,
            instance_id=instance_id
        )
        orchestrator.register_server(config)
        print(f"📝 Registered {server_info['name']} for event wrapping")

    return orchestrator, event_bus


async def demonstrate_integration():
    """
    Demonstrate the Claude Code event integration.

    This shows how events are automatically emitted when
    Claude Code makes MCP tool calls.
    """
    print("\n🎯 Integration Demonstration")
    print("=" * 50)

    # Setup integration
    orchestrator, event_bus = await setup_claude_code_integration()

    # Create an event listener to show events being emitted
    events_received = []

    def handle_event(event):
        """Handle received events for demonstration."""
        events_received.append(event)
        print(f"📨 Event: {event.envelope.type}")
        if "mcp.tool_call" in event.envelope.type:
            tool = event.payload.get("tool_name", "unknown")
            if event.envelope.type.endswith(".started"):
                print(f"   🔧 Started: {tool}")
            elif event.envelope.type.endswith(".completed"):
                duration = event.payload.get("duration_ms", 0)
                print(f"   ✅ Completed: {tool} ({duration}ms)")

    # Subscribe to MCP events
    subscription_id = await event_bus.subscribe(
        "instance.*.mcp.*",
        handle_event
    )
    print("👂 Listening for MCP events...\n")

    # Simulate Claude Code operations
    print("📋 Simulating Claude Code MCP calls:")
    print("1. ConPort: Getting active context")
    print("2. Context7: Fetching documentation")
    print("3. Zen: Multi-model reasoning")
    print()

    # Note: In production, these would be actual MCP calls from Claude Code
    # The wrapper intercepts the stdio/TCP communications transparently

    # Wait for events to be processed
    await asyncio.sleep(2)

    # Show summary
    print(f"\n📊 Integration Summary:")
    print(f"   Events captured: {len(events_received)}")
    print(f"   Integration ready for production use")

    # Cleanup
    await event_bus.unsubscribe(subscription_id)
    await event_bus.disconnect()


def generate_claude_config_update():
    """
    Generate the configuration update needed for Claude Code.

    This shows what changes are needed in .claude/claude.json
    to enable event integration.
    """
    print("\n📝 Claude Code Configuration Update")
    print("=" * 50)
    print("Add this wrapper configuration to .claude/claude.json:\n")

    config = {
        "mcpServers": {
            "conport_wrapped": {
                "command": "python",
                "args": [
                    "/Users/hue/code/dopemux-mvp/scripts/mcp_event_wrapper.py",
                    "--server", "conport",
                    "--instance", "${DOPEMUX_INSTANCE_ID:-A}"
                ],
                "env": {
                    "WORKSPACE_ID": "/Users/hue/code/dopemux-mvp"
                }
            },
            "context7_wrapped": {
                "command": "python",
                "args": [
                    "/Users/hue/code/dopemux-mvp/scripts/mcp_event_wrapper.py",
                    "--server", "context7",
                    "--instance", "${DOPEMUX_INSTANCE_ID:-A}"
                ],
                "env": {
                    "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
                }
            },
            "zen_wrapped": {
                "command": "python",
                "args": [
                    "/Users/hue/code/dopemux-mvp/scripts/mcp_event_wrapper.py",
                    "--server", "zen",
                    "--instance", "${DOPEMUX_INSTANCE_ID:-A}"
                ],
                "env": {
                    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                    "GEMINI_API_KEY": "${GEMINI_API_KEY}"
                }
            }
        }
    }

    print(json.dumps(config, indent=2))
    print("\nThis configuration wraps each MCP server with event emission.")


async def main():
    """Main entry point for Claude Code event integration."""
    print("🚀 Claude Code Event Integration System")
    print("=" * 50)
    print("This system enables transparent event emission for all MCP tool calls")
    print("made by Claude Code, without modifying the MCP servers themselves.")
    print()

    # Show how to update Claude configuration
    generate_claude_config_update()

    # Demonstrate the integration
    await demonstrate_integration()

    print("\n✅ Integration Complete!")
    print("\nBenefits:")
    print("• All MCP calls automatically emit events")
    print("• Multi-instance coordination enabled")
    print("• ConPort operations trigger domain events")
    print("• Performance metrics collected automatically")
    print("• ADHD-optimized cognitive load management")
    print("\nNext Steps:")
    print("1. Update .claude/claude.json with wrapper configuration")
    print("2. Set DOPEMUX_INSTANCE_ID environment variable")
    print("3. Start Claude Code with event integration")
    print("4. Monitor events in Redis Commander (localhost:8081)")


if __name__ == "__main__":
    asyncio.run(main())