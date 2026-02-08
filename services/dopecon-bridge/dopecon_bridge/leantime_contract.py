"""Leantime PM route contract helpers.

Shared translation/normalization logic used by `/route/pm` when routing
operations to leantime-bridge.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

LEANTIME_ROUTE_OPERATION_TO_TOOL: Dict[str, str] = {
    "get_tasks": "list_tickets",
    "list_tasks": "list_tickets",
    "create_task": "create_ticket",
    "update_task": "update_ticket",
    "update_task_status": "update_ticket",
    "create_project": "create_project",
    "get_project_status": "get_project_stats",
    "allocate_resource": "update_ticket",
    "update_sprint": "update_ticket",
    "leantime.get_tasks": "list_tickets",
    "leantime.list_tasks": "list_tickets",
    "leantime.create_task": "create_ticket",
    "leantime.update_task": "update_ticket",
    "leantime.update_task_status": "update_ticket",
    "leantime.create_project": "create_project",
    "leantime.get_project_status": "get_project_stats",
    "leantime.allocate_resource": "update_ticket",
    "leantime.update_sprint": "update_ticket",
}


def normalize_leantime_priority(value: Any) -> str:
    """Normalize mixed priority values to Leantime's 1-4 scale."""
    if value is None:
        return "2"
    if isinstance(value, int):
        return str(min(max(value, 1), 4))
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        return str(min(max(parsed, 1), 4))

    mapped = {
        "low": "1",
        "medium": "2",
        "med": "2",
        "high": "3",
        "critical": "4",
        "urgent": "4",
    }
    return mapped.get(str(value).strip().lower(), "2")


def coerce_optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_leantime_tool_request(operation: str, data: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Translate cross-plane PM route payloads to leantime-bridge tool calls."""
    op = (operation or "").strip().lower()
    tool_name = LEANTIME_ROUTE_OPERATION_TO_TOOL.get(op)
    if not tool_name:
        raise ValueError(f"Unsupported PM operation: {operation}")

    payload = dict(data or {})

    if tool_name == "list_tickets":
        req: Dict[str, Any] = {}
        project_id = payload.get("projectId", payload.get("project_id"))
        if project_id is not None:
            req["projectId"] = int(project_id)
        if "status" in payload:
            req["status"] = payload["status"]
        assigned_to = payload.get("assignedTo", payload.get("assigned_to"))
        if assigned_to is not None:
            req["assignedTo"] = int(assigned_to)
        return tool_name, req

    if tool_name == "create_ticket":
        headline = payload.get("headline", payload.get("title"))
        if not headline:
            raise ValueError("create_task requires 'title' or 'headline'")
        req = {
            "projectId": int(payload.get("projectId", payload.get("project_id", 1))),
            "headline": headline,
            "description": payload.get("description", ""),
            "priority": normalize_leantime_priority(payload.get("priority")),
            "type": payload.get("type", "task"),
        }
        milestone_id = coerce_optional_int(payload.get("milestoneid", payload.get("milestone_id")))
        if milestone_id is not None:
            req["milestoneid"] = milestone_id
        return tool_name, req

    if tool_name == "update_ticket":
        ticket_id = (
            payload.get("ticketId")
            or payload.get("task_id")
            or payload.get("taskId")
            or payload.get("id")
            or payload.get("sprint_id")
            or payload.get("sprintId")
            or (payload.get("allocation") or {}).get("task_id")
            or (payload.get("allocation") or {}).get("taskId")
            or (payload.get("allocation") or {}).get("ticketId")
        )
        if ticket_id is None:
            raise ValueError("update operation requires ticket/task identifier")
        req = {"ticketId": int(ticket_id)}
        for field in ("headline", "description", "status"):
            if field in payload:
                req[field] = payload[field]
        if "priority" in payload:
            req["priority"] = normalize_leantime_priority(payload["priority"])

        assigned_to = coerce_optional_int(payload.get("assignedTo", payload.get("assigned_to")))
        if assigned_to is None:
            allocation = payload.get("allocation") or {}
            assigned_to = coerce_optional_int(
                allocation.get("assignedTo", allocation.get("assigned_to"))
            )
        if assigned_to is None and (operation or "").strip().lower().endswith("allocate_resource"):
            if str(payload.get("resource_type", "")).strip().lower() in {"user", "assignee", "member"}:
                assigned_to = coerce_optional_int(payload.get("resource_id"))
        if assigned_to is not None:
            req["assignedTo"] = assigned_to
        return tool_name, req

    if tool_name == "create_project":
        name = payload.get("name", payload.get("project_name"))
        if not name:
            raise ValueError("create_project requires 'name' or 'project_name'")
        details = payload.get("details", payload.get("description", ""))
        req = {
            "name": name,
            "description": details if isinstance(details, str) else json.dumps(details, ensure_ascii=True),
        }
        if "state" in payload:
            req["state"] = str(payload["state"])
        return tool_name, req

    if tool_name == "get_project_stats":
        project_id = payload.get("projectId", payload.get("project_id"), payload.get("id"))
        if project_id is None:
            raise ValueError("get_project_status requires project identifier")
        return tool_name, {"projectId": int(project_id)}

    return tool_name, payload


def extract_ticket_list(tool_result: Any) -> List[Dict[str, Any]]:
    if isinstance(tool_result, list):
        return [item for item in tool_result if isinstance(item, dict)]
    if not isinstance(tool_result, dict):
        return []
    for key in ("tasks", "tickets", "result", "items"):
        value = tool_result.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def normalize_leantime_route_response(operation: str, tool_result: Any) -> Dict[str, Any]:
    """Shape responses for existing clients expecting task_id/tasks/project_id keys."""
    op = (operation or "").strip().lower()

    if op in {"get_tasks", "list_tasks", "leantime.get_tasks", "leantime.list_tasks"}:
        return {
            "tasks": extract_ticket_list(tool_result),
            "source": "leantime-bridge",
            "raw_result": tool_result,
        }

    if op in {"create_task", "leantime.create_task"}:
        if isinstance(tool_result, dict):
            ticket_id = tool_result.get("id") or tool_result.get("ticketId") or tool_result.get("task_id")
            response = dict(tool_result)
            if ticket_id is not None:
                response["task_id"] = str(ticket_id)
            return response
        return {"task_id": str(tool_result), "raw_result": tool_result}

    if op in {"create_project", "leantime.create_project"}:
        if isinstance(tool_result, dict):
            project_id = tool_result.get("id") or tool_result.get("projectId") or tool_result.get("project_id")
            response = dict(tool_result)
            if project_id is not None:
                response["project_id"] = str(project_id)
            return response
        return {"project_id": str(tool_result), "raw_result": tool_result}

    if op in {"update_sprint", "leantime.update_sprint"}:
        return {"updated": True, "raw_result": tool_result}

    if op in {"allocate_resource", "leantime.allocate_resource"}:
        return {"allocated": True, "raw_result": tool_result}

    if op in {"get_project_status", "leantime.get_project_status"}:
        if isinstance(tool_result, dict):
            return dict(tool_result)
        return {"result": tool_result}

    return {"result": tool_result}
