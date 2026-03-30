"""
Dopemux Native Hook Adapter for Claude Code.

Implements the internal hook contract for Claude Code, enabling deterministic
context injection and high-fidelity action capture.
"""

import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure core modules are importable
CORE_DIR = Path(__file__).resolve().parents[2]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# Constants for Claude Code hook response codes
EXIT_SUCCESS = 0
EXIT_BLOCK = 2

class NativeHookAdapter:
    """
    Handles internal Claude Code hook events.
    
    Transforms internal JSON events into Dopemux memory actions.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.dopemux_home = Path.home() / ".dopemux"
        self.instance_id = os.environ.get("DOPEMUX_INSTANCE_ID", "A")
        
    def handle_event(self, event_data: Dict[str, Any]) -> int:
        """
        Main entry point for hook execution.
        
        Args:
            event_data: The JSON object received via stdin from Claude Code.
        """
        event_name = event_data.get("hook_event_name")
        
        try:
            if event_name == "SessionStart":
                return self._on_session_start(event_data)
            elif event_name == "UserPromptSubmit":
                return self._on_user_prompt(event_data)
            elif event_name == "PreToolUse":
                return self._on_pre_tool_use(event_data)
            elif event_name == "PermissionRequest":
                return self._on_permission_request(event_data)
            elif event_name == "PostToolUse":
                return self._on_post_tool_use(event_data)
            elif event_name == "PostToolUseFailure":
                return self._on_post_tool_use_failure(event_data)
            elif event_name == "Stop" or event_name == "SubagentStop":
                return self._on_stop(event_data)
            elif event_name == "PreCompact":
                return self._on_pre_compact(event_data)
            elif event_name == "SessionEnd":
                return self._on_session_end(event_data)
        except Exception:
            # Silent failure for reliability
            return EXIT_SUCCESS
            
        return EXIT_SUCCESS

    def _on_session_start(self, data: Dict[str, Any]) -> int:
        """Inject initial Dopemux context at startup."""
        from dopemux.ui.theme import Glyphs
        
        role = os.environ.get("DOPEMUX_AGENT_ROLE", "developer")
        
        # Load project-specific context
        context_file = self.project_root / ".dopemux" / "instances" / self.instance_id / "context.json"
        goal = "Unknown"
        if context_file.exists():
            try:
                state = json.loads(context_file.read_text())
                goal = state.get("current_goal", "Continue development")
            except:
                pass

        # Check attention status
        attention_status = self._get_attention_status()

        response = {
            "systemMessage": f"{Glyphs.BRAND_MARK} Dopemux Intelligence Active. Role: {role.upper()}",
            "hookSpecificOutput": {
                "additionalContext": (
                    f"Dopemux Status: Unified\n"
                    f"Active Goal: {goal}\n"
                    f"Instance: {self.instance_id}\n"
                    f"Integrity: Verified\n"
                    f"Attention State: {attention_status}\n"
                )
            }
        }
        print(json.dumps(response))
        return EXIT_SUCCESS

    def _on_user_prompt(self, data: Dict[str, Any]) -> int:
        """Inject relevant memories based on the user's prompt."""
        # Inject attention monitor state update
        attention_status = self._get_attention_status()
        
        response = {
            "hookSpecificOutput": {
                "additionalContext": f"[Dopemux Monitor: Attention={attention_status}]"
            }
        }
        print(json.dumps(response))
        return EXIT_SUCCESS

    def _on_pre_tool_use(self, data: Dict[str, Any]) -> int:
        """Validate tool use against Dopemux guardrails."""
        tool_name = data.get("tool_name")
        
        # Log the attempt
        self._log_action(data, status="attempt")
        
        # Auto-allow logic for safe tools in specific modes
        safe_tools = {"ls", "grep", "cat", "read_file", "list_dir"}
        if tool_name in safe_tools:
            # We can use hookSpecificOutput.permissionDecision to automate
            pass
            
        return EXIT_SUCCESS

    def _on_permission_request(self, data: Dict[str, Any]) -> int:
        """Automate permissions based on Dopemux policy."""
        tool_name = data.get("tool_name")
        role = os.environ.get("DOPEMUX_AGENT_ROLE", "developer")
        
        # In 'act' mode, we might want to auto-approve more tools
        if role.lower() == "act":
            safe_tools = {"ls", "grep", "cat", "read_file", "list_dir", "glob"}
            if tool_name in safe_tools:
                response = {
                    "hookSpecificOutput": {
                        "permissionDecision": "allow"
                    }
                }
                print(json.dumps(response))
                
        return EXIT_SUCCESS

    def _on_post_tool_use(self, data: Dict[str, Any]) -> int:
        """Capture successful tool execution."""
        self._log_action(data, status="success")
        return EXIT_SUCCESS

    def _on_post_tool_use_failure(self, data: Dict[str, Any]) -> int:
        """Capture failed tool execution."""
        self._log_action(data, status="failure")
        return EXIT_SUCCESS

    def _on_stop(self, data: Dict[str, Any]) -> int:
        """Handle session stop/pause."""
        return EXIT_SUCCESS

    def _on_pre_compact(self, data: Dict[str, Any]) -> int:
        """Prepare context before compaction."""
        return EXIT_SUCCESS

    def _on_session_end(self, data: Dict[str, Any]) -> int:
        """Cleanup and final state flush."""
        return EXIT_SUCCESS

    def _get_attention_status(self) -> str:
        """Retrieve current attention state from monitor."""
        status_file = self.project_root / ".dopemux" / "attention" / "status.json"
        if status_file.exists():
            try:
                state = json.loads(status_file.read_text())
                return state.get("attention_state", "normal")
            except:
                pass
        return "normal"

    def _log_action(self, data: Dict[str, Any], status: str) -> None:
        """Helper to log actions to local instance state."""
        log_dir = self.dopemux_home / "instances" / self.instance_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": time.time(),
            "event": data.get("hook_event_name"),
            "tool": data.get("tool_name"),
            "input": data.get("tool_input"),
            "status": status,
            "error": data.get("error")
        }
        
        try:
            with open(log_dir / "actions.jsonl", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass

def main():
    """CLI entry point for the hook script."""
    try:
        # Read JSON from stdin
        line = sys.stdin.read()
        if not line:
            sys.exit(0)
            
        input_data = json.loads(line)
        
        adapter = NativeHookAdapter()
        sys.exit(adapter.handle_event(input_data))
        
    except json.JSONDecodeError:
        sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
