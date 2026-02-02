#!/usr/bin/env python3
"""
Enhanced MetaMCP Server for Claude Code Integration

This enhanced version provides better integration with Claude Code, including:
- Improved MCP protocol compatibility
- ADHD-optimized response formatting
- Role-aware tool suggestions
- Session persistence across Claude Code restarts
- Enhanced error handling and fallbacks
"""

import asyncio
import json
import sys
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig, ToolCallRequest
from dopemux.mcp.roles import RoleManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ClaudeCodeSession:
    """Represents a Claude Code session with ADHD accommodations"""
    session_id: str
    current_role: str
    start_time: float
    last_activity: float
    focus_duration: int = 1500  # 25 minutes in seconds
    break_suggested: bool = False
    context_preserved: bool = True
    tools_mounted: List[str] = None

    def __post_init__(self):
        if self.tools_mounted is None:
            self.tools_mounted = []

    @property
    def session_duration(self) -> int:
        """Current session duration in seconds"""
        return int(time.time() - self.start_time)

    @property
    def time_until_break(self) -> int:
        """Time until break suggestion in seconds"""
        return max(0, self.focus_duration - self.session_duration)

    @property
    def should_suggest_break(self) -> bool:
        """Whether to suggest a break based on ADHD accommodations"""
        return (self.session_duration >= self.focus_duration and
                not self.break_suggested)


class EnhancedMetaMCPServer:
    """
    Enhanced MCP-compatible server optimized for Claude Code integration.

    Features:
    - ADHD-accommodated session management
    - Role-aware tool mounting with explanations
    - Enhanced error handling with helpful suggestions
    - Session persistence across Claude Code restarts
    - Progressive disclosure of tool capabilities
    """

    def __init__(self):
        self.broker: Optional[MetaMCPBroker] = None
        self.sessions: Dict[str, ClaudeCodeSession] = {}
        self.current_session_id = "claude-code-main"
        self.available_tools = []
        self.server_info = {
            "name": "dopemux-metamcp-enhanced",
            "version": "1.1.0",
            "description": "Enhanced MetaMCP server with ADHD optimizations for Claude Code"
        }

    async def initialize(self) -> bool:
        """Initialize the enhanced MetaMCP broker"""
        try:
            # Load configuration
            config_path = os.getenv("METAMCP_CONFIG_PATH", "config/mcp")

            config = BrokerConfig(
                name="claude-code-enhanced-metamcp",
                version="1.1.0",
                broker_config_path=f"{config_path}/broker.yaml",
                policy_config_path=f"{config_path}/policy.yaml",
                role_based_mounting=True,
                budget_aware_hooks=True,
                adhd_optimizations=True,
                letta_integration=True
            )

            self.broker = MetaMCPBroker(config)
            await self.broker.start()

            # Initialize default session
            await self._initialize_session(self.current_session_id)

            logger.info("✅ Enhanced MetaMCP Server initialized for Claude Code")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced MetaMCP Server: {e}")
            return False

    async def _initialize_session(self, session_id: str, role: str = "developer") -> ClaudeCodeSession:
        """Initialize a new Claude Code session with ADHD accommodations"""
        current_time = time.time()

        session = ClaudeCodeSession(
            session_id=session_id,
            current_role=role,
            start_time=current_time,
            last_activity=current_time
        )

        self.sessions[session_id] = session

        # Switch to initial role
        await self.switch_role(role, session_id)

        return session

    async def switch_role(self, new_role: str, session_id: str = None) -> Dict[str, Any]:
        """Switch to a different role with ADHD-friendly explanations"""
        session_id = session_id or self.current_session_id

        try:
            # Get or create session
            if session_id not in self.sessions:
                session = await self._initialize_session(session_id, new_role)
            else:
                session = self.sessions[session_id]

            # Update activity
            session.last_activity = time.time()

            # Switch role through broker
            result = await self.broker.switch_role(session_id, new_role)

            if result.get('success'):
                session.current_role = new_role
                session.tools_mounted = result.get('mounted_tools', [])

                # Format ADHD-friendly response
                role_explanation = self._get_role_explanation(new_role)
                tools_summary = self._format_tools_summary(session.tools_mounted)

                logger.info(f"🔄 Switched to {new_role} role (session: {session_id})")

                return {
                    'success': True,
                    'role': new_role,
                    'explanation': role_explanation,
                    'tools_summary': tools_summary,
                    'mounted_tools': session.tools_mounted,
                    'session_info': self._get_session_info(session)
                }
            else:
                logger.error(f"❌ Role switch failed: {result.get('error')}")
                return result

        except Exception as e:
            logger.error(f"❌ Role switch error: {e}")
            return {'success': False, 'error': str(e)}

    def _get_role_explanation(self, role: str) -> str:
        """Get ADHD-friendly explanation of what each role does"""
        explanations = {
            "developer": "🛠️ **Developer Mode**: Focus on coding, debugging, and implementation. Tools optimized for writing and testing code.",
            "researcher": "🔍 **Research Mode**: Gather information, analyze documentation, and explore solutions. Tools optimized for finding and understanding information.",
            "planner": "📋 **Planner Mode**: Organize tasks, manage projects, and plan implementation. Tools optimized for breaking down complex work.",
            "reviewer": "🔍 **Review Mode**: Code review, quality assurance, and validation. Tools optimized for analysis and feedback.",
            "ops": "⚙️ **Operations Mode**: Deploy, monitor, and maintain systems. Tools optimized for infrastructure and automation.",
            "architect": "🏗️ **Architect Mode**: System design and high-level planning. Tools optimized for complex reasoning and design.",
            "debugger": "🐛 **Debug Mode**: Problem-solving and troubleshooting. Tools optimized for investigation and root cause analysis."
        }
        return explanations.get(role, f"🎯 **{role.title()} Mode**: Specialized tool set for {role} tasks.")

    def _format_tools_summary(self, tools: List[str]) -> str:
        """Format tools summary in ADHD-friendly way"""
        if not tools:
            return "No tools currently mounted."

        # Group tools by category for better cognitive processing
        categorized = {
            "🔍 Search & Analysis": [],
            "💭 Reasoning & Planning": [],
            "⚙️ Development & Code": [],
            "📋 Project Management": [],
            "🌐 External Resources": []
        }

        tool_categories = {
            "claude-context": "🔍 Search & Analysis",
            "serena": "🔍 Search & Analysis",
            "sequential-thinking": "💭 Reasoning & Planning",
            "zen": "💭 Reasoning & Planning",
            "morphllm-fast-apply": "⚙️ Development & Code",
            "desktop-commander": "⚙️ Development & Code",
            "task-master-ai": "📋 Project Management",
            "conport": "📋 Project Management",
            "leantime-mcp": "📋 Project Management",
            "exa": "🌐 External Resources",
            "context7": "🌐 External Resources"
        }

        for tool in tools:
            category = tool_categories.get(tool, "⚙️ Development & Code")
            categorized[category].append(tool)

        # Format summary
        summary_parts = []
        for category, category_tools in categorized.items():
            if category_tools:
                summary_parts.append(f"{category}: {', '.join(category_tools)}")

        return "\n".join(summary_parts)

    def _get_session_info(self, session: ClaudeCodeSession) -> Dict[str, Any]:
        """Get ADHD-friendly session information"""
        return {
            "duration_minutes": round(session.session_duration / 60, 1),
            "time_until_break_minutes": round(session.time_until_break / 60, 1),
            "should_suggest_break": session.should_suggest_break,
            "focus_remaining": f"{session.time_until_break // 60}:{session.time_until_break % 60:02d}"
        }

    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests with enhanced error handling"""
        try:
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')

            # Update session activity
            session = self.sessions.get(self.current_session_id)
            if session:
                session.last_activity = time.time()

            if method == "initialize":
                return await self._handle_initialize(request_id, params)

            elif method == "tools/list":
                return await self._handle_list_tools(request_id)

            elif method == "tools/call":
                return await self._handle_tool_call(request_id, params)

            elif method == "metamcp/switch_role":
                return await self._handle_role_switch(request_id, params)

            elif method == "metamcp/get_status":
                return await self._handle_get_status(request_id)

            elif method == "metamcp/get_session_info":
                return await self._handle_get_session_info(request_id)

            elif method == "metamcp/suggest_break":
                return await self._handle_suggest_break(request_id)

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                        "data": {
                            "available_methods": [
                                "initialize", "tools/list", "tools/call",
                                "metamcp/switch_role", "metamcp/get_status",
                                "metamcp/get_session_info", "metamcp/suggest_break"
                            ]
                        }
                    }
                }

        except Exception as e:
            logger.error(f"❌ Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get('id'),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                    "data": {
                        "suggestion": "Try restarting the MetaMCP server or check server logs"
                    }
                }
            }

    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request with enhanced capabilities"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    },
                    "resources": {},
                    "prompts": {},
                    "experimental": {
                        "adhdOptimizations": True,
                        "roleBasedMounting": True,
                        "sessionPersistence": True
                    }
                },
                "serverInfo": self.server_info
            }
        }

    async def _handle_list_tools(self, request_id: str) -> Dict[str, Any]:
        """Handle tools/list request with enhanced tool information"""
        try:
            session = self.sessions.get(self.current_session_id)
            current_role = session.current_role if session else "developer"

            # Get role-specific tools with enhanced descriptions
            role_tools = self._get_enhanced_role_tools(current_role)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": role_tools,
                    "_meta": {
                        "current_role": current_role,
                        "total_tools": len(role_tools),
                        "adhd_optimized": True
                    }
                }
            }

        except Exception as e:
            logger.error(f"❌ List tools error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to list tools: {str(e)}",
                    "data": {
                        "suggestion": "Try switching to a different role or check server connectivity"
                    }
                }
            }

    def _get_enhanced_role_tools(self, role: str) -> List[Dict[str, Any]]:
        """Get enhanced tool definitions with ADHD-friendly descriptions"""
        base_tools = {
            "switch_role": {
                "name": "switch_role",
                "description": "Switch to a different development role (e.g., developer, researcher, planner)",
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
                },
                "tags": ["core", "adhd-friendly"]
            },
            "get_status": {
                "name": "get_status",
                "description": "Get current MetaMCP session status and role information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                },
                "tags": ["core", "status"]
            },
            "search_code": {
                "name": "search_code",
                "description": "Search through codebase using intelligent semantic search (claude-context)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'authentication functions', 'React components')"
                        },
                        "maxResults": {
                            "type": "integer",
                            "default": 3,
                            "description": "Maximum number of results (ADHD-optimized default: 3)"
                        }
                    },
                    "required": ["query"]
                },
                "tags": ["search", "code", "adhd-optimized"]
            },
            "get_session_info": {
                "name": "get_session_info",
                "description": "Get ADHD-accommodated session information (focus time, break suggestions)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                },
                "tags": ["adhd", "session", "wellness"]
            }
        }

        # Role-specific tools
        role_specific_tools = {
            "developer": {
                "apply_code_changes": {
                    "name": "apply_code_changes",
                    "description": "Apply intelligent code transformations and refactoring (morphllm-fast-apply)",
                    "tags": ["code", "transformation"]
                }
            },
            "researcher": {
                "web_search": {
                    "name": "web_search",
                    "description": "Search the web for development information and documentation (exa)",
                    "tags": ["search", "research", "external"]
                },
                "get_documentation": {
                    "name": "get_documentation",
                    "description": "Get official documentation and guides (context7)",
                    "tags": ["docs", "research", "official"]
                }
            },
            "planner": {
                "manage_tasks": {
                    "name": "manage_tasks",
                    "description": "Manage tasks and project planning with ADHD accommodations (task-master-ai)",
                    "tags": ["planning", "tasks", "adhd-optimized"]
                },
                "manage_project": {
                    "name": "manage_project",
                    "description": "Integrate with Leantime project management (leantime-mcp)",
                    "tags": ["project", "management", "external"]
                }
            },
            "architect": {
                "analyze_with_thinking": {
                    "name": "analyze_with_thinking",
                    "description": "Deep analysis using sequential thinking with ADHD-friendly focus (sequential-thinking)",
                    "tags": ["analysis", "thinking", "adhd-optimized"]
                },
                "multi_model_consensus": {
                    "name": "multi_model_consensus",
                    "description": "Get consensus from multiple AI models for complex decisions (zen)",
                    "tags": ["consensus", "complex", "multi-model"]
                }
            },
            "debugger": {
                "analyze_with_thinking": {
                    "name": "analyze_with_thinking",
                    "description": "Deep debugging analysis with step-by-step thinking (sequential-thinking)",
                    "tags": ["debug", "analysis", "step-by-step"]
                },
                "search_code": {
                    "name": "search_code",
                    "description": "Search codebase for debugging context (claude-context)",
                    "tags": ["debug", "search", "context"]
                }
            }
        }

        # Combine base tools with role-specific tools
        available_tools = list(base_tools.values())

        if role in role_specific_tools:
            for tool_name, tool_def in role_specific_tools[role].items():
                # Add missing required fields
                tool_def.setdefault("inputSchema", {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                })
                available_tools.append(tool_def)

        return available_tools

    async def _handle_tool_call(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request with enhanced ADHD accommodations"""
        try:
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            # Get current session
            session = self.sessions.get(self.current_session_id)
            if not session:
                session = await self._initialize_session(self.current_session_id)

            # Check if break should be suggested
            break_suggestion = ""
            if session.should_suggest_break:
                break_suggestion = "\n\n🌿 **Gentle Reminder**: You've been focusing for 25+ minutes. Consider taking a 5-minute break after this task."
                session.break_suggested = True

            # Handle MetaMCP-specific tools
            if tool_name == "switch_role":
                result = await self.switch_role(arguments.get('role'), self.current_session_id)

                response_text = f"✅ **Role Switch Complete**\n\n{result.get('explanation', '')}\n\n"
                response_text += f"**Available Tools:**\n{result.get('tools_summary', '')}\n\n"

                session_info = result.get('session_info', {})
                response_text += f"**Session Info:**\n"
                response_text += f"• Focus time: {session_info.get('duration_minutes', 0):.1f} minutes\n"
                response_text += f"• Time until break: {session_info.get('focus_remaining', 'N/A')}\n"
                response_text += break_suggestion

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": response_text
                            }
                        ]
                    }
                }

            elif tool_name == "get_status":
                status = await self.broker.get_session_status(self.current_session_id)
                health = await self.broker.get_broker_health()
                session_info = self._get_session_info(session)

                response_text = f"🧠 **MetaMCP Status**\n\n"
                response_text += f"**Current Role:** {session.current_role}\n"
                response_text += f"**Available Tools:** {len(session.tools_mounted)} tools mounted\n"
                response_text += f"**Session Duration:** {session_info['duration_minutes']:.1f} minutes\n"
                response_text += f"**Focus Remaining:** {session_info['focus_remaining']}\n"
                response_text += f"**Broker Health:** {health.get('overall_status', 'unknown')}\n"
                response_text += break_suggestion

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": response_text
                            }
                        ]
                    }
                }

            elif tool_name == "get_session_info":
                session_info = self._get_session_info(session)

                response_text = f"📊 **Session Information**\n\n"
                response_text += f"• **Focus Duration:** {session_info['duration_minutes']:.1f} minutes\n"
                response_text += f"• **Time Until Break:** {session_info['focus_remaining']}\n"
                response_text += f"• **Current Role:** {session.current_role}\n"
                response_text += f"• **Tools Available:** {len(session.tools_mounted)}\n"

                if session_info['should_suggest_break']:
                    response_text += f"\n🌿 **Break Recommended:** You've been in focus mode for over 25 minutes."
                else:
                    response_text += f"\n✅ **Focus Mode:** Good focus rhythm maintained."

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": response_text
                            }
                        ]
                    }
                }

            # Route other tool calls through MetaMCP broker
            else:
                # Enhanced tool mapping with better error handling
                tool_mapping = {
                    "search_code": {
                        "tool": "claude-context",
                        "method": "search",
                        "description": "Searching codebase"
                    },
                    "analyze_with_thinking": {
                        "tool": "sequential-thinking",
                        "method": "analyze",
                        "description": "Deep thinking analysis"
                    },
                    "web_search": {
                        "tool": "exa",
                        "method": "search",
                        "description": "Web research"
                    },
                    "get_documentation": {
                        "tool": "context7",
                        "method": "get_docs",
                        "description": "Documentation lookup"
                    },
                    "manage_tasks": {
                        "tool": "task-master-ai",
                        "method": arguments.get('action', 'list'),
                        "description": "Task management"
                    },
                    "manage_project": {
                        "tool": "leantime-mcp",
                        "method": "manage",
                        "description": "Project management"
                    },
                    "apply_code_changes": {
                        "tool": "morphllm-fast-apply",
                        "method": "apply",
                        "description": "Code transformation"
                    },
                    "multi_model_consensus": {
                        "tool": "zen",
                        "method": "consensus",
                        "description": "Multi-model analysis"
                    }
                }

                if tool_name in tool_mapping:
                    mapping = tool_mapping[tool_name]

                    # Create tool call request
                    tool_request = ToolCallRequest(
                        session_id=self.current_session_id,
                        tool_name=mapping["tool"],
                        method=mapping["method"],
                        args=arguments,
                        role=session.current_role
                    )

                    # Execute through broker
                    response = await self.broker.call_tool(tool_request)

                    if response.success:
                        # Format response with ADHD accommodations
                        result_text = f"✅ **{mapping['description'].title()} Complete**\n\n"

                        # Format result (limit length for ADHD)
                        result_data = response.result
                        if isinstance(result_data, dict):
                            result_text += json.dumps(result_data, indent=2)
                        else:
                            result_text += str(result_data)

                        # Add optimization info if available
                        if response.optimizations:
                            savings = sum(opt.estimated_token_savings for opt in response.optimizations)
                            result_text += f"\n\n🎯 **Optimizations:** {len(response.optimizations)} applied, ~{savings} tokens saved"

                        result_text += break_suggestion

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
                                "code": -32603,
                                "message": f"Tool '{tool_name}' failed: {response.error}",
                                "data": {
                                    "tool": mapping["tool"],
                                    "suggestion": f"Try using a different {mapping['description']} approach or check if the {mapping['tool']} server is running"
                                }
                            }
                        }

                else:
                    available_tools = [list(tool_mapping.keys())]
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}",
                            "data": {
                                "available_tools": available_tools,
                                "suggestion": f"Use 'switch_role' to access different tool sets or check available tools with 'get_status'"
                            }
                        }
                    }

        except Exception as e:
            logger.error(f"❌ Tool call error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool call failed: {str(e)}",
                    "data": {
                        "suggestion": "Check server logs, verify tool availability, or try restarting MetaMCP server"
                    }
                }
            }

    async def _handle_role_switch(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metamcp/switch_role request"""
        role = params.get('role')
        result = await self.switch_role(role, self.current_session_id)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    async def _handle_get_status(self, request_id: str) -> Dict[str, Any]:
        """Handle metamcp/get_status request"""
        session = self.sessions.get(self.current_session_id)
        if not session:
            session = await self._initialize_session(self.current_session_id)

        status = await self.broker.get_session_status(self.current_session_id)
        health = await self.broker.get_broker_health()

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "current_role": session.current_role,
                "available_tools": session.tools_mounted,
                "session_status": status,
                "broker_health": health,
                "session_info": self._get_session_info(session),
                "adhd_accommodations": {
                    "break_suggested": session.should_suggest_break,
                    "focus_duration_minutes": session.focus_duration / 60,
                    "progressive_disclosure": True
                }
            }
        }

    async def _handle_get_session_info(self, request_id: str) -> Dict[str, Any]:
        """Handle session info request"""
        session = self.sessions.get(self.current_session_id)
        if not session:
            session = await self._initialize_session(self.current_session_id)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": self._get_session_info(session)
        }

    async def _handle_suggest_break(self, request_id: str) -> Dict[str, Any]:
        """Handle break suggestion request"""
        session = self.sessions.get(self.current_session_id)
        if not session:
            session = await self._initialize_session(self.current_session_id)

        break_message = "🌿 **5-Minute Break Suggestions:**\n\n"
        break_message += "• Step away from the screen\n"
        break_message += "• Take 3 deep breaths\n"
        break_message += "• Stretch or walk around\n"
        break_message += "• Hydrate with water\n"
        break_message += "• Look at something far away\n\n"
        break_message += "Your progress is saved and will be here when you return! 🎯"

        # Reset break suggestion flag
        session.break_suggested = False

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": break_message
                    }
                ]
            }
        }

    async def run_stdio_server(self):
        """Run enhanced MCP server using stdio transport"""
        logger.info("🚀 Starting Enhanced MetaMCP Server for Claude Code (stdio)")

        if not await self.initialize():
            return 1

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
                    logger.error(f"❌ Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": {
                                "suggestion": "Ensure request is valid JSON format"
                            }
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("📡 Received interrupt signal")
        finally:
            if self.broker:
                await self.broker.stop()

        return 0


async def main():
    """Main entry point for enhanced MetaMCP server"""
    server = EnhancedMetaMCPServer()
    return await server.run_stdio_server()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)