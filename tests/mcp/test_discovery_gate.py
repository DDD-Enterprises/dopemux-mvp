import asyncio
import json
import os
import shutil
from pathlib import Path
from aiohttp import web
from dopemux.mcp.gate import DiscoveryGate

# Mock MCP Server
async def handle_mcp(request):
    data = await request.json()
    if data.get("method") == "tools/list":
        return web.json_response({
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "tools": [
                    {"name": "conport_search"},
                    {"name": "conport_upsert"}
                ]
            }
        })
    return web.json_response({"error": "unknown method"})

async def start_mock_server(port):
    app = web.Application()
    app.router.add_post("/mcp", handle_mcp)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return runner

async def test_discovery_gate():
    project_root = Path.cwd() / "tmp_test_project"
    project_root.mkdir(parents=True, exist_ok=True)
    
    # 1. Create .dopemux/mcp.instances.toml
    dopemux_dir = project_root / ".dopemux"
    dopemux_dir.mkdir(exist_ok=True)
    
    with open(dopemux_dir / "mcp.instances.toml", "w") as f:
        f.write("""
[project]
project_id = "test-project"

[mcp.conport]
url = "http://127.0.0.1:8099"
transport = "http"
required_tool_globs = ["conport_*"]
""")

    # 2. Start mock server
    mock_runner = await start_mock_server(8099)
    print("Mock server started on 8099")

    try:
        # 3. Run gate
        gate = DiscoveryGate(project_root, run_id="test_run")
        passed = await gate.run()
        
        print(f"Gate result: {'PASS' if passed else 'BLOCK'}")
        
        # Verify reports exist
        proof_dir = project_root / "proof" / "test_run"
        if (proof_dir / "INSTANCE_RESOLUTION.json").exists():
            print("✓ INSTANCE_RESOLUTION.json created")
        if (proof_dir / "DISCOVERY_REPORT.json").exists():
            print("✓ DISCOVERY_REPORT.json created")
        if (proof_dir / "GATE_RESULT.json").exists():
            print("✓ GATE_RESULT.json created")

        # 4. Test failure case (missing glob)
        with open(dopemux_dir / "mcp.instances.toml", "w") as f:
            f.write("""
[project]
project_id = "test-project"

[mcp.conport]
url = "http://127.0.0.1:8099"
transport = "http"
required_tool_globs = ["conport_*", "missing_tool_*"]
""")
        
        gate2 = DiscoveryGate(project_root, run_id="test_run_fail")
        passed2 = await gate2.run()
        print(f"Gate result (expected failure): {'PASS' if passed2 else 'BLOCK'}")
        if not passed2:
            print("✓ Missing tool glob successfully blocked")

    finally:
        await mock_runner.cleanup()
        # shutil.rmtree(project_root)

if __name__ == "__main__":
    asyncio.run(test_discovery_gate())
