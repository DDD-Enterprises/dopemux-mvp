"""Read-only MCP wrappers for orchestrator operator status and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from dopemux.orchestrator.policy import CapabilityDecision, classify_capability
from dopemux.orchestrator.validation.packets import validate_packet_file
from dopemux.orchestrator.validation.proof import validate_proof_file


DEFAULT_PROJECT_ID = "dopemux-mvp"

ORCHESTRATOR_MCP_TOOLS = [
    {
        "name": "orchestrator.status.queue",
        "description": "Read the Task Orchestrator priority queue without mutation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                }
            },
        },
    },
    {
        "name": "orchestrator.status.blockers",
        "description": "Read active Task Orchestrator blockers without mutation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                }
            },
        },
    },
    {
        "name": "orchestrator.status.state",
        "description": "Read workflow state without applying transitions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                }
            },
        },
    },
    {
        "name": "orchestrator.daily.summary",
        "description": "Build a read-only daily operator workflow summary",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                }
            },
        },
    },
    {
        "name": "orchestrator.packet.validate",
        "description": "Validate a Task Packet JSON file against the canonical schema",
        "inputSchema": {
            "type": "object",
            "properties": {
                "packet_path": {"type": "string"},
                "schema_path": {"type": "string"},
            },
            "required": ["packet_path"],
        },
    },
    {
        "name": "orchestrator.proof.validate",
        "description": "Validate a proof bundle JSON file without writing artifacts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proof_path": {"type": "string"},
            },
            "required": ["proof_path"],
        },
    },
]

ORCHESTRATOR_MCP_TOOL_NAMES = {
    tool["name"] for tool in ORCHESTRATOR_MCP_TOOLS
}


async def pm_get_priority_queue(project_id: str):
    from dopemux.pm.reads import pm_get_priority_queue as read_priority_queue

    return await read_priority_queue(project_id)


async def pm_get_blockers(project_id: str):
    from dopemux.pm.reads import pm_get_blockers as read_blockers

    return await read_blockers(project_id)


async def pm_get_workflow_state(project_id: str):
    from dopemux.pm.reads import pm_get_workflow_state as read_workflow_state

    return await read_workflow_state(project_id)


async def handle_orchestrator_tool_call(
    tool_name: str,
    arguments: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Dispatch one registered read-only orchestrator MCP wrapper."""
    args = dict(arguments or {})
    decision = classify_capability(tool_name)
    if tool_name not in ORCHESTRATOR_MCP_TOOL_NAMES:
        return _error_payload(
            tool_name,
            decision,
            "Unknown read-only orchestrator MCP tool",
        )
    if not decision.allowed:
        return _error_payload(
            tool_name,
            decision,
            "Capability is not automatically allowed by policy",
        )

    if tool_name == "orchestrator.status.queue":
        result = await pm_get_priority_queue(_project_id(args))
        return _result_payload(tool_name, decision, _to_mapping(result))

    if tool_name == "orchestrator.status.blockers":
        result = await pm_get_blockers(_project_id(args))
        return _result_payload(tool_name, decision, _to_mapping(result))

    if tool_name == "orchestrator.status.state":
        result = await pm_get_workflow_state(_project_id(args))
        return _result_payload(tool_name, decision, _to_mapping(result))

    if tool_name == "orchestrator.daily.summary":
        project_id = _project_id(args)
        queue = _to_mapping(await pm_get_priority_queue(project_id))
        blockers = _to_mapping(await pm_get_blockers(project_id))
        workflow_state = _to_mapping(await pm_get_workflow_state(project_id))
        return _result_payload(
            tool_name,
            decision,
            {
                "queue": queue,
                "blockers": blockers,
                "workflow_state": workflow_state,
            },
        )

    if tool_name == "orchestrator.packet.validate":
        packet_path = args.get("packet_path")
        if not packet_path:
            return _error_payload(tool_name, decision, "packet_path is required")
        schema_path = args.get("schema_path")
        report = validate_packet_file(
            Path(str(packet_path)),
            schema_path=Path(str(schema_path)) if schema_path else None,
        )
        return _validation_payload(tool_name, decision, report.to_dict())

    if tool_name == "orchestrator.proof.validate":
        proof_path = args.get("proof_path")
        if not proof_path:
            return _error_payload(tool_name, decision, "proof_path is required")
        report = validate_proof_file(Path(str(proof_path)))
        return _validation_payload(tool_name, decision, report.to_dict())

    return _error_payload(tool_name, decision, "Unhandled orchestrator MCP tool")


def _project_id(arguments: Mapping[str, Any]) -> str:
    value = arguments.get("project_id") or DEFAULT_PROJECT_ID
    return str(value)


def _to_mapping(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    return {}


def _policy_payload(decision: CapabilityDecision) -> Dict[str, Any]:
    return decision.to_dict()


def _base_payload(tool_name: str, decision: CapabilityDecision) -> Dict[str, Any]:
    return {
        "tool": tool_name,
        "read_only": True,
        "policy": _policy_payload(decision),
    }


def _result_payload(
    tool_name: str,
    decision: CapabilityDecision,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    payload = _base_payload(tool_name, decision)
    payload["result"] = result
    return payload


def _validation_payload(
    tool_name: str,
    decision: CapabilityDecision,
    report: Dict[str, Any],
) -> Dict[str, Any]:
    payload = _base_payload(tool_name, decision)
    payload["validation"] = report
    return payload


def _error_payload(
    tool_name: str,
    decision: CapabilityDecision,
    message: str,
) -> Dict[str, Any]:
    payload = _base_payload(tool_name, decision)
    payload["error"] = message
    return payload
