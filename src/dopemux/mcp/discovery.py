import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, Any, List

class ToolDiscoveryClient:
    """
    Discovers tools from resolved MCP endpoints.
    Supports standard MCP JSON-RPC over HTTP.
    Normalizes to stable-sorted tool lists.
    """
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.report = {
            "servers": [],
            "reachable": True,
            "tools": {},
            "status": {}
        }

    async def discover(self, resolved_servers: Dict[str, Any]) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for name, config in resolved_servers.items():
                tasks.append(self._discover_server(session, name, config))
            
            results = await asyncio.gather(*tasks)
            
            for res in results:
                self.report["servers"].append(res)
                if not res["reachable"]:
                    # If any server is unreachable, we marked overall reachable as false
                    # wait, only if it's considered "required"
                    # But discovery report should reflect all.
                    pass
                
                name = res["name"]
                self.report["tools"][name] = sorted(res.get("tools", []))
                self.report["status"][name] = res["status"]

        # Final reachability check (if any server failed)
        self.report["reachable"] = all(s["reachable"] for s in self.report["servers"])
        return self.report

    async def _discover_server(self, session: aiohttp.ClientSession, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get("url")
        if not url:
            return {"name": name, "reachable": False, "status": "missing_url", "tools": []}

        base_url = url.rstrip('/')
        
        # Priority 1: Standard MCP JSON-RPC over HTTP
        probe_endpoints = []
        if base_url.endswith('/mcp'):
            probe_endpoints.append(base_url)
            probe_endpoints.append(base_url[:-4])
        else:
            probe_endpoints.append(f"{base_url}/mcp")
            probe_endpoints.append(base_url)

        tool_list_methods = [
            "tools/list",
            "tools.list",
            "mcp.listTools",
            "list_tools",
            "listTools",
        ]

        errors = []
        for endpoint in probe_endpoints:
            if not endpoint:
                continue
            for method in tool_list_methods:
                try:
                    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": {}}
                    # Add comprehensive headers to satisfy strict servers (like Dope-Context/Serena)
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                    
                    async with session.post(endpoint, json=payload, headers=headers, timeout=self.timeout) as resp:
                        data = None
                        try:
                            data = await resp.json()
                        except Exception:
                            try:
                                text = await resp.text()
                                if "jsonrpc" in text:
                                    data = json.loads(text)
                            except Exception:
                                pass

                        is_jsonrpc = isinstance(data, dict) and "jsonrpc" in data
                        
                        if resp.status == 200 or is_jsonrpc:
                            # If we have an error, check if it's a "reachable" error
                            if isinstance(data, dict) and "error" in data:
                                err_code = data["error"].get("code")
                                err_msg = data["error"].get("message", "")
                                
                                # Method not found means server is up but doesn't like this method
                                if err_code == -32601:
                                    continue
                                
                                # Missing session ID or similar handshakes mean the transport is alive
                                if "session" in err_msg.lower() or "not acceptable" in err_msg.lower():
                                    return {"name": name, "reachable": True, "status": "ok", "tools": [], "endpoint": endpoint, "warning": "transport active, handshake required"}

                                errors.append(f"{endpoint} ({method}): JSON-RPC Error {err_code}: {err_msg}")
                                continue

                            tools = self._extract_tools(data) if data else []
                            if tools:
                                return {"name": name, "reachable": True, "status": "ok", "tools": tools, "endpoint": endpoint}
                            
                            continue
                        else:
                            errors.append(f"{endpoint} ({method}): HTTP {resp.status}")
                except Exception as e:
                    errors.append(f"{endpoint} ({method}): {str(e)}")
                    continue

        # If we reached here, try one last check for "Method not found" signal to mark as reachable but unsupported
        for endpoint in probe_endpoints:
            if not endpoint: continue
            try:
                payload = {"jsonrpc": "2.0", "id": 1, "method": "mcp.ping", "params": {}}
                async with session.post(endpoint, json=payload, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        return {"name": name, "reachable": True, "status": "ok", "tools": [], "endpoint": endpoint, "warning": "tool listing unsupported"}
            except Exception:
                pass

        # Fallback to GET for non-standard servers (legacy)
        for suffix in ["/tools", "/health", ""]:
            try:
                async with session.get(f"{base_url}{suffix}", timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tools = self._extract_tools(data)
                        if tools:
                            return {"name": name, "reachable": True, "status": "ok", "tools": tools, "endpoint": f"{base_url}{suffix}"}
            except Exception:
                pass
        
        return {
            "name": name, 
            "reachable": False, 
            "status": "unreachable", 
            "errors": errors,
            "tools": [], 
            "url": url
        }

    def _extract_tools(self, data: Any) -> List[str]:
        # MCP style: {"result": {"tools": [{"name": "..."}]}}
        if isinstance(data, dict):
            # Try JSON-RPC result format
            res = data.get("result")
            if res:
                if isinstance(res, dict):
                    tools_data = res.get("tools", [])
                    if isinstance(tools_data, list):
                        if tools_data and isinstance(tools_data[0], dict):
                            return [t.get("name") for t in tools_data if t.get("name")]
                        return [str(t) for t in tools_data]
                elif isinstance(res, list):
                    if res and isinstance(res[0], dict):
                        return [t.get("name") for t in res if t.get("name")]
                    return [str(t) for t in res]
            
            # Try direct fields
            tools_data = data.get("tools")
            if isinstance(tools_data, list):
                if tools_data and isinstance(tools_data[0], dict):
                    return [t.get("name") for t in tools_data if t.get("name")]
                return [str(t) for t in tools_data]
                
            # If it's just a dict with names
            if not res and not tools_data:
                # Some servers might just return the list of tools directly if not JSON-RPC
                pass

        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                return [t.get("name") for t in data if t.get("name")]
            return [str(t) for t in data]
            
        return []

    def save_report(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.report, f, indent=2, sort_keys=True)
