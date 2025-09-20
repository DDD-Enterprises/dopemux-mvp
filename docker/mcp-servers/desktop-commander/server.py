#!/usr/bin/env python3
"""
Desktop Commander MCP Server for Dopemux
Provides desktop automation and system control capabilities
"""

import os
import subprocess
import json
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Desktop Commander MCP Server", version="1.0.0")

class CommandRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

class CommandResponse(BaseModel):
    result: Any = None
    error: str = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "server": "desktop-commander"}

@app.post("/mcp")
async def handle_mcp_request(request: CommandRequest) -> CommandResponse:
    """Handle MCP protocol requests for desktop automation"""
    try:
        method = request.method
        params = request.params

        if method == "tools/list":
            return CommandResponse(result={
                "tools": [
                    {
                        "name": "screenshot",
                        "description": "Take a screenshot of the current desktop",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filename": {"type": "string", "description": "Output filename"}
                            }
                        }
                    },
                    {
                        "name": "window_list",
                        "description": "List all open windows",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "focus_window",
                        "description": "Focus a specific window by title",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Window title to focus"}
                            },
                            "required": ["title"]
                        }
                    },
                    {
                        "name": "type_text",
                        "description": "Type text using desktop automation",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "Text to type"}
                            },
                            "required": ["text"]
                        }
                    }
                ]
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "screenshot":
                filename = arguments.get("filename", "/tmp/screenshot.png")
                result = await take_screenshot(filename)
                return CommandResponse(result=result)

            elif tool_name == "window_list":
                result = await list_windows()
                return CommandResponse(result=result)

            elif tool_name == "focus_window":
                title = arguments.get("title")
                result = await focus_window(title)
                return CommandResponse(result=result)

            elif tool_name == "type_text":
                text = arguments.get("text")
                result = await type_text(text)
                return CommandResponse(result=result)

            else:
                return CommandResponse(error=f"Unknown tool: {tool_name}")

        else:
            return CommandResponse(error=f"Unknown method: {method}")

    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return CommandResponse(error=str(e))

async def take_screenshot(filename: str) -> Dict[str, Any]:
    """Take a screenshot using scrot"""
    try:
        result = subprocess.run(
            ["scrot", filename],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return {
                "success": True,
                "filename": filename,
                "message": f"Screenshot saved to {filename}"
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Screenshot failed"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def list_windows() -> Dict[str, Any]:
    """List all open windows using wmctrl"""
    try:
        result = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            windows = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        windows.append({
                            "id": parts[0],
                            "desktop": parts[1],
                            "client": parts[2],
                            "title": parts[3]
                        })

            return {"success": True, "windows": windows}
        else:
            return {"success": False, "error": result.stderr or "Failed to list windows"}

    except Exception as e:
        return {"success": False, "error": str(e)}

async def focus_window(title: str) -> Dict[str, Any]:
    """Focus a window by title using wmctrl"""
    try:
        result = subprocess.run(
            ["wmctrl", "-a", title],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return {"success": True, "message": f"Focused window with title: {title}"}
        else:
            return {"success": False, "error": result.stderr or f"Failed to focus window: {title}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

async def type_text(text: str) -> Dict[str, Any]:
    """Type text using xdotool"""
    try:
        result = subprocess.run(
            ["xdotool", "type", text],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return {"success": True, "message": f"Typed: {text[:50]}..."}
        else:
            return {"success": False, "error": result.stderr or "Failed to type text"}

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv('MCP_SERVER_PORT', 3012))
    logger.info(f"🖥️  Desktop Commander MCP Server starting on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )