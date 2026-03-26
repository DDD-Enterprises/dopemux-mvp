"""Claude native hook adapter for Dopemux workflows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from ..workflow import WorkflowStore


HOOK_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "SessionEnd",
}


def _instance_id(payload: Dict[str, Any]) -> str:
    env = payload.get("env")
    if isinstance(env, dict):
        value = env.get("DOPEMUX_INSTANCE_ID")
        if isinstance(value, str) and value.strip():
            return value
    return "main"


def _cwd(payload: Dict[str, Any]) -> Optional[Path]:
    for key in ("cwd", "workspace", "workspace_root"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value)
    return None


def _tool_name(payload: Dict[str, Any]) -> str:
    for key in ("tool_name", "toolName", "name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    tool = payload.get("tool")
    if isinstance(tool, dict):
        for key in ("name", "tool_name", "toolName"):
            value = tool.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return "unknown"


def _base_response(system_message: str, additional_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "systemMessage": system_message,
        "additionalContext": additional_context,
    }


def _state_context(state) -> Dict[str, Any]:
    return {
        "workflow_id": state.workflow_id,
        "phase": state.phase.value,
        "status": state.status.value,
        "current_task_id": state.current_task_id,
        "iteration": state.iteration,
        "max_iterations": state.max_iterations,
        "max_minutes": state.max_minutes,
        "validation": state.validation_summary(),
    }


def handle_event(event_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = dict(payload or {})
    normalized_event = str(event_name)
    if normalized_event not in HOOK_EVENTS:
        return _base_response(
            f"Unsupported hook event: {normalized_event}",
            {"decision": "noop", "event": normalized_event},
        )

    store = WorkflowStore.for_path(_cwd(payload))
    state = store.resolve_active(_instance_id(payload))
    if state is None:
        return _base_response(
            "No active Dopemux workflow was found for this workspace.",
            {
                "decision": "noop",
                "event": normalized_event,
                "workflow_active": False,
            },
        )

    if normalized_event in {"SessionStart", "UserPromptSubmit"}:
        attention = payload.get("attention_state") or payload.get("attentionState") or "focused"
        state.record_event(
            "hook_context_injected",
            f"{normalized_event} context injected",
            metadata={"attention_state": attention},
        )
        store.save(state)
        return _base_response(
            (
                f"Workflow active. Phase={state.phase.value}, "
                f"current_task={state.current_task_id or 'none'}, attention={attention}."
            ),
            {
                "decision": "continue",
                "event": normalized_event,
                "workflow": _state_context(state),
                "attention_state": attention,
            },
        )

    if normalized_event == "PreToolUse":
        state.iteration += 1
        tool_name = _tool_name(payload)
        state.record_event(
            "tool_attempt",
            f"PreToolUse {tool_name}",
            metadata={"tool_name": tool_name},
        )
        store.save(state)
        violations = state.limit_violations()
        if violations:
            return _base_response(
                (
                    "Workflow execution is blocked until review because one or more run limits "
                    f"were exceeded: {', '.join(violations)}."
                ),
                {
                    "decision": "block",
                    "event": normalized_event,
                    "workflow": _state_context(state),
                    "violations": violations,
                },
            )
        return _base_response(
            f"Tool use accepted for phase {state.phase.value}.",
            {
                "decision": "continue",
                "event": normalized_event,
                "workflow": _state_context(state),
            },
        )

    if normalized_event == "PostToolUse":
        tool_name = _tool_name(payload)
        success = payload.get("success")
        state.record_event(
            "tool_result",
            f"PostToolUse {tool_name}",
            metadata={"tool_name": tool_name, "success": success},
        )
        store.save(state)
        return _base_response(
            f"Recorded tool result for {tool_name}.",
            {
                "decision": "continue",
                "event": normalized_event,
                "workflow": _state_context(state),
            },
        )

    if normalized_event == "Stop":
        if not state.can_stop():
            state.record_event(
                "stop_blocked",
                "Stop blocked because no approved checkpoint or completion token exists.",
            )
            store.save(state)
            return _base_response(
                (
                    "Stop is blocked for the active workflow. Emit an approved checkpoint for the "
                    f"current phase ({state.phase.value}) or include the completion token "
                    f"{state.completion_token!r} in the completion evidence."
                ),
                {
                    "decision": "block",
                    "event": normalized_event,
                    "workflow": _state_context(state),
                },
            )
        state.record_event("stop_allowed", "Stop allowed by workflow checkpoint state.")
        store.save(state)
        return _base_response(
            "Stop allowed for the active workflow.",
            {
                "decision": "continue",
                "event": normalized_event,
                "workflow": _state_context(state),
            },
        )

    state.record_event("session_end", "Workflow session ended.")
    store.save(state)
    return _base_response(
        "Session end recorded for active workflow.",
        {
            "decision": "continue",
            "event": normalized_event,
            "workflow": _state_context(state),
        },
    )


def _load_payload(payload_file: Optional[str]) -> Dict[str, Any]:
    if not payload_file or payload_file == "-":
        raw = sys.stdin.read().strip()
        return json.loads(raw) if raw else {}
    with open(payload_file, "r", encoding="utf-8") as handle:
        raw = handle.read().strip()
    return json.loads(raw) if raw else {}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Emit strict JSON Claude hook responses for Dopemux workflows.")
    parser.add_argument("event_name")
    parser.add_argument("--payload-file", default="-")
    args = parser.parse_args(argv)
    response = handle_event(args.event_name, _load_payload(args.payload_file))
    json.dump(response, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
