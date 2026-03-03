import asyncio
import aiohttp
import json
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional

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

        # Common MCP-over-HTTP patterns
        endpoints = [
            # 1. Standard bridge endpoint (POST /mcp)
            (f"{url.rstrip('/')}/mcp", "POST", {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}),
            # 2. Simple list tools endpoint (GET /tools)
            (f"{url.rstrip('/')}/tools", "GET", None),
            # 3. Direct JSON-RPC endpoint (POST /)
            (f"{url.rstrip('/')}/", "POST", {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}),
        ]
        
        errors = []
        for endpoint, method, payload in endpoints:
            try:
                if method == "POST":
                    async with session.post(endpoint, json=payload, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            tools = self._extract_tools(data)
                            return {"name": name, "reachable": True, "status": "ok", "tools": tools, "endpoint": endpoint}
                        else:
                            errors.append(f"{endpoint}: HTTP {resp.status}")
                else:
                    async with session.get(endpoint, timeout=self.timeout) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            tools = self._extract_tools(data)
                            return {"name": name, "reachable": True, "status": "ok", "tools": tools, "endpoint": endpoint}
                        else:
                            errors.append(f"{endpoint}: HTTP {resp.status}")
            except Exception as e:
                errors.append(f"{endpoint}: {str(e)}")
                continue
        
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
            res = data.get("result", data)
            if isinstance(res, dict):
                tools_data = res.get("tools", [])
                if isinstance(tools_data, list):
                    if tools_data and isinstance(tools_data[0], dict):
                        return [t.get("name") for t in tools_data if t.get("name")]
                    return [str(t) for t in tools_data]
            # Try list format
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    return [t.get("name") for t in data if t.get("name")]
                return [str(t) for t in data]
        return []

    def save_report(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.report, f, indent=2, sort_keys=True)
