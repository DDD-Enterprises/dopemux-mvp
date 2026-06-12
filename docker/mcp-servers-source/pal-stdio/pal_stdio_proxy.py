#!/usr/bin/env python3
"""
PAL Stdio Proxy for Docker MCP Toolkit.
Bridges stdio JSON-RPC <-> PAL HTTP/SSE endpoint.
"""
import asyncio
import json
import os
import sys
import httpx
from typing import Any

PAL_URL = os.getenv("PAL_HTTP_URL", "http://host.docker.internal:3003")

class PalStdioProxy:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)
        self.session_id = None
        
    async def handle_message(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        method = msg.get("method")
        msg_id = msg.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "prompts": {"listChanged": False}
                    },
                    "serverInfo": {"name": "pal", "version": "1.0.0"}
                }
            }
        
        if method == "tools/list":
            # Fetch from PAL HTTP endpoint
            try:
                # PAL uses SSE; for now return known tools
                tools = [
                    {"name": "thinkdeep", "description": "Deep multi-model analysis", "inputSchema": {"type": "object"}},
                    {"name": "planner", "description": "Interactive planning", "inputSchema": {"type": "object"}},
                    {"name": "consensus", "description": "Multi-model consensus", "inputSchema": {"type": "object"}},
                    {"name": "debug", "description": "Debug investigation", "inputSchema": {"type": "object"}},
                    {"name": "codereview", "description": "Code review", "inputSchema": {"type": "object"}},
                    {"name": "precommit", "description": "Pre-commit validation", "inputSchema": {"type": "object"}},
                ]
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}
        
        if method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name")
            # Forward to PAL HTTP (simplified - real impl needs SSE streaming)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"[PAL Proxy] Tool '{tool_name}' invoked. Full SSE streaming not yet implemented in proxy."}],
                    "isError": False
                }
            }
        
        return None
    
    async def run(self):
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            try:
                msg = json.loads(line.strip())
                resp = await self.handle_message(msg)
                if resp:
                    print(json.dumps(resp), flush=True)
            except json.JSONDecodeError:
                err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                print(json.dumps(err), flush=True)
            except Exception as e:
                err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
                print(json.dumps(err), flush=True)

if __name__ == "__main__":
    proxy = PalStdioProxy()
    asyncio.run(proxy.run())
