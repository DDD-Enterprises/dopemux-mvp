#!/usr/bin/env python3
"""
Serena MCP Server Wrapper

Serena provides LSP functionality, semantic code navigation, and project memory
with ADHD-optimized features for context preservation and intelligent guidance.

Key capabilities:
- Semantic code navigation
- Intelligent refactoring suggestions
- Project context understanding
- Session persistence across development
"""

import asyncio
import json
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict

# Add dopemux to path for event bus integration
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
    from dopemux.producers.mcp_producer import MCPEventProducer
    EVENTS_ENABLED = True
except ImportError:
    EVENTS_ENABLED = False
    logging.warning("Event bus integration not available - continuing without events")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("serena-wrapper")


class SerenaWrapper:
    """
    MCP Wrapper for Serena with ADHD-optimized code navigation and project memory.

    This wrapper provides:
    - Transparent stdio proxy to the underlying Serena LSP server
    - Event emission for code navigation and refactoring activities
    - ADHD-friendly context preservation and intelligent guidance
    - ConPort integration for session persistence
    - Progressive disclosure of complex refactoring operations
    """

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.event_bus: Optional[RedisStreamsAdapter] = None
        self.mcp_producer: Optional[MCPEventProducer] = None
        self.instance_id = os.getenv("DOPEMUX_INSTANCE", "default")
        self.workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

        # Code navigation state
        self.current_symbols = {}
        self.navigation_history = []
        self.refactoring_queue = []
        self.focus_context = None

        # ADHD configuration for code navigation
        self.adhd_config = {
            "max_search_results": int(os.getenv("MAX_SEARCH_RESULTS", "10")),
            "context_depth": int(os.getenv("CONTEXT_DEPTH", "3")),
            "progressive_disclosure": os.getenv("PROGRESSIVE_DISCLOSURE", "true").lower() == "true",
            "navigation_breadcrumbs": os.getenv("NAVIGATION_BREADCRUMBS", "true").lower() == "true",
            "intelligent_suggestions": os.getenv("INTELLIGENT_SUGGESTIONS", "true").lower() == "true",
            "gentle_guidance": os.getenv("GENTLE_GUIDANCE", "true").lower() == "true"
        }

        # Track method calls and navigation patterns
        self.pending_calls = {}
        self.navigation_stats = {
            "symbols_explored": 0,
            "refactorings_suggested": 0,
            "context_switches": 0,
            "session_duration": 0
        }
        self.session_start = datetime.now()

    async def initialize_event_bus(self):
        """Initialize connection to Redis event bus if available."""
        if not EVENTS_ENABLED:
            return

        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.event_bus = RedisStreamsAdapter(redis_url)
            await self.event_bus.connect()

            self.mcp_producer = MCPEventProducer(
                self.event_bus,
                self.instance_id
            )

            logger.info(f"Connected to event bus for instance {self.instance_id}")

        except Exception as e:
            logger.warning(f"Failed to connect to event bus: {e}")
            logger.info("Continuing without event emission")

    async def start_serena(self):
        """Start the underlying Serena LSP server."""
        try:
            # Determine how to launch Serena
            serena_command = os.getenv("SERENA_COMMAND", "serena")

            # Check different installation methods
            if os.getenv("USE_UVX", "true").lower() == "true":
                # Use uvx to run serena
                cmd = ["uvx", "serena", "--mcp-mode", "--workspace", self.workspace_id]
            elif os.getenv("USE_PIP_INSTALL", "false").lower() == "true":
                # Use globally installed serena
                cmd = ["serena", "--mcp-mode", "--workspace", self.workspace_id]
            else:
                # Use python module directly
                cmd = ["python", "-m", "serena", "--mcp-mode", "--workspace", self.workspace_id]

            # Add ADHD-specific configuration
            cmd.extend([
                "--max-results", str(self.adhd_config["max_search_results"]),
                "--context-depth", str(self.adhd_config["context_depth"]),
                "--instance-id", self.instance_id
            ])

            if self.adhd_config["progressive_disclosure"]:
                cmd.append("--progressive-disclosure")
            if self.adhd_config["navigation_breadcrumbs"]:
                cmd.append("--breadcrumbs")

            # Set up environment
            env = os.environ.copy()
            env["PYTHONPATH"] = ":".join([str(project_root), env.get("PYTHONPATH", "")])
            env["SERENA_WORKSPACE"] = self.workspace_id
            env["SERENA_INSTANCE"] = self.instance_id
            env["ADHD_MODE"] = "true"

            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=False  # Use binary mode for proper stdio handling
            )

            logger.info(f"Started Serena server with command: {' '.join(cmd)}")

        except FileNotFoundError as e:
            logger.error(f"Failed to start Serena: {e}")
            logger.error("Please install serena via: uvx install serena")
            logger.error("Or: pip install serena")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error starting Serena: {e}")
            sys.exit(1)

    async def emit_navigation_event(self, event_type: str, data: Dict[str, Any]):
        """Emit a navigation-related event to the event bus."""
        if not self.mcp_producer:
            return

        try:
            # Determine priority and cognitive load based on event type
            priority_map = {
                "focus_change": Priority.HIGH,
                "complex_refactor": Priority.HIGH,
                "navigation": Priority.MEDIUM,
                "symbol_found": Priority.LOW,
                "context_preserved": Priority.LOW
            }

            cognitive_load_map = {
                "focus_change": CognitiveLoad.HIGH,
                "complex_refactor": CognitiveLoad.HIGH,
                "navigation": CognitiveLoad.MEDIUM,
                "symbol_found": CognitiveLoad.LOW,
                "context_preserved": CognitiveLoad.LOW
            }

            priority = priority_map.get(event_type, Priority.MEDIUM)
            cognitive_load = cognitive_load_map.get(event_type, CognitiveLoad.MEDIUM)

            event = DopemuxEvent(
                event_type=f"serena.{event_type}",
                source=f"serena-{self.instance_id}",
                instance_id=self.instance_id,
                data=data,
                priority=priority,
                cognitive_load=cognitive_load,
                adhd_metadata=ADHDMetadata(
                    interruption_allowed=event_type not in ["focus_change", "complex_refactor"],
                    focus_required=event_type in ["focus_change", "complex_refactor"],
                    time_sensitive=event_type == "focus_change",
                    can_batch=event_type in ["symbol_found", "context_preserved"]
                )
            )

            await self.event_bus.publish(event)
            logger.debug(f"Emitted {event_type} navigation event")

        except Exception as e:
            logger.warning(f"Failed to emit event: {e}")

    async def handle_message(self, message: bytes) -> Optional[bytes]:
        """
        Process a message from Claude Code, analyze for navigation patterns,
        and forward to the Serena server.
        """
        try:
            # Try to parse as JSON-RPC
            try:
                msg_str = message.decode('utf-8')
                msg_json = json.loads(msg_str)

                # Track method calls for navigation analysis
                if msg_json.get("method") == "tools/call":
                    params = msg_json.get("params", {})
                    tool_name = params.get("name", "")

                    # Store pending call for response tracking
                    msg_id = msg_json.get("id")
                    if msg_id:
                        self.pending_calls[msg_id] = {
                            "tool": tool_name,
                            "params": params,
                            "start_time": datetime.now()
                        }

                    # Handle navigation-specific tools
                    if tool_name in self._get_navigation_tools():
                        await self._handle_navigation_tool(tool_name, params)

                    # Show ADHD-friendly guidance if enabled
                    if self.adhd_config["gentle_guidance"]:
                        guidance = self._generate_navigation_guidance(tool_name, params)
                        if guidance:
                            sys.stderr.write(f"\n{guidance}\n")
                            sys.stderr.flush()

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, just pass through
                pass

            # Forward to Serena
            if self.process and self.process.stdin:
                self.process.stdin.write(message)
                self.process.stdin.flush()

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_response(self, response: bytes) -> Optional[bytes]:
        """
        Process a response from Serena, analyze results and provide ADHD accommodations,
        and forward to Claude Code.
        """
        try:
            # Try to parse as JSON-RPC response
            try:
                resp_str = response.decode('utf-8')
                resp_json = json.loads(resp_str)

                # Check if this is a response to a tracked call
                msg_id = resp_json.get("id")
                if msg_id and msg_id in self.pending_calls:
                    call_info = self.pending_calls.pop(msg_id)
                    duration = (datetime.now() - call_info["start_time"]).total_seconds()

                    # Process navigation results with ADHD accommodations
                    if "result" in resp_json:
                        await self._process_navigation_result(
                            call_info["tool"],
                            resp_json["result"],
                            duration
                        )

                    # Update navigation statistics
                    self._update_navigation_stats(call_info["tool"])

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, just pass through
                pass

            # Forward to Claude Code
            sys.stdout.buffer.write(response)
            sys.stdout.buffer.flush()

        except Exception as e:
            logger.error(f"Error handling response: {e}")

    def _get_navigation_tools(self) -> List[str]:
        """Get list of navigation-specific tools that Serena provides."""
        return [
            "find_symbol",
            "goto_definition",
            "find_references",
            "suggest_refactor",
            "navigate_to",
            "search_code",
            "get_context",
            "save_session",
            "restore_session",
            "find_related",
            "analyze_dependencies",
            "get_call_hierarchy",
            "find_implementations"
        ]

    async def _handle_navigation_tool(self, tool_name: str, params: Dict[str, Any]):
        """Handle navigation-specific tool calls with ADHD accommodations."""
        if tool_name == "find_symbol":
            symbol_name = params.get("symbol", "")
            await self.emit_navigation_event("symbol_search", {
                "symbol": symbol_name,
                "workspace": self.workspace_id,
                "timestamp": datetime.now().isoformat()
            })

        elif tool_name == "goto_definition":
            # Track navigation patterns for ADHD context preservation
            location = params.get("location", {})
            self.navigation_history.append({
                "action": "goto_definition",
                "location": location,
                "timestamp": datetime.now().isoformat()
            })

            # Limit history for ADHD focus
            if len(self.navigation_history) > 10:
                self.navigation_history = self.navigation_history[-10:]

            await self.emit_navigation_event("navigation", {
                "action": "goto_definition",
                "location": location,
                "history_depth": len(self.navigation_history)
            })

        elif tool_name == "suggest_refactor":
            # ADHD: Break down complex refactorings
            refactor_type = params.get("type", "")
            complexity = params.get("complexity", "medium")

            if complexity in ["high", "complex"] and self.adhd_config["progressive_disclosure"]:
                sys.stderr.write("\n🔄 Complex refactoring detected - breaking into steps...\n")
                sys.stderr.flush()

            await self.emit_navigation_event("complex_refactor" if complexity == "high" else "refactor", {
                "type": refactor_type,
                "complexity": complexity,
                "timestamp": datetime.now().isoformat()
            })

        elif tool_name in ["save_session", "restore_session"]:
            # Critical for ADHD: session persistence
            await self.emit_navigation_event("context_preserved", {
                "action": tool_name,
                "workspace": self.workspace_id,
                "instance": self.instance_id,
                "timestamp": datetime.now().isoformat()
            })

    async def _process_navigation_result(self, tool_name: str, result: Any, duration: float):
        """Process and enhance navigation results with ADHD accommodations."""
        if tool_name == "find_symbol" and isinstance(result, dict):
            symbols = result.get("symbols", [])

            # ADHD: Limit and prioritize results
            if len(symbols) > self.adhd_config["max_search_results"]:
                if self.adhd_config["progressive_disclosure"]:
                    result["symbols"] = symbols[:self.adhd_config["max_search_results"]]
                    result["truncated"] = True
                    result["total_found"] = len(symbols)

                    sys.stderr.write(f"\n📋 Showing {self.adhd_config['max_search_results']} of {len(symbols)} symbols (use 'show more' for additional results)\n")
                    sys.stderr.flush()

            self.navigation_stats["symbols_explored"] += len(result.get("symbols", []))

        elif tool_name == "suggest_refactor" and isinstance(result, dict):
            suggestions = result.get("suggestions", [])

            # ADHD: Categorize and prioritize suggestions
            if suggestions and self.adhd_config["intelligent_suggestions"]:
                categorized = self._categorize_refactor_suggestions(suggestions)
                result["categorized"] = categorized

                # Show gentle guidance
                guidance = self._generate_refactor_guidance(categorized)
                if guidance:
                    sys.stderr.write(f"\n{guidance}\n")
                    sys.stderr.flush()

            self.navigation_stats["refactorings_suggested"] += len(suggestions)

        elif tool_name == "get_context" and isinstance(result, dict):
            # ADHD: Progressive context disclosure
            context = result.get("context", {})

            if self.adhd_config["context_depth"] and self.adhd_config["progressive_disclosure"]:
                # Limit context depth to prevent overwhelm
                limited_context = self._limit_context_depth(context, self.adhd_config["context_depth"])
                result["context"] = limited_context

                if context != limited_context:
                    result["context_limited"] = True
                    sys.stderr.write(f"\n🎯 Showing focused context (depth {self.adhd_config['context_depth']}) - use 'expand context' for more\n")
                    sys.stderr.flush()

        # Emit completion event
        await self.emit_navigation_event("tool_completed", {
            "tool": tool_name,
            "duration": duration,
            "result_size": len(str(result)) if result else 0,
            "timestamp": datetime.now().isoformat()
        })

    def _categorize_refactor_suggestions(self, suggestions: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize refactoring suggestions for ADHD-friendly presentation."""
        categories = {
            "quick_wins": [],      # Simple, low-risk changes
            "improvements": [],    # Medium complexity improvements
            "major_changes": []    # Complex refactorings requiring focus
        }

        for suggestion in suggestions:
            complexity = suggestion.get("complexity", "medium")
            risk = suggestion.get("risk", "medium")

            if complexity == "low" and risk == "low":
                categories["quick_wins"].append(suggestion)
            elif complexity == "high" or risk == "high":
                categories["major_changes"].append(suggestion)
            else:
                categories["improvements"].append(suggestion)

        return categories

    def _generate_refactor_guidance(self, categorized: Dict[str, List[Dict]]) -> str:
        """Generate ADHD-friendly refactoring guidance."""
        guidance = []

        if categorized["quick_wins"]:
            guidance.append(f"✨ {len(categorized['quick_wins'])} quick wins available (low risk)")

        if categorized["improvements"]:
            guidance.append(f"🔧 {len(categorized['improvements'])} improvements suggested")

        if categorized["major_changes"]:
            guidance.append(f"⚡ {len(categorized['major_changes'])} major changes (require focus time)")

        if guidance:
            return "💡 Refactoring suggestions:\n  " + "\n  ".join(guidance)
        return ""

    def _limit_context_depth(self, context: Dict[str, Any], max_depth: int) -> Dict[str, Any]:
        """Limit context depth to prevent ADHD overwhelm."""
        def limit_recursive(obj, depth):
            if depth <= 0:
                return "... (use 'expand context' for more)"

            if isinstance(obj, dict):
                return {k: limit_recursive(v, depth - 1) for k, v in obj.items()}
            elif isinstance(obj, list):
                if len(obj) > 5:  # Limit list length too
                    return [limit_recursive(item, depth - 1) for item in obj[:5]] + ["... (and more)"]
                return [limit_recursive(item, depth - 1) for item in obj]
            else:
                return obj

        return limit_recursive(context, max_depth)

    def _generate_navigation_guidance(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate ADHD-friendly navigation guidance."""
        guidance_map = {
            "find_symbol": f"🔍 Searching for symbol: {params.get('symbol', 'unknown')}...",
            "goto_definition": "🎯 Navigating to definition...",
            "find_references": f"📋 Finding references for: {params.get('symbol', 'unknown')}...",
            "suggest_refactor": "🔄 Analyzing refactoring opportunities...",
            "navigate_to": f"📍 Going to: {params.get('location', 'unknown')}...",
            "search_code": f"🔍 Searching code for: {params.get('query', 'unknown')}...",
            "get_context": "🧠 Loading context...",
            "save_session": "💾 Saving session state...",
            "restore_session": "📂 Restoring session state...",
        }

        return guidance_map.get(tool_name, f"⚡ Processing {tool_name}...")

    def _update_navigation_stats(self, tool_name: str):
        """Update navigation statistics for ADHD insights."""
        if tool_name in ["goto_definition", "navigate_to", "find_symbol"]:
            self.navigation_stats["context_switches"] += 1

        # Update session duration
        self.navigation_stats["session_duration"] = (
            datetime.now() - self.session_start
        ).total_seconds() / 60  # minutes

    async def run(self):
        """Main run loop for the wrapper."""
        # Initialize event bus
        await self.initialize_event_bus()

        # Start Serena server
        await self.start_serena()

        # Create tasks for reading from stdin and Serena
        tasks = []

        # Task to read from stdin and forward to Serena
        async def read_stdin():
            loop = asyncio.get_event_loop()
            while True:
                try:
                    # Read from stdin in non-blocking mode
                    message = await loop.run_in_executor(None, sys.stdin.buffer.read1, 8192)
                    if message:
                        await self.handle_message(message)
                    else:
                        # EOF reached
                        break
                except Exception as e:
                    logger.error(f"Error reading stdin: {e}")
                    break

        # Task to read from Serena and forward to stdout
        async def read_serena():
            loop = asyncio.get_event_loop()
            while self.process and self.process.stdout:
                try:
                    # Read from Serena in non-blocking mode
                    response = await loop.run_in_executor(None, self.process.stdout.read1, 8192)
                    if response:
                        await self.handle_response(response)
                    else:
                        # EOF reached
                        break
                except Exception as e:
                    logger.error(f"Error reading from Serena: {e}")
                    break

        # Start both tasks
        tasks.append(asyncio.create_task(read_stdin()))
        tasks.append(asyncio.create_task(read_serena()))

        # Also forward stderr
        async def read_stderr():
            loop = asyncio.get_event_loop()
            while self.process and self.process.stderr:
                try:
                    error = await loop.run_in_executor(None, self.process.stderr.read1, 8192)
                    if error:
                        sys.stderr.buffer.write(error)
                        sys.stderr.buffer.flush()
                    else:
                        break
                except Exception as e:
                    logger.error(f"Error reading stderr: {e}")
                    break

        tasks.append(asyncio.create_task(read_stderr()))

        # Wait for any task to complete (usually stdin EOF)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

        # Clean up
        if self.process:
            self.process.terminate()
            await asyncio.sleep(0.5)
            if self.process.poll() is None:
                self.process.kill()

        if self.event_bus:
            # Emit final session statistics
            await self.emit_navigation_event("session_ended", {
                "stats": self.navigation_stats,
                "timestamp": datetime.now().isoformat()
            })
            await self.event_bus.disconnect()

        logger.info(f"Serena wrapper shut down. Session stats: {self.navigation_stats}")


async def main():
    """Main entry point."""
    wrapper = SerenaWrapper()
    try:
        await wrapper.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())