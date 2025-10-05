#!/usr/bin/env python3
"""
MetaMCP Server: MCP-compatible interface for MetaMCP broker

This server provides an MCP-compatible interface that Claude Code can connect to,
while internally routing all tool calls through the MetaMCP role-aware broker.
It acts as a translation layer between the MCP protocol and the MetaMCP system.
"""

import asyncio
import json
import sys
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig, ToolCallRequest
from dopemux.mcp.roles import RoleManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetaMCPServer:
    """
    MCP-compatible server that provides role-aware tool access.

    This server implements the MCP protocol while internally routing
    all requests through the MetaMCP broker for intelligent tool management.
    """

    def __init__(self):
        self.broker: Optional[MetaMCPBroker] = None
        self.current_session_id = "claude-code-session"
        self.current_role = "developer"  # Default role
        self.available_tools = []

    async def initialize(self):
        """Initialize the MetaMCP broker"""
        try:
            # Configure broker
            config = BrokerConfig(
                name="claude-code-metamcp-server",
                version="1.0.0",
                broker_config_path="config/mcp/broker.yaml",
                policy_config_path="config/mcp/policy.yaml",
                role_based_mounting=True,
                budget_aware_hooks=True,
                adhd_optimizations=True,
                letta_integration=False
            )

            self.broker = MetaMCPBroker(config)
            await self.broker.start()

            # Set initial role
            await self.switch_role(self.current_role)

            logger.info("✅ MetaMCP Server initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize MetaMCP Server: {e}")
            return False

    async def switch_role(self, new_role: str) -> Dict[str, Any]:
        """Switch to a different role"""
        try:
            result = await self.broker.switch_role(self.current_session_id, new_role)

            if result.get('success'):
                self.current_role = new_role
                self.available_tools = result.get('mounted_tools', [])
                logger.info(f"🔄 Switched to role: {new_role} (tools: {self.available_tools})")
                return result
            else:
                logger.error(f"❌ Role switch failed: {result.get('error')}")
                return result

        except Exception as e:
            logger.error(f"❌ Role switch error: {e}")
            return {'success': False, 'error': str(e)}

    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        try:
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')

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
            logger.error(f"❌ Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get('id'),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "metamcp-server",
                    "version": "1.0.0",
                    "description": "Role-aware MCP tool broker with ADHD optimizations"
                }
            }
        }

    async def _handle_list_tools(self, request_id: str) -> Dict[str, Any]:
        """Handle tools/list request - returns tools for current role"""
        try:
            # Define tool schemas for the current role
            role_tools = self._get_role_tools()

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": role_tools
                }
            }

        except Exception as e:
            logger.error(f"❌ List tools error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to list tools: {str(e)}"
                }
            }

    def _get_role_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for the current role"""
        # Define common tool schemas that will be available through MetaMCP
        tool_schemas = {
            "switch_role": {
                "name": "switch_role",
                "description": "Switch to a different development role",
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
            "get_status": {
                "name": "get_status",
                "description": "Get current MetaMCP session status and role information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            "search_code": {
                "name": "search_code",
                "description": "Search through codebase (via claude-context)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "maxResults": {
                            "type": "integer",
                            "default": 3,
                            "description": "Maximum number of results"
                        }
                    },
                    "required": ["query"]
                }
            },
            "analyze_with_thinking": {
                "name": "analyze_with_thinking",
                "description": "Deep analysis using sequential thinking (available for architect/debugger roles)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Analysis query"
                        },
                        "maxDepth": {
                            "type": "integer",
                            "default": 5,
                            "description": "Maximum thinking depth"
                        }
                    },
                    "required": ["query"]
                }
            },
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information (via exa)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "numResults": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of results"
                        }
                    },
                    "required": ["query"]
                }
            },
            "manage_tasks": {
                "name": "manage_tasks",
                "description": "Manage tasks and project planning (via task-master-ai)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "create", "update", "complete"],
                            "description": "Action to perform"
                        },
                        "taskData": {
                            "type": "object",
                            "description": "Task data for create/update actions"
                        }
                    },
                    "required": ["action"]
                }
            }
        }

        # Return tools based on current role
        role_tool_mapping = {
            "developer": ["switch_role", "get_status", "search_code"],
            "researcher": ["switch_role", "get_status", "web_search"],
            "planner": ["switch_role", "get_status", "manage_tasks"],
            "reviewer": ["switch_role", "get_status", "search_code"],
            "ops": ["switch_role", "get_status"],
            "architect": ["switch_role", "get_status", "search_code", "analyze_with_thinking"],
            "debugger": ["switch_role", "get_status", "search_code", "analyze_with_thinking"]
        }

        available_tool_names = role_tool_mapping.get(self.current_role, ["switch_role", "get_status"])

        return [tool_schemas[tool_name] for tool_name in available_tool_names if tool_name in tool_schemas]

    async def _handle_tool_call(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        try:
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            # Handle MetaMCP-specific tools
            if tool_name == "switch_role":
                result = await self.switch_role(arguments.get('role'))
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Switched to role: {arguments.get('role')}\n\nAvailable tools: {result.get('mounted_tools', [])}\n\nToken budget: {result.get('budget_status', {}).get('total_budget', 'Unknown')} tokens"
                            }
                        ]
                    }
                }

            elif tool_name == "get_status":
                status = await self.broker.get_session_status(self.current_session_id)
                health = await self.broker.get_broker_health()

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"MetaMCP Status:\n\nCurrent Role: {self.current_role}\nAvailable Tools: {self.available_tools}\nSession: {status}\nBroker Health: {health.get('overall_status', 'unknown')}"
                            }
                        ]
                    }
                }

            # Route other tool calls through MetaMCP broker
            else:
                # Map tool names to actual MCP servers
                tool_mapping = {
                    "search_code": {"tool": "claude-context", "method": "search"},
                    "analyze_with_thinking": {"tool": "sequential-thinking", "method": "analyze"},
                    "web_search": {"tool": "exa", "method": "search"},
                    "manage_tasks": {"tool": "task-master-ai", "method": arguments.get('action', 'list')}
                }

                if tool_name in tool_mapping:
                    mapping = tool_mapping[tool_name]

                    # Create tool call request
                    tool_request = ToolCallRequest(
                        session_id=self.current_session_id,
                        tool_name=mapping["tool"],
                        method=mapping["method"],
                        args=arguments,
                        role=self.current_role
                    )

                    # Execute through broker
                    response = await self.broker.call_tool(tool_request)

                    if response.success:
                        # Format optimizations info
                        optimizations_text = ""
                        if response.optimizations:
                            savings = sum(opt.estimated_token_savings for opt in response.optimizations)
                            optimizations_text = f"\n\n🎯 Optimizations applied: {len(response.optimizations)} optimizations saved ~{savings} tokens"

                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"{json.dumps(response.result, indent=2)}{optimizations_text}"
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
                                "message": f"Tool call failed: {response.error}"
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
            logger.error(f"❌ Tool call error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool call failed: {str(e)}"
                }
            }

    async def _handle_role_switch(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metamcp/switch_role request"""
        role = params.get('role')
        result = await self.switch_role(role)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    async def _handle_get_status(self, request_id: str) -> Dict[str, Any]:
        """Handle metamcp/get_status request"""
        status = await self.broker.get_session_status(self.current_session_id)
        health = await self.broker.get_broker_health()

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "current_role": self.current_role,
                "available_tools": self.available_tools,
                "session_status": status,
                "broker_health": health
            }
        }

    async def run_stdio_server(self):
        """Run MCP server using stdio transport"""
        logger.info("🚀 Starting MetaMCP Server (stdio)")

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
                            "message": "Parse error"
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
    """Main entry point"""
    server = MetaMCPServer()
    return await server.run_stdio_server()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)