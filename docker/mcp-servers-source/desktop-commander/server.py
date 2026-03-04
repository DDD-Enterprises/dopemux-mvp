#!/usr/bin/env python3
"""
FastMCP Server for Desktop Commander
Provides desktop automation and system control capabilities via MCP SSE
"""

import os
import subprocess
import logging
import platform
from typing import Dict, Any
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] - %(message)s',
)
logger = logging.getLogger("desktop-commander-mcp")

# Detect operating system
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Initialize FastMCP server
mcp = FastMCP(
    name="Desktop Commander"
)

@mcp.tool()
async def screenshot(filename: str = "/tmp/screenshot.png") -> Dict[str, Any]:
    """
    Take a screenshot of the current desktop.
    
    Args:
        filename: Output filename for the screenshot
    """
    try:
        if IS_MACOS:
            result = subprocess.run(["screencapture", "-x", filename], capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(["scrot", filename], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return {"success": True, "filename": filename, "message": f"Screenshot saved to {filename}"}
        else:
            return {"success": False, "error": result.stderr or "Screenshot failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def window_list() -> Dict[str, Any]:
    """List all open windows."""
    try:
        if IS_MACOS:
            applescript = 'tell application "System Events" to get name of every window of (every process whose visible is true)'
            result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=10)
            return {"success": True, "windows": result.stdout.strip(), "platform": "macOS"}
        else:
            result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
            return {"success": True, "windows": result.stdout.strip(), "platform": "Linux"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def focus_window(title: str) -> Dict[str, Any]:
    """
    Focus a specific window by title.
    
    Args:
        title: Window title or application name to focus
    """
    try:
        if IS_MACOS:
            applescript = (
                'on run argv\n'
                '  tell application (item 1 of argv) to activate\n'
                'end run'
            )
            result = subprocess.run(
                ["osascript", "-e", applescript, title],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return {"success": result.returncode == 0, "message": f"Focusing {title}"}
        else:
            result = subprocess.run(["wmctrl", "-a", title], capture_output=True, text=True, timeout=5)
            return {"success": result.returncode == 0, "message": f"Focusing {title}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def type_text(text: str) -> Dict[str, Any]:
    """
    Type text using desktop automation.
    
    Args:
        text: Text to type
    """
    try:
        if IS_MACOS:
            escaped_text = text.replace('"', '\\"')
            applescript = f'tell application "System Events" to keystroke "{escaped_text}"'
            result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=10)
            return {"success": result.returncode == 0, "message": "Typed text"}
        else:
            result = subprocess.run(["xdotool", "type", text], capture_output=True, text=True, timeout=10)
            return {"success": result.returncode == 0, "message": "Typed text"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "3012"))
    logger.info(f"🚀 Starting Desktop Commander MCP Server on port {port} (SSE)")
    mcp.run(transport="sse", host="0.0.0.0", port=port)
