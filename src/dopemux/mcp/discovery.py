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
        # Determine probe endpoints - avoid double-joins if URL already has /mcp
        probe_endpoints = []
        if base_url.endswith('/mcp'):
            probe_endpoints.append(base_url)
            # Also try the base in case it's actually a prefix
            probe_endpoints.append(base_url[:-4])
        else:
            probe_endpoints.append(f"{base_url}/mcp")
            probe_endpoints.append(base_url)

        errors = []
        for endpoint in probe_endpoints:
            if not endpoint:
                continue
            try:
                # Use a POST JSON-RPC probe
                payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
                headers = {"Content-Type": "application/json", "Accept": "application/json"}
                
                async with session.post(endpoint, json=payload, headers=headers, timeout=self.timeout) as resp:
                    # Reachability signal: 200 OK OR any status with a valid JSON-RPC body
                    data = None
                    try:
                        data = await resp.json()
                    except Exception:
                        # Fallback: try reading as text if JSON decode fails to see if it's at least responding
                        try:
                            text = await resp.text()
                            if "jsonrpc" in text:
                                data = json.loads(text)
                        except Exception:
                            pass

                    is_jsonrpc = isinstance(data, dict) and "jsonrpc" in data
                    
                    if resp.status == 200 or is_jsonrpc:
                        # Server is REACHABLE because it responded with JSON-RPC (even if error)
                        tools = self._extract_tools(data) if data else []
                        
                        # If we have an error but it's "Method not found", the server IS reachable
                        if isinstance(data, dict) and "error" in data:
                            err_code = data["error"].get("code")
                            if err_code == -32601: # Method not found
                                return {"name": name, "reachable": True, "status": "ok", "tools": [], "endpoint": endpoint, "warning": "tools/list not supported"}
                            
                            errors.append(f"{endpoint}: JSON-RPC Error {err_code}: {data['error'].get('message')}")
                            # If it's a real JSON-RPC error, it's still "reachable" but maybe not "functional"
                            # We'll continue to see if another endpoint works better
                            continue

                        # Success! We found tools or a functional JSON-RPC endpoint
                        return {"name": name, "reachable": True, "status": "ok", "tools": tools, "endpoint": endpoint}
                    else:
                        errors.append(f"{endpoint}: HTTP {resp.status}")
            except Exception as e:
                errors.append(f"{endpoint}: {str(e)}")
                continue

        # Fallback to GET for non-standard servers (legacy)
        for suffix in ["/tools", "/health", ""]:
            try:
                async with session.get(f"{base_url}{suffix}", timeout=self.timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tools = self._extract_tools(data)
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
