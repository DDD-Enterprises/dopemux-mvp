#!/usr/bin/env python3
"""
Desktop Commander MCP Server for Dopemux
Provides desktop automation and system control capabilities
Hybrid OS Support: Auto-detects Linux (X11) vs macOS and uses appropriate commands
"""

import os
import sys
import platform
import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detect operating system
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Set DISPLAY for X11 access on macOS/Linux
if IS_MACOS or IS_LINUX:
    if not os.environ.get('DISPLAY'):
        os.environ['DISPLAY'] = ':0'
        logger.info(f"🖥️  Set DISPLAY={os.environ['DISPLAY']} for X11 access")
    else:
        logger.info(f"🖥️  Using existing DISPLAY={os.environ['DISPLAY']}")

logger.info(f"🖥️  Desktop Commander detected OS: {platform.system()}")
logger.info(f"   macOS mode: {IS_MACOS}, Linux mode: {IS_LINUX}")

app = FastAPI(title="Desktop Commander MCP Server", version="2.0.0")

# CORS Configuration
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8097,http://adhd-dashboard:8097"
    ).split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key: Optional[str] = Security(api_key_header),
):
    """Validate API key if DESKTOP_COMMANDER_API_KEY is set."""
    required_key = os.getenv("DESKTOP_COMMANDER_API_KEY")
    if not required_key:
        return None

    if api_key == required_key:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key",
    )

class CommandRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

class CommandResponse(BaseModel):
    result: Any = None
    error: str = None

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "server": "desktop-commander",
        "version": "2.0.0",
        "platform": platform.system(),
        "macos_mode": IS_MACOS,
        "linux_mode": IS_LINUX
    }

@app.get("/info", dependencies=[Depends(get_api_key)])
async def service_info():
    """Service discovery endpoint - auto-config support (ADR-208)"""
    port = int(os.getenv("MCP_SERVER_PORT", 3012))
    return {
        "name": "desktop-commander",
        "version": "2.0.0",
        "mcp": {
            "protocol": "sse",
            "connection": {
                "type": "sse",
                "url": f"http://localhost:{port}/sse"
            },
            "env": {
                "DISPLAY": "${DISPLAY:-:0}"
            }
        },
        "health": "/health",
        "description": "Desktop automation via Docker container",
        "metadata": {
            "role": "utility",
            "priority": "medium",
            "platform": platform.system(),
            "adhd_integration": "Auto-focus windows, sub-2s context switching"
        }
    }

@app.post("/mcp", dependencies=[Depends(get_api_key)])
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
                                "title": {"type": "string", "description": "Window title or application name to focus"}
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
    """Take a screenshot using platform-appropriate tool"""
    try:
        if IS_MACOS:
            # macOS: use screencapture
            # -x: no sound, -t: format (png default)
            result = subprocess.run(
                ["screencapture", "-x", filename],
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            # Linux: use scrot
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
                "message": f"Screenshot saved to {filename}",
                "platform": platform.system()
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Screenshot failed"
            }
    except FileNotFoundError as e:
        tool = "screencapture" if IS_MACOS else "scrot"
        return {
            "success": False,
            "error": f"Tool not found: {tool}. Install required: {'XCode Command Line Tools' if IS_MACOS else 'scrot'}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def list_windows() -> Dict[str, Any]:
    """List all open windows using platform-appropriate tool"""
    try:
        if IS_MACOS:
            # macOS: use AppleScript via osascript
            applescript = '''
            tell application "System Events"
                set appList to {}
                repeat with proc in (every process whose visible is true)
                    set appName to name of proc
                    set windowList to {}
                    try
                        set windowList to (name of every window of proc)
                    end try
                    if (count of windowList) > 0 then
                        repeat with winName in windowList
                            set end of appList to {appName:appName, windowTitle:winName as text}
                        end repeat
                    else
                        set end of appList to {appName:appName, windowTitle:""}
                    end if
                end repeat
                return appList
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse AppleScript output
                windows = []
                # AppleScript returns comma-separated list
                output = result.stdout.strip()
                if output:
                    # Simple parsing for demonstration
                    # In production, use more robust parsing
                    windows.append({
                        "platform": "macOS",
                        "raw_output": output,
                        "message": "Window list retrieved. Parse the raw_output field for details."
                    })

                return {"success": True, "windows": windows, "platform": "macOS"}
            else:
                return {"success": False, "error": result.stderr or "Failed to list windows"}
        else:
            # Linux: use wmctrl
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

                return {"success": True, "windows": windows, "platform": "Linux"}
            else:
                return {"success": False, "error": result.stderr or "Failed to list windows"}

    except FileNotFoundError as e:
        tool = "osascript (AppleScript)" if IS_MACOS else "wmctrl"
        return {
            "success": False,
            "error": f"Tool not found: {tool}. {'Already included in macOS' if IS_MACOS else 'Install wmctrl package'}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def focus_window(title: str) -> Dict[str, Any]:
    """Focus a window by title using platform-appropriate tool"""
    try:
        if IS_MACOS:
            # macOS: use AppleScript to activate application
            # Try treating 'title' as application name first
            applescript = f'tell application "{title}" to activate'

            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Focused application: {title}",
                    "platform": "macOS"
                }
            else:
                # Try finding by window title if app name failed
                applescript2 = f'''
                tell application "System Events"
                    set frontmost of first process whose name contains "{title}" to true
                end tell
                '''
                result2 = subprocess.run(
                    ["osascript", "-e", applescript2],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result2.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Focused process containing: {title}",
                        "platform": "macOS"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Could not find application or window: {title}",
                        "details": result.stderr or result2.stderr
                    }
        else:
            # Linux: use wmctrl
            result = subprocess.run(
                ["wmctrl", "-a", title],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Focused window with title: {title}",
                    "platform": "Linux"
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or f"Failed to focus window: {title}"
                }

    except FileNotFoundError as e:
        tool = "osascript (AppleScript)" if IS_MACOS else "wmctrl"
        return {
            "success": False,
            "error": f"Tool not found: {tool}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def type_text(text: str) -> Dict[str, Any]:
    """Type text using platform-appropriate tool"""
    try:
        if IS_MACOS:
            # macOS: use AppleScript to type text
            # Escape quotes in text
            escaped_text = text.replace('"', '\\"')
            applescript = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Typed text (length: {len(text)})",
                    "platform": "macOS"
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "Failed to type text"
                }
        else:
            # Linux: use xdotool
            result = subprocess.run(
                ["xdotool", "type", text],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Typed: {text[:50]}...",
                    "platform": "Linux"
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "Failed to type text"
                }

    except FileNotFoundError as e:
        tool = "osascript (AppleScript)" if IS_MACOS else "xdotool"
        return {
            "success": False,
            "error": f"Tool not found: {tool}. {'Already included in macOS' if IS_MACOS else 'Install xdotool package'}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Entry point for uvx/uv tool"""
    # Use 127.0.0.1 by default for security, override via MCP_SERVER_HOST
    host = os.getenv('MCP_SERVER_HOST', '127.0.0.1')
    port = int(os.getenv('MCP_SERVER_PORT', 3012))

    logger.info(f"🖥️  Desktop Commander MCP Server v2.0.0")
    logger.info(f"   Platform: {platform.system()}")
    logger.info(f"   Starting on {host}:{port}")

    if host == "0.0.0.0" and not os.getenv("DESKTOP_COMMANDER_API_KEY"):
        logger.warning("⚠️  SECURITY WARNING: Server is exposed on all interfaces (0.0.0.0) without an API key.")
        logger.warning("   It is highly recommended to set DESKTOP_COMMANDER_API_KEY.")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
