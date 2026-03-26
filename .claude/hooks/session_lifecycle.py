#!/usr/bin/env python3
import json
import os
import sys
import httpx
import asyncio
from pathlib import Path

ORCHESTRATOR_URL = "http://localhost:3009"  # Default port from app.py settings or config

async def call_tool(tool_name: str, args: dict):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/api/tools/{tool_name}",
                json=args
            )
            return response.json()
    except Exception as e:
        # Hooks should be silent on failure to not disrupt Claude
        return {"error": str(e)}

async def main():
    if len(sys.argv) < 2:
        return

    event = sys.argv[1]  # 'start' or 'stop'
    
    if event == "start":
        # Get current working directory name as task description
        cwd = os.getcwd()
        task_desc = f"Working in {os.path.basename(cwd)}"
        
        result = await call_tool("start_session", {
            "task_description": task_desc,
            "energy_level": "medium"
        })
        # Start session might return a visual banner to print
        if "display" in result:
            print(result["display"])
            
    elif event == "stop":
        # End current session if exists
        # We might need to find the session ID from /tmp/dopemux_current_session.json
        session_file = Path("/tmp/dopemux_current_session.json")
        if session_file.exists():
            try:
                session_data = json.loads(session_file.read_text())
                session_id = session_data.get("session_id")
                if session_id:
                    await call_tool("end_session", {
                        "session_id": session_id,
                        "outcome": "completed"
                    })
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
