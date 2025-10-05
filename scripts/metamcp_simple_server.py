#!/usr/bin/env python3
"""
Simplified MetaMCP Server for Claude Code integration

This is a simplified version that provides role-aware tool access without
requiring the full MetaMCP broker infrastructure to be running. It demonstrates
the concept and can be enhanced later.

Enhanced with ADHD attention-aware tool selection.
"""

import asyncio
import json
import sys
import logging
import aiohttp
from typing import Dict, List, Any, Optional

# ADHD accommodations: Simple, user-controlled approach
# Note: Complex AttentionManager disabled after analysis showed it increases cognitive load
# Focusing on user agency and simplicity instead of algorithmic attention detection
ATTENTION_MANAGER_AVAILABLE = False  # Intentionally disabled for simpler approach

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce log noise for Claude Code
logger = logging.getLogger(__name__)


class SimpleMetaMCPServer:
    """
    Simplified MCP-compatible server for demonstrating role-aware tool access.
    """

    def __init__(self):
        self.current_role = "developer"  # Default role
        self.session_info = {
            "session_id": "claude-code-session",
            "role": self.current_role,
            "token_budget": 10000,
            "tokens_used": 0
        }
        # Simple ADHD accommodation: User-controlled tool limiting
        self.tool_profile = "standard"  # minimal/standard/full
        self.tool_limits = {
            "minimal": 3,     # For overwhelmed/scattered days
            "standard": 5,    # Normal working mode
            "full": None      # Power user mode, no limit
        }

        # Docker MCP server endpoints
        self.mcp_servers = {
            "zen": "http://localhost:3003",
            "context7": "http://localhost:3002",
            "exa": "http://localhost:3008"
        }

        # Session bookmarking for context preservation
        self.session_bookmarks = {}
        self.current_bookmark = None

        # HTTP session for MCP server connections
        self.http_session = None

        # ADHD Finishing Helpers - "There is NOW and there is NEVER"
        self.active_projects = {}  # Track almost-done work
        self.completion_reminders = {}  # Visual field reminders

        # Gentle timer for break reminders
        from datetime import datetime
        self.session_start_time = datetime.now()
        self.last_break_reminder = None

    def add_helpful_visual_indicators(self, tool: Dict[str, Any]) -> str:
        """Add helpful visual indicators that ADHD developers actually want"""
        name = tool.get("name", "").lower()

        # Helpful categorization with visual cues (emojis are good for ADHD!)
        if name in ["switch_role", "get_metamcp_status", "bookmark_session", "restore_session", "list_bookmarks"]:
            return "🟢 Quick"  # Fast, immediate tools
        elif name in ["track_almost_done", "finish_line_check", "mark_completed"]:
            return "🎯 Finish"  # Completion helpers - critical for ADHD!
        elif name in ["search_code", "web_search", "get_docs", "run_command", "manage_tasks"]:
            return "🟡 Standard"  # Normal work tools
        elif name in ["analyze_architecture", "debug_analysis", "review_session", "design_patterns"]:
            return "🟠 Focused"  # Requires sustained attention
        else:
            return "🔴 Deep"  # Complex, long tasks

    def check_break_reminder(self) -> Optional[str]:
        """Check if it's time for a gentle break reminder"""
        from datetime import datetime, timedelta

        now = datetime.now()
        session_minutes = (now - self.session_start_time).total_seconds() / 60

        # Simple Pomodoro: remind every 25 minutes
        if session_minutes > 25 and (session_minutes % 25) < 1:
            # Only remind once per 25-minute cycle
            if self.last_break_reminder is None or (now - self.last_break_reminder).total_seconds() > 1200:  # 20 min cooldown
                self.last_break_reminder = now
                return "🍅 25 minutes completed! Consider taking a short break to recharge."

        return None

    def get_role_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for the current role with attention-aware filtering"""

        # Base tools available to all roles
        base_tools = [
            {
                "name": "switch_role",
                "description": f"Switch to a different development role (current: {self.current_role})",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["developer", "researcher", "planner", "reviewer", "ops", "architect", "debugger"],
                            "description": "The role to switch to"
                        }
                    },
                    "required": ["role"]
                }
            },
            {
                "name": "get_metamcp_status",
                "description": "Get current MetaMCP session status and available tools",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "set_tool_profile",
                "description": "Change tool complexity profile for ADHD accommodation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "string",
                            "enum": ["minimal", "standard", "full"],
                            "description": "Tool profile: minimal (3 tools), standard (5 tools), full (all tools)"
                        }
                    },
                    "required": ["profile"]
                }
            },
            {
                "name": "bookmark_session",
                "description": "Save current working context for easy resumption",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name for this bookmark (e.g., 'debugging-auth', 'feature-review')"
                        },
                        "note": {
                            "type": "string",
                            "description": "Optional note about what you were working on"
                        },
                        "current_file": {
                            "type": "string",
                            "description": "File you're currently working in (optional)"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "restore_session",
                "description": "Restore a previously bookmarked working context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the bookmark to restore"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "list_bookmarks",
                "description": "Show all saved session bookmarks",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "track_almost_done",
                "description": "Track project that's almost finished - make it visible!",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Project name (e.g., 'auth-bug-fix', 'user-dashboard')"
                        },
                        "progress": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Completion percentage (1-100)"
                        },
                        "next_step": {
                            "type": "string",
                            "description": "Specific next action to finish it"
                        },
                        "deadline": {
                            "type": "string",
                            "description": "When this needs to be done (optional)"
                        }
                    },
                    "required": ["project", "progress", "next_step"]
                }
            },
            {
                "name": "finish_line_check",
                "description": "Show all almost-done projects - visual reminder!",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "mark_completed",
                "description": "Celebrate! Mark project as DONE",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Project name to mark complete"
                        }
                    },
                    "required": ["project"]
                }
            }
        ]

        # Role-specific tools
        role_specific_tools = {
            "developer": [
                {
                    "name": "search_code",
                    "description": "Search through codebase (simulated claude-context)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "maxResults": {"type": "integer", "default": 3, "description": "Maximum number of results"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "run_command",
                    "description": "Execute development commands (simulated CLI tool)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"}
                        },
                        "required": ["command"]
                    }
                }
            ],
            "researcher": [
                {
                    "name": "web_search",
                    "description": "Search the web for information (simulated exa)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "numResults": {"type": "integer", "default": 10, "description": "Number of results"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_docs",
                    "description": "Get official documentation (simulated context7)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Documentation topic"}
                        },
                        "required": ["topic"]
                    }
                }
            ],
            "planner": [
                {
                    "name": "manage_tasks",
                    "description": "Manage tasks and project planning (simulated task-master-ai)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["list", "create", "update", "complete"], "description": "Action to perform"},
                            "task": {"type": "string", "description": "Task description (for create/update)"}
                        },
                        "required": ["action"]
                    }
                }
            ],
            "reviewer": [
                {
                    "name": "search_code",
                    "description": "Search through codebase for review (simulated claude-context)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "maxResults": {"type": "integer", "default": 3, "description": "Maximum number of results"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "review_session",
                    "description": "Start a code review session (simulated conport)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "files": {"type": "array", "items": {"type": "string"}, "description": "Files to review"}
                        },
                        "required": ["files"]
                    }
                }
            ],
            "architect": [
                {
                    "name": "analyze_architecture",
                    "description": "Deep architectural analysis (simulated zen + sequential-thinking)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Architecture question"},
                            "depth": {"type": "string", "enum": ["shallow", "medium", "deep"], "default": "medium"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "design_patterns",
                    "description": "Suggest design patterns and architecture",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "context": {"type": "string", "description": "Design context"}
                        },
                        "required": ["context"]
                    }
                }
            ],
            "debugger": [
                {
                    "name": "debug_analysis",
                    "description": "Debug complex issues (simulated zen + sequential-thinking)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "issue": {"type": "string", "description": "Issue description"},
                            "logs": {"type": "string", "description": "Log data (optional)"}
                        },
                        "required": ["issue"]
                    }
                },
                {
                    "name": "search_code",
                    "description": "Search codebase for debugging",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            ],
            "ops": [
                {
                    "name": "run_command",
                    "description": "Execute operational commands",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"}
                        },
                        "required": ["command"]
                    }
                },
                {
                    "name": "deployment_status",
                    "description": "Check deployment and system status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "environment": {"type": "string", "description": "Environment to check"}
                        }
                    }
                }
            ]
        }

        # Combine base tools with role-specific tools
        tools = base_tools.copy()
        if self.current_role in role_specific_tools:
            tools.extend(role_specific_tools[self.current_role])

        # Apply simple ADHD accommodation: User-controlled tool limiting
        tool_limit = self.tool_limits.get(self.tool_profile)

        if tool_limit and len(tools) > tool_limit:
            # Simple prioritization: base tools first, then role-specific
            prioritized_tools = []

            # Always include base tools (they're essential)
            prioritized_tools.extend(base_tools)

            # Add role-specific tools up to the limit
            remaining_slots = tool_limit - len(base_tools)
            if remaining_slots > 0 and self.current_role in role_specific_tools:
                role_tools = role_specific_tools[self.current_role][:remaining_slots]
                prioritized_tools.extend(role_tools)

            tools = prioritized_tools

        # Add helpful visual indicators (emojis are good for ADHD!)
        for tool in tools:
            visual_indicator = self.add_helpful_visual_indicators(tool)
            tool["description"] = f"{visual_indicator} {tool['description']}"

        logger.info(f"Applied tool profile '{self.tool_profile}': {len(tools)} tools available")
        return tools

    async def call_mcp_server(self, server_name: str, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to containerized MCP server"""
        if server_name not in self.mcp_servers:
            return {"error": f"Unknown MCP server: {server_name}"}

        if not self.http_session:
            self.http_session = aiohttp.ClientSession()

        url = self.mcp_servers[server_name]
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }

        try:
            async with self.http_session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status} from {server_name}"}
        except Exception as e:
            return {"error": f"Failed to call {server_name}: {str(e)}"}

    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')

            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "metamcp-server",
                            "version": "1.0.0",
                            "description": "Role-aware MCP tool broker with ADHD optimizations (simplified)"
                        }
                    }
                }

            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.get_role_tools()
                    }
                }

            elif method == "tools/call":
                return await self.handle_tool_call(request_id, params)

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get('id'),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def handle_tool_call(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        try:
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            # Update token usage
            self.session_info["tokens_used"] += 50  # Simulate token usage

            if tool_name == "switch_role":
                new_role = arguments.get('role')
                if new_role in ["developer", "researcher", "planner", "reviewer", "ops", "architect", "debugger"]:
                    old_role = self.current_role
                    self.current_role = new_role
                    self.session_info["role"] = new_role

                    # Get new role's tools
                    new_tools = self.get_role_tools()
                    tool_names = [tool['name'] for tool in new_tools]

                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"🔄 **Role switched from {old_role} to {new_role}**\n\n**Available tools:**\n" +
                                           "\n".join(f"• {name}" for name in tool_names) +
                                           f"\n\n**Token budget:** {self.session_info['token_budget'] - self.session_info['tokens_used']} remaining of {self.session_info['token_budget']}\n\n**ADHD Optimizations:** ✅ Active (context preservation, gentle notifications, break reminders)"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Invalid role: {new_role}"
                        }
                    }

            elif tool_name == "get_metamcp_status":
                available_tools = [tool['name'] for tool in self.get_role_tools()]
                tool_limit = self.tool_limits.get(self.tool_profile, "No limit")

                # Check for gentle break reminder
                break_reminder = self.check_break_reminder()

                # Calculate session time
                from datetime import datetime
                session_minutes = int((datetime.now() - self.session_start_time).total_seconds() / 60)

                status_text = f"**MetaMCP Status**\n\n" +\
                             f"**Current Role:** {self.current_role}\n" +\
                             f"**Tool Profile:** {self.tool_profile.title()} ({tool_limit} tools max)\n" +\
                             f"**Available Tools:** {len(available_tools)} tools\n" +\
                             f"**Session Time:** {session_minutes} minutes\n" +\
                             f"**Token Usage:** {self.session_info['tokens_used']}/{self.session_info['token_budget']} ({(self.session_info['tokens_used']/self.session_info['token_budget']*100):.1f}%)\n"

                # Add current bookmark if available
                if self.current_bookmark:
                    status_text += f"**Current Bookmark:** {self.current_bookmark} ⭐\n"

                status_text += f"\n**ADHD Accommodations:**\n" +\
                              f"✓ User-controlled tool limiting\n" +\
                              f"✓ Session bookmarking\n" +\
                              f"✓ Simple, clear descriptions\n" +\
                              f"✓ Gentle break reminders\n"

                # Add break reminder if it's time
                if break_reminder:
                    status_text += f"\n**{break_reminder}**\n"

                # CRITICAL: Show almost-done projects in status (visual field reminder!)
                if self.active_projects:
                    urgent_projects = [name for name, details in self.active_projects.items() if details['progress'] >= 75]
                    if urgent_projects:
                        status_text += f"\n**🔥 FINISH LINE ALERT - DON'T LET THESE SLIP AWAY!**\n"
                        for project in urgent_projects[:2]:  # Show top 2 most urgent
                            details = self.active_projects[project]
                            progress_bar = "█" * (details['progress'] // 10) + "░" * (10 - details['progress'] // 10)
                            status_text += f"   • **{project}**: {details['progress']}% [{progress_bar}] - {details['next_step'][:50]}...\n"
                        if len(urgent_projects) > 2:
                            status_text += f"   • +{len(urgent_projects) - 2} more almost-done projects\n"
                        status_text += f"\n💡 **ADHD Reminder:** There is NOW and NEVER - make these NOW!\n"

                status_text += f"\n*Use `set_tool_profile` to change complexity | `finish_line_check` for all almost-done work*"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": status_text
                            }
                        ]
                    }
                }

            elif tool_name == "set_tool_profile":
                new_profile = arguments.get('profile')
                if new_profile in self.tool_limits:
                    old_profile = self.tool_profile
                    self.tool_profile = new_profile

                    # Get updated tool count
                    updated_tools = self.get_role_tools()
                    tool_limit = self.tool_limits.get(new_profile, "No limit")

                    profile_descriptions = {
                        "minimal": "Perfect for overwhelmed days - just the essentials",
                        "standard": "Balanced mode for normal work sessions",
                        "full": "Power user mode with access to all tools"
                    }

                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**🎯 Tool Profile Updated**\n\n" +
                                           f"**Changed from:** {old_profile.title()} → **{new_profile.title()}**\n" +
                                           f"**Description:** {profile_descriptions[new_profile]}\n" +
                                           f"**Tool Limit:** {tool_limit if tool_limit else 'No limit'}\n" +
                                           f"**Available Tools:** {len(updated_tools)} tools\n\n" +
                                           f"*Your tool selection will refresh on the next request.*"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Invalid profile: {new_profile}. Choose: minimal, standard, or full"
                        }
                    }

            elif tool_name == "bookmark_session":
                bookmark_name = arguments.get('name')
                note = arguments.get('note', '')
                current_file = arguments.get('current_file', '')

                from datetime import datetime
                bookmark = {
                    "name": bookmark_name,
                    "timestamp": datetime.now().isoformat(),
                    "note": note,
                    "current_file": current_file,
                    "role": self.current_role,
                    "tool_profile": self.tool_profile,
                    "session_info": self.session_info.copy()
                }

                self.session_bookmarks[bookmark_name] = bookmark
                self.current_bookmark = bookmark_name

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**📌 Session Bookmarked**\n\n" +
                                       f"**Name:** {bookmark_name}\n" +
                                       f"**Time:** {datetime.now().strftime('%H:%M')}\n" +
                                       f"**Role:** {self.current_role.title()}\n" +
                                       f"**Profile:** {self.tool_profile.title()}\n" +
                                       (f"**File:** {current_file}\n" if current_file else "") +
                                       (f"**Note:** {note}\n" if note else "") +
                                       f"\n*Use `restore_session` to resume this context later.*"
                            }
                        ]
                    }
                }

            elif tool_name == "restore_session":
                bookmark_name = arguments.get('name')

                if bookmark_name not in self.session_bookmarks:
                    available = list(self.session_bookmarks.keys())
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Bookmark '{bookmark_name}' not found. Available: {', '.join(available) if available else 'None'}"
                        }
                    }

                bookmark = self.session_bookmarks[bookmark_name]

                # Restore context
                self.current_role = bookmark['role']
                self.tool_profile = bookmark['tool_profile']
                self.current_bookmark = bookmark_name

                from datetime import datetime
                saved_time = datetime.fromisoformat(bookmark['timestamp'])
                time_ago = datetime.now() - saved_time
                hours_ago = int(time_ago.total_seconds() // 3600)
                mins_ago = int((time_ago.total_seconds() % 3600) // 60)

                time_str = ""
                if hours_ago > 0:
                    time_str = f"{hours_ago}h {mins_ago}m ago"
                else:
                    time_str = f"{mins_ago}m ago"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**🔄 Session Restored**\n\n" +
                                       f"**Name:** {bookmark['name']}\n" +
                                       f"**Saved:** {time_str}\n" +
                                       f"**Role:** {bookmark['role'].title()}\n" +
                                       f"**Profile:** {bookmark['tool_profile'].title()}\n" +
                                       (f"**File:** {bookmark['current_file']}\n" if bookmark.get('current_file') else "") +
                                       (f"**Note:** {bookmark['note']}\n" if bookmark.get('note') else "") +
                                       f"\n*Your context has been restored. Ready to continue where you left off!*"
                            }
                        ]
                    }
                }

            elif tool_name == "list_bookmarks":
                if not self.session_bookmarks:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "**📌 Session Bookmarks**\n\n*No bookmarks saved yet.*\n\nUse `bookmark_session` to save your current working context."
                                }
                            ]
                        }
                    }

                from datetime import datetime
                bookmark_list = "**📌 Session Bookmarks**\n\n"

                for name, bookmark in self.session_bookmarks.items():
                    saved_time = datetime.fromisoformat(bookmark['timestamp'])
                    time_ago = datetime.now() - saved_time
                    hours_ago = int(time_ago.total_seconds() // 3600)
                    mins_ago = int((time_ago.total_seconds() % 3600) // 60)

                    time_str = f"{hours_ago}h {mins_ago}m ago" if hours_ago > 0 else f"{mins_ago}m ago"

                    current_marker = " ⭐" if name == self.current_bookmark else ""

                    bookmark_list += f"**{name}**{current_marker}\n"
                    bookmark_list += f"   • Saved: {time_str}\n"
                    bookmark_list += f"   • Role: {bookmark['role'].title()}\n"
                    if bookmark.get('current_file'):
                        bookmark_list += f"   • File: {bookmark['current_file']}\n"
                    if bookmark.get('note'):
                        bookmark_list += f"   • Note: {bookmark['note']}\n"
                    bookmark_list += f"\n"

                bookmark_list += f"*Use `restore_session <name>` to resume any context.*"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": bookmark_list
                            }
                        ]
                    }
                }

            elif tool_name == "track_almost_done":
                project = arguments.get('project')
                progress = arguments.get('progress')
                next_step = arguments.get('next_step')
                deadline = arguments.get('deadline', '')

                from datetime import datetime

                # Track the almost-done project
                self.active_projects[project] = {
                    "progress": progress,
                    "next_step": next_step,
                    "deadline": deadline,
                    "last_updated": datetime.now().isoformat(),
                    "created": datetime.now().isoformat()
                }

                # Create visual urgency based on progress
                urgency_emoji = "🔥" if progress >= 90 else "⚡" if progress >= 75 else "🎯"
                progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**{urgency_emoji} Almost Done Project Tracked!**\n\n" +
                                       f"**Project:** {project}\n" +
                                       f"**Progress:** {progress}% [{progress_bar}]\n" +
                                       f"**Next Step:** {next_step}\n" +
                                       (f"**Deadline:** {deadline}\n" if deadline else "") +
                                       f"**Added:** Just now\n\n" +
                                       f"🎯 **This is now in your visual field!**\n" +
                                       f"*Use `finish_line_check` to see all almost-done work*\n\n" +
                                       f"💡 **ADHD Tip:** In ADHD there is NOW and NEVER - let's make this NOW!"
                            }
                        ]
                    }
                }

            elif tool_name == "finish_line_check":
                if not self.active_projects:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "**🎯 Finish Line Check**\n\n" +
                                           "✨ **No almost-done projects tracked!**\n\n" +
                                           "This is actually great - either everything's complete or nothing's been started yet.\n\n" +
                                           "*Use `track_almost_done` when you have projects close to finishing.*"
                                }
                            ]
                        }
                    }

                from datetime import datetime

                # Sort by urgency (highest progress first, then by deadline)
                sorted_projects = sorted(
                    self.active_projects.items(),
                    key=lambda x: (-x[1]['progress'], x[1].get('deadline', 'zzz'))
                )

                finish_line_text = "**🎯 FINISH LINE CHECK - Visual Field Reminder**\n\n"
                finish_line_text += "**🔥 ALMOST DONE PROJECTS (Don't let these slip away!):**\n\n"

                for project, details in sorted_projects:
                    progress = details['progress']
                    progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)

                    # Visual urgency
                    if progress >= 95:
                        urgency = "🔥🔥🔥 SO CLOSE!"
                    elif progress >= 85:
                        urgency = "🔥🔥 ALMOST THERE!"
                    elif progress >= 75:
                        urgency = "⚡ PUSH THROUGH!"
                    else:
                        urgency = "🎯 Keep going"

                    # Time since last update
                    last_updated = datetime.fromisoformat(details['last_updated'])
                    hours_since = (datetime.now() - last_updated).total_seconds() / 3600

                    time_warning = ""
                    if hours_since > 24:
                        time_warning = f" ⚠️ {int(hours_since // 24)}d ago!"
                    elif hours_since > 8:
                        time_warning = f" ⚠️ {int(hours_since)}h ago!"

                    finish_line_text += f"**{project}** {urgency}{time_warning}\n"
                    finish_line_text += f"   Progress: {progress}% [{progress_bar}]\n"
                    finish_line_text += f"   Next: {details['next_step']}\n"
                    if details.get('deadline'):
                        finish_line_text += f"   Deadline: {details['deadline']}\n"
                    finish_line_text += f"\n"

                finish_line_text += f"**💡 ADHD Reality Check:**\n"
                finish_line_text += f"• There is NOW and there is NEVER\n"
                finish_line_text += f"• Out of sight = Out of mind (that's why this exists!)\n"
                finish_line_text += f"• Finishing is harder than starting for ADHD brains\n\n"
                finish_line_text += f"*Pick ONE project above and do the next step RIGHT NOW*"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": finish_line_text
                            }
                        ]
                    }
                }

            elif tool_name == "mark_completed":
                project = arguments.get('project')

                if project not in self.active_projects:
                    available_projects = list(self.active_projects.keys())
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Project '{project}' not found. Available: {', '.join(available_projects) if available_projects else 'None'}"
                        }
                    }

                # Remove from active projects and celebrate!
                completed_project = self.active_projects.pop(project)
                progress = completed_project['progress']

                celebration = "🎉🎉🎉" if progress >= 90 else "🎉🎉" if progress >= 75 else "🎉"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"**{celebration} PROJECT COMPLETED! {celebration}**\n\n" +
                                       f"**🏆 {project.upper()} IS DONE!**\n\n" +
                                       f"**Final Progress:** {progress}% ➜ 100% ✅\n" +
                                       f"**You did it!** You crossed the finish line!\n\n" +
                                       f"🧠 **ADHD Victory:**\n" +
                                       f"• You overcame the 'finishing is hard' challenge\n" +
                                       f"• You proved there CAN be completion, not just 'never'\n" +
                                       f"• This deserves real celebration!\n\n" +
                                       f"🎯 **Take a moment to appreciate this win** - your ADHD brain needs positive reinforcement for completion!"
                            }
                        ]
                    }
                }

            # Simulate other tool calls
            elif tool_name in ["search_code", "web_search", "run_command", "manage_tasks", "analyze_architecture", "debug_analysis", "get_docs", "review_session", "design_patterns", "deployment_status"]:

                # Simulate different responses based on tool
                if tool_name == "search_code":
                    query = arguments.get('query', 'unknown')
                    result_text = f"🔍 **Code Search Results for '{query}'**\n\n*[Simulated results - in production this would use claude-context]*\n\nFound 3 matches:\n• src/main.py:42 - function definition\n• tests/test_main.py:18 - usage example\n• docs/api.md:12 - documentation\n\n💰 **Token optimization:** Limited to 3 results (saved ~500 tokens)"

                elif tool_name == "web_search":
                    query = arguments.get('query', 'unknown')
                    result_text = f"🌐 **Web Search Results for '{query}'**\n\n*[Simulated results - in production this would use exa]*\n\nTop 5 results:\n• Official documentation\n• Best practices guide\n• Stack Overflow discussion\n• GitHub repository\n• Tutorial article\n\n💰 **Token optimization:** Summaries only (saved ~1000 tokens)"

                elif tool_name == "analyze_architecture":
                    query = arguments.get('query', 'unknown')
                    depth = arguments.get('depth', 'medium')
                    result_text = f"🏗️ **Architecture Analysis for '{query}' (depth: {depth})**\n\n*[Simulated results - in production this would use zen + sequential-thinking]*\n\nKey insights:\n• Modular design recommended\n• Consider dependency injection\n• Implement proper error boundaries\n• Use event-driven patterns\n\n💰 **Token optimization:** {depth} depth analysis (saved ~2000 tokens vs deep)"

                elif tool_name == "manage_tasks":
                    action = arguments.get('action', 'list')
                    result_text = f"📋 **Task Management - {action.title()}**\n\n*[Simulated results - in production this would use task-master-ai]*\n\nCurrent tasks:\n• Implement authentication\n• Write unit tests\n• Update documentation\n• Deploy to staging\n\n💰 **Token optimization:** Limited to 50 tasks (saved ~300 tokens)"

                else:
                    result_text = f"**{tool_name.replace('_', ' ').title()}**\n\n*[Simulated tool response - MetaMCP would route this to the appropriate MCP server]*\n\nRequest: {json.dumps(arguments, indent=2)}\n\n💰 **Token optimization:** Budget-aware query optimization applied"

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
                    }
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool call failed: {str(e)}"
                }
            }

    async def run_stdio_server(self):
        """Run MCP server using stdio transport"""
        try:
            while True:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = await self.handle_mcp_request(request)

                    # Write response to stdout
                    print(json.dumps(response))
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()

        except KeyboardInterrupt:
            pass

        return 0


async def main():
    """Main entry point"""
    server = SimpleMetaMCPServer()
    return await server.run_stdio_server()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)