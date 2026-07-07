#!/usr/bin/env python3
"""
Dope-Memory MCP Stdio Adapter
Converts MCP JSON-RPC calls to Dope-Memory REST endpoints
"""

import json
import os
import sys
import requests
from typing import Any, Dict, Optional

DEFAULT_TOOLS_URL = "http://localhost:3020/tools"


class DopeMemoryMCPAdapter:
    """MCP stdio adapter for Dope-Memory REST service"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get("DOPE_MEMORY_TOOLS_URL", DEFAULT_TOOLS_URL)).rstrip("/")
        self.tools = {
            "memory_recap": self._memory_recap,
            "memory_search": self._memory_search,
            "memory_store": self._memory_store,
        }

    def _jsonrpc_error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    def _call_rest_endpoint(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Dope-Memory REST endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def _memory_recap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """memory_recap tool implementation"""
        workspace_id = params.get("workspace_id", "default")
        instance_id = params.get("instance_id", "A")
        scope = params.get("scope", "today")
        session_id = params.get("session_id")

        payload = {
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "scope": scope,
        }
        if session_id:
            payload["session_id"] = session_id

        return self._call_rest_endpoint("memory_recap", payload)

    def _memory_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """memory_search tool implementation"""
        workspace_id = params.get("workspace_id", "default")
        instance_id = params.get("instance_id", "A")
        query = params.get("query", "")
        top_k = params.get("top_k", 5)
        session_id = params.get("session_id")

        payload = {
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "query": query,
            "top_k": top_k,
        }
        if session_id:
            payload["session_id"] = session_id

        return self._call_rest_endpoint("memory_search", payload)

    def _memory_store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """memory_store tool implementation"""
        workspace_id = params.get("workspace_id", "default")
        instance_id = params.get("instance_id", "A")
        category = params.get("category", "manual")
        entry_type = params.get("entry_type", "note")
        summary = params.get("summary", "")
        details = params.get("details", "")
        session_id = params.get("session_id")

        payload = {
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "category": category,
            "entry_type": entry_type,
            "summary": summary,
            "details": details,
        }
        if session_id:
            payload["session_id"] = session_id

        return self._call_rest_endpoint("memory_store", payload)

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle MCP JSON-RPC request"""
        request_id = request.get("id")
        method = request.get("method")

        if not method:
            return self._jsonrpc_error(request_id, -32600, "Invalid Request: missing method")

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "dope-memory", "version": "1.0.0"},
                    },
                }
            if method == "notifications/initialized":
                return None
            if method == "tools/list":
                tool_list = [
                    {
                        "name": name,
                        "description": self._get_tool_description(name),
                        "inputSchema": self._get_tool_schema(name),
                    }
                    for name in self.tools
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tool_list},
                }
            if method == "tools/call":
                params = request.get("params") or {}
                if not isinstance(params, dict):
                    return self._jsonrpc_error(request_id, -32602, "Invalid params: params must be an object")

                tool_name = params.get("name")
                if not tool_name:
                    return self._jsonrpc_error(request_id, -32602, "Invalid params: missing tool name")

                arguments = params.get("arguments") or {}
                if not isinstance(arguments, dict):
                    return self._jsonrpc_error(request_id, -32602, "Invalid params: arguments must be an object")

                if tool_name not in self.tools:
                    return self._jsonrpc_error(request_id, -32601, f"Tool not found: {tool_name}")

                result = self.tools[tool_name](arguments)
                if result["success"]:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(result["data"])}],
                            "isError": False,
                        },
                    }
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": result["error"]}],
                        "isError": True,
                    },
                }

            return self._jsonrpc_error(request_id, -32601, f"Method not found: {method}")
        except Exception as e:
            return self._jsonrpc_error(request_id, -32603, f"Internal error: {str(e)}")

    def _get_tool_description(self, tool_name: str) -> str:
        """Get tool description"""
        descriptions = {
            "memory_recap": "Get a recap of recent work and memory entries",
            "memory_search": "Search memory entries by query",
            "memory_store": "Store a new memory entry",
        }
        return descriptions.get(tool_name, "Dope-Memory tool")

    def _get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get tool parameter schema"""
        schemas = {
            "memory_recap": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "Workspace ID"},
                    "instance_id": {"type": "string", "description": "Instance ID"},
                    "scope": {"type": "string", "description": "Time scope (today, session, etc.)", "default": "today"},
                    "session_id": {"type": "string", "description": "Optional session ID"},
                },
                "required": ["workspace_id", "instance_id"],
            },
            "memory_search": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "Workspace ID"},
                    "instance_id": {"type": "string", "description": "Instance ID"},
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Number of results", "default": 5},
                    "session_id": {"type": "string", "description": "Optional session ID"},
                },
                "required": ["workspace_id", "instance_id", "query"],
            },
            "memory_store": {
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "Workspace ID"},
                    "instance_id": {"type": "string", "description": "Instance ID"},
                    "category": {"type": "string", "description": "Entry category", "default": "manual"},
                    "entry_type": {"type": "string", "description": "Entry type", "default": "note"},
                    "summary": {"type": "string", "description": "Entry summary"},
                    "details": {"type": "string", "description": "Detailed content"},
                    "session_id": {"type": "string", "description": "Optional session ID"},
                },
                "required": ["workspace_id", "instance_id", "summary"],
            },
        }
        return schemas.get(tool_name, {"type": "object"})


def main():
    """Main stdio server loop"""
    adapter = DopeMemoryMCPAdapter()

    print("Dope-Memory MCP Adapter started", file=sys.stderr)
    print(f"Targeting REST tools at {adapter.base_url}", file=sys.stderr)
    print("Listening on stdin for MCP JSON-RPC requests...", file=sys.stderr)

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = adapter.handle_request(request)
                if response is not None:
                    print(json.dumps(response))
                    sys.stdout.flush()
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": f"Adapter error: {str(e)}"},
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("Shutting down...", file=sys.stderr)


if __name__ == "__main__":
    main()