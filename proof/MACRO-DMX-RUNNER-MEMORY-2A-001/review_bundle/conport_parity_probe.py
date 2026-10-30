"""Read-only ConPort tool-parity probe: JSON-RPC POST /mcp (REST child) vs the SSE MCP surface.

Sends only initialize / notifications/initialized / tools/list. Never calls a tool.
Usage: python3 -I conport_parity_probe.py <rest_port> <sse_port>
"""
import http.client
import json
import sys
import threading
import queue

REST_PORT, SSE_PORT = int(sys.argv[1]), int(sys.argv[2])
HOST = "127.0.0.1"


def rest_call(method, params=None, req_id=1):
    conn = http.client.HTTPConnection(HOST, REST_PORT, timeout=10)
    body = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
    conn.request("POST", "/mcp", body, {"Content-Type": "application/json"})
    resp = conn.getresponse()
    return resp.status, json.loads(resp.read() or b"{}")


def sse_tools():
    conn = http.client.HTTPConnection(HOST, SSE_PORT, timeout=15)
    conn.request("GET", "/sse", headers={"Accept": "text/event-stream"})
    resp = conn.getresponse()
    if resp.status != 200:
        return f"GET /sse -> {resp.status}", None
    events: "queue.Queue[tuple[str, str]]" = queue.Queue()

    def reader():
        event, data = "message", []
        for raw in resp:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].strip())
            elif line == "":
                if data:
                    events.put((event, "\n".join(data)))
                event, data = "message", []

    threading.Thread(target=reader, daemon=True).start()
    ev, endpoint = events.get(timeout=10)
    if ev != "endpoint":
        return f"first SSE event was {ev!r}, not endpoint", None

    def post(msg):
        c = http.client.HTTPConnection(HOST, SSE_PORT, timeout=10)
        c.request("POST", endpoint, json.dumps(msg), {"Content-Type": "application/json"})
        r = c.getresponse()
        r.read()
        return r.status

    def wait_for(req_id):
        while True:
            _, payload = events.get(timeout=15)
            msg = json.loads(payload)
            if msg.get("id") == req_id:
                return msg

    post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "parity-probe", "version": "0"}}})
    init = wait_for(1)
    post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    listed = wait_for(2)
    server = init.get("result", {}).get("serverInfo", {})
    return f"ok (server {server.get('name')} {server.get('version')})", sorted(
        t["name"] for t in listed.get("result", {}).get("tools", []))


out = {}
status, init = rest_call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                        "clientInfo": {"name": "parity-probe", "version": "0"}})
out["rest_initialize"] = {"http": status, "error": init.get("error"), "has_result": "result" in init}
status, listed = rest_call("tools/list", req_id=2)
rest_names = sorted(t["name"] for t in listed.get("result", {}).get("tools", []))
out["rest_tools_list"] = {"http": status, "count": len(rest_names), "error": listed.get("error")}

try:
    sse_status, sse_names = sse_tools()
except Exception as exc:  # report, never retry
    sse_status, sse_names = f"error: {type(exc).__name__}: {exc}", None
out["sse"] = {"status": sse_status, "count": None if sse_names is None else len(sse_names)}

if sse_names is not None:
    out["only_rest"] = sorted(set(rest_names) - set(sse_names))
    out["only_sse"] = sorted(set(sse_names) - set(rest_names))
    out["identical"] = rest_names == sse_names
out["rest_names"] = rest_names
out["sse_names"] = sse_names
print(json.dumps(out, indent=1))
