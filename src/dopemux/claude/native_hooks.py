"""
Dopemux Native Hook Adapter for Claude Code.

Implements deterministic workflow-aware hook behavior for context injection,
tool logging, and stop-gate continuity.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Tuple

# Ensure core modules are importable
CORE_DIR = Path(__file__).resolve().parents[2]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from dopemux.workflow import WorkflowStatus, contains_completion_token, parse_workflow_checkpoint  # noqa: E402
from dopemux.workflow.service import WorkflowKernel  # noqa: E402

# Claude Code command hook exit codes
EXIT_SUCCESS = 0
EXIT_BLOCK = 2


def _truncate(value: Any, limit: int = 400) -> Any:
    """Trim overly large hook payloads before persisting them."""
    if value is None:
        return None
    if isinstance(value, str):
        return value if len(value) <= limit else value[: limit - 3] + "..."
    if isinstance(value, dict):
        return {str(k): _truncate(v, limit=limit) for k, v in value.items()}
    if isinstance(value, list):
        return [_truncate(item, limit=limit) for item in value[:10]]
    return value


def _response_text(payload: Dict[str, Any]) -> str:
    """Extract the assistant response text from a stop hook payload."""
    for key in (
        "response",
        "assistant_response",
        "prompt_response",
        "completion",
        "text",
        "stop_text",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _workflow_context_lines(state, *, include_gates: bool = False) -> str:
    task = state.current_task()
    lines = [
        f"Dopemux workflow {state.workflow_id} is active.",
        f"Phase: {state.phase.value}",
        f"Mode: {state.mode}",
        f"PM authority: {state.pm_authority} (reachable={state.pm_reachable})",
    ]
    if task:
        lines.append(f"Task: {task.title} [{task.status}]")
    if state.brief_path:
        lines.append(f"Brief: {state.brief_path}")
    lines.append("Explain your next move before acting.")
    lines.append("Keep changes evidence-first, anti-slop, and checkpoint-driven.")
    if include_gates:
        failures = state.gate_failures_for(state.phase)
        if failures:
            lines.append("Gate warnings:")
            lines.extend(f"- {failure}" for failure in failures)
    return "\n".join(lines)


class NativeHookAdapter:
    """Handle Claude Code command hooks for Dopemux workflow continuity."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = (project_root or Path.cwd()).resolve()
        self.instance_id = os.environ.get("DOPEMUX_INSTANCE_ID") or "A"
        self.kernel = WorkflowKernel(self.project_root)

    def _emit(self, payload: Dict[str, Any], exit_code: int = EXIT_SUCCESS) -> Tuple[int, Dict[str, Any]]:
        return exit_code, payload

    def _allow(self, *, system_message: Optional[str] = None, additional_context: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        if system_message:
            payload["systemMessage"] = system_message
        if additional_context:
            payload["hookSpecificOutput"] = {
                "additionalContext": additional_context,
            }
        return self._emit(payload, EXIT_SUCCESS)

    def _deny_tool(self, message: str, additional_context: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "systemMessage": message,
            "hookSpecificOutput": {
                "permissionDecision": "deny",
            },
        }
        if additional_context:
            payload["hookSpecificOutput"]["additionalContext"] = additional_context
        return self._emit(payload, EXIT_SUCCESS)

    def _block_stop(self, message: str, additional_context: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "decision": "block",
            "systemMessage": message,
        }
        if additional_context:
            payload["hookSpecificOutput"] = {
                "additionalContext": additional_context,
            }
        return self._emit(payload, EXIT_SUCCESS)

    def _active_state(self):
        state = self.kernel.resolve()
        if not state:
            return None
        if state.status not in {WorkflowStatus.ACTIVE, WorkflowStatus.PAUSED}:
            return None
        return state

    @staticmethod
    def _elapsed_minutes(state) -> int:
        try:
            started_at = state.started_at.replace("Z", "+00:00")
            start_time = datetime.fromisoformat(started_at)
        except ValueError:
            return 0
        return max(0, int((datetime.now(start_time.tzinfo) - start_time).total_seconds() // 60))

    def handle_event(self, event_data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Main entry point for hook execution."""
        event_name = str(event_data.get("hook_event_name", ""))
        try:
            if event_name == "SessionStart":
                return self._on_session_start()
            if event_name == "UserPromptSubmit":
                return self._on_user_prompt(event_data)
            if event_name == "PreToolUse":
                return self._on_pre_tool_use(event_data)
            if event_name == "PermissionRequest":
                return self._on_permission_request(event_data)
            if event_name == "PostToolUse":
                return self._on_post_tool_use(event_data)
            if event_name == "PostToolUseFailure":
                return self._on_post_tool_use_failure(event_data)
            if event_name in {"Stop", "SubagentStop"}:
                return self._on_stop(event_data)
            if event_name == "PreCompact":
                return self._on_pre_compact()
            if event_name == "SessionEnd":
                return self._on_session_end(event_data)
        except Exception as exc:  # pragma: no cover - reliability fallback
            return self._allow(system_message=f"Dopemux hook fallback: {type(exc).__name__}")
        return self._allow()

    def _on_session_start(self) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()
        context = _workflow_context_lines(state, include_gates=True)
        return self._allow(
            system_message=f"Dopemux workflow mode: {state.mode}",
            additional_context=context,
        )

    def _on_user_prompt(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        state.iteration += 1
        state.record_history(
            event="hook.user_prompt",
            message="User prompt submitted while workflow was active.",
            details={"prompt": _truncate(data.get("prompt"))},
        )
        self.kernel.save(state)
        return self._allow(
            additional_context=_workflow_context_lines(state, include_gates=True),
        )

    def _on_pre_tool_use(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        tool_name = str(data.get("tool_name") or "unknown")
        if state.max_iterations > 0 and state.iteration > state.max_iterations:
            return self._deny_tool(
                f"Workflow iteration limit reached ({state.iteration}/{state.max_iterations}).",
                _workflow_context_lines(state, include_gates=True),
            )
        elapsed_minutes = self._elapsed_minutes(state)
        if state.max_minutes > 0 and elapsed_minutes >= state.max_minutes:
            return self._deny_tool(
                f"Workflow time limit reached ({elapsed_minutes}/{state.max_minutes} minutes).",
                _workflow_context_lines(state, include_gates=True),
            )

        self.kernel.record_tool_event(
            state,
            event_name="pretooluse",
            tool_name=tool_name,
            status="attempt",
            payload={
                "tool_input": _truncate(data.get("tool_input")),
            },
        )
        return self._allow()

    def _on_permission_request(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        tool_name = str(data.get("tool_name") or "")
        safe_tools = {"read_file", "glob", "list_dir", "search_file_content"}
        if tool_name in safe_tools:
            return self._emit(
                {
                    "hookSpecificOutput": {
                        "permissionDecision": "allow",
                        "additionalContext": _workflow_context_lines(state),
                    }
                },
                EXIT_SUCCESS,
            )
        return self._allow()

    def _on_post_tool_use(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        self.kernel.record_tool_event(
            state,
            event_name="posttooluse",
            tool_name=str(data.get("tool_name") or "unknown"),
            status="success",
            payload={
                "tool_input": _truncate(data.get("tool_input")),
                "tool_response": _truncate(data.get("tool_response")),
            },
        )
        return self._allow()

    def _on_post_tool_use_failure(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        self.kernel.record_tool_event(
            state,
            event_name="posttoolusefailure",
            tool_name=str(data.get("tool_name") or "unknown"),
            status="failure",
            payload={
                "tool_input": _truncate(data.get("tool_input")),
                "error": _truncate(data.get("error")),
            },
        )
        return self._allow()

    def _on_stop(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        if data.get("stop_hook_active") is True:
            return self._allow()

        response_text = _response_text(data)
        if response_text:
            state = self.kernel.apply_response_text(state, response_text)

        checkpoint = parse_workflow_checkpoint(response_text)
        if checkpoint and checkpoint.status.is_stop_safe:
            return self._allow(
                system_message=f"Workflow checkpoint accepted: {checkpoint.phase.value}/{checkpoint.status.value}",
                additional_context=_workflow_context_lines(state),
            )

        if contains_completion_token(response_text, state.completion_token) or state.status == WorkflowStatus.COMPLETE:
            return self._allow(
                system_message="Workflow completion token observed.",
                additional_context=_workflow_context_lines(state),
            )

        return self._block_stop(
            f"Workflow {state.workflow_id} is still active in phase '{state.phase.value}'.",
            _workflow_context_lines(state, include_gates=True),
        )

    def _on_pre_compact(self) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()
        return self._allow(
            additional_context=_workflow_context_lines(state, include_gates=True),
        )

    def _on_session_end(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        state = self._active_state()
        if not state:
            return self._allow()

        state.record_history(
            event="hook.session_end",
            message="Claude Code session ended while workflow state persisted.",
            details={"reason": data.get("reason")},
        )
        self.kernel.save(state)
        return self._allow()


def main() -> None:
    """CLI entry point for the hook script."""
    raw_input = sys.stdin.read()
    if not raw_input:
        sys.exit(EXIT_SUCCESS)

    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(1)

    adapter = NativeHookAdapter()
    exit_code, response = adapter.handle_event(payload)
    if response:
        sys.stdout.write(json.dumps(response))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
