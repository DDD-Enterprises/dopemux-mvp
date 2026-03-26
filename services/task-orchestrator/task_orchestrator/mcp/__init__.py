"""
Task-Orchestrator MCP Tools.

MCP tool definitions and handlers for task orchestration.
Provides 13 tools: 6 original + 7 new high-value tools for daily dev workflow.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..adhd import adhd_monitor
from ..agents import agent_coordinator
from ..core import leantime_client, redis_manager
from ..models import TaskStatus
from .resilience import graceful_degradation
from .visual_tools import (
    format_session_banner,
    format_task_decomposition,
    format_workflow_status,
    format_context_switch,
    format_risk_assessment
)
from ..adapters.auto_logger import auto_logger
from ..adapters.bridge_publisher import publish_session_event, publish_task_event

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# In-memory session store (local-first, syncs to Redis when up)
# ──────────────────────────────────────────────────────────────

_sessions: Dict[str, Dict[str, Any]] = {}
_context_switches: List[Dict[str, Any]] = []
_file_edits: List[Dict[str, Any]] = []

SESSION_FILE = "/tmp/dopemux_current_session.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────
# MCP Tool Definitions (schema for /api/tools listing)
# ──────────────────────────────────────────────────────────────

MCP_TOOLS = [
    # --- Original 6 tools ---
    {
        "name": "analyze_dependencies",
        "description": "Analyze task dependencies and detect conflicts, blockers, and critical paths",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "List of tasks to analyze",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                }
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "batch_tasks",
        "description": "Batch tasks into ADHD-friendly focus sessions with energy matching",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs to batch",
                },
                "session_minutes": {
                    "type": "integer",
                    "default": 25,
                    "description": "Target session duration in minutes",
                },
                "energy_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                    "description": "Current energy level for matching",
                },
            },
            "required": ["task_ids"],
        },
    },
    {
        "name": "get_adhd_state",
        "description": "Get current ADHD cognitive state: energy, attention, break needs, session duration",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_task_recommendations",
        "description": "Get energy-matched task recommendations based on current cognitive state",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum recommendations to return",
                },
                "energy_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Current energy level",
                },
            },
        },
    },
    {
        "name": "record_break",
        "description": "Record a break taken - resets ADHD counters and session timers",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_agent_status",
        "description": "Get status of all AI agents in the coordination pool",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # --- New high-value tools (Phase 1.2) ---
    {
        "name": "start_session",
        "description": "Start a focused work session. Tracks time, sets energy context, returns session ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "What you're working on",
                },
                "energy_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
                "estimated_minutes": {
                    "type": "integer",
                    "default": 25,
                    "description": "Planned session duration",
                },
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "end_session",
        "description": "End current session. Saves context, logs progress, recommends next action",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "outcome": {
                    "type": "string",
                    "enum": ["completed", "paused", "blocked", "interrupted"],
                    "default": "completed",
                },
                "notes": {"type": "string", "default": ""},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "decompose_task",
        "description": "Decompose a complex task into ADHD-friendly subtasks with energy and time estimates",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_title": {"type": "string"},
                "task_description": {"type": "string"},
                "complexity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
            },
            "required": ["task_title", "task_description"],
        },
    },
    {
        "name": "log_decision",
        "description": "Log a decision with rationale to ConPort knowledge graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "rationale": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                },
            },
            "required": ["summary", "rationale"],
        },
    },
    {
        "name": "get_workflow_status",
        "description": "Get workflow status: current session, active tasks, recent decisions, break schedule",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "record_context_switch",
        "description": "Record a context switch - saves current state for later resumption",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_task": {"type": "string"},
                "to_task": {"type": "string"},
                "reason": {"type": "string", "default": ""},
            },
            "required": ["from_task", "to_task"],
        },
    },
    {
        "name": "assess_risk",
        "description": "Get risk assessment for a proposed change or task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "files_affected": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                },
                "change_type": {
                    "type": "string",
                    "enum": ["feature", "bugfix", "refactor", "config", "infrastructure"],
                    "default": "feature",
                },
            },
            "required": ["description"],
        },
    },
    # --- Internal tools (called by hooks, not shown to users) ---
    {
        "name": "record_intent",
        "description": "Internal: record user prompt intent from hooks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt_summary": {"type": "string"},
                "signals": {"type": "object"},
                "timestamp": {"type": "string"},
            },
        },
    },
    {
        "name": "track_edit",
        "description": "Internal: track file edit from PreToolUse hook",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "timestamp": {"type": "string"},
            },
        },
    },
    {
        "name": "get_visual_status",
        "description": "Get a beautifully formatted workflow status dashboard for terminal display",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ──────────────────────────────────────────────────────────────
# Tool dispatcher
# ──────────────────────────────────────────────────────────────


async def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool call and return result."""
    try:
        handler = _TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        return await handler(arguments)
    except Exception as e:
        logger.error(f"Tool call failed: {tool_name} - {e}", exc_info=True)
        return {"error": str(e)}


# ──────────────────────────────────────────────────────────────
# Tool implementations
# ──────────────────────────────────────────────────────────────


@graceful_degradation()
async def _handle_analyze_dependencies(args: Dict[str, Any]) -> Dict[str, Any]:
    tasks = args.get("tasks", [])
    if not tasks:
        return {"dependencies": [], "conflicts": [], "analyzed_count": 0}

    dependencies: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []

    for i, task in enumerate(tasks):
        task_id = task.get("id", f"task_{i}")
        text = f"{task.get('title', '')} {task.get('description', '')}".lower()

        for j, other in enumerate(tasks):
            if i == j:
                continue
            other_title = other.get("title", "").lower()
            other_id = other.get("id", f"task_{j}")
            if other_title and other_title in text:
                dependencies.append(
                    {"task_id": task_id, "depends_on": [other_id], "confidence": 0.7}
                )

    return {
        "dependencies": dependencies,
        "conflicts": conflicts,
        "analyzed_count": len(tasks),
    }


@graceful_degradation()
async def _handle_batch_tasks(args: Dict[str, Any]) -> Dict[str, Any]:
    task_ids = args.get("task_ids", [])
    session_minutes = args.get("session_minutes", 25)
    if not task_ids:
        return {"batches": []}

    batch_size = max(1, session_minutes // 10)
    batches = []
    for i in range(0, len(task_ids), batch_size):
        batch = task_ids[i : i + batch_size]
        batches.append(
            {
                "batch_id": f"batch_{i // batch_size + 1}",
                "tasks": batch,
                "estimated_minutes": len(batch) * 10,
                "break_after": True,
            }
        )

    return {
        "batches": batches,
        "total_batches": len(batches),
        "session_minutes": session_minutes,
    }


@graceful_degradation()
async def _handle_get_adhd_state(_args: Dict[str, Any]) -> Dict[str, Any]:
    state = adhd_monitor.get_adhd_state()
    # Enrich with energy_level for statusline
    mins = state.get("session_duration_minutes", 0)
    if mins < 15:
        state["energy_level"] = "high"
    elif mins < 30:
        state["energy_level"] = "medium"
    else:
        state["energy_level"] = "low"
    return state


@graceful_degradation()
async def _handle_get_task_recommendations(args: Dict[str, Any]) -> Dict[str, Any]:
    limit = args.get("limit", 5)
    energy_level = args.get("energy_level")
    adhd_state = adhd_monitor.get_adhd_state()

    recommendations: List[Dict[str, Any]] = []

    if adhd_state.get("break_needed"):
        recommendations.append(
            {
                "id": "break",
                "title": "Take a Break ☕",
                "priority": "high",
                "reason": "Session duration exceeded recommended limit",
                "estimated_minutes": 10,
            }
        )

    energy = energy_level or "medium"
    if energy == "low":
        recommendations.append(
            {
                "id": "review",
                "title": "Review Documentation",
                "priority": "low",
                "reason": "Low-energy task suitable for current state",
                "estimated_minutes": 15,
            }
        )
    elif energy == "high":
        recommendations.append(
            {
                "id": "implement",
                "title": "Feature Implementation",
                "priority": "high",
                "reason": "High-energy task for focused work",
                "estimated_minutes": 25,
            }
        )

    return {
        "recommendations": recommendations[:limit],
        "adhd_state": adhd_state,
        "energy_level": energy,
    }


@graceful_degradation()
async def _handle_record_break(_args: Dict[str, Any]) -> Dict[str, Any]:
    adhd_monitor.record_break()
    return {
        "success": True,
        "message": "Break recorded ☕ — counters reset",
        "state": adhd_monitor.get_adhd_state(),
    }


@graceful_degradation()
async def _handle_get_agent_status(_args: Dict[str, Any]) -> Dict[str, Any]:
    return agent_coordinator.get_agent_status()


# ── New tools ────────────────────────────────────────────────


@graceful_degradation()
async def _handle_start_session(args: Dict[str, Any]) -> Dict[str, Any]:
    """Start a tracked focus session."""
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc)
    est_minutes = args.get("estimated_minutes", 25)
    energy = args.get("energy_level", "medium")
    task_desc = args.get("task_description", "General work")

    from datetime import timedelta

    break_at = now + timedelta(minutes=est_minutes)

    session_data = {
        "session_id": session_id,
        "task": task_desc,
        "energy_level": energy,
        "estimated_minutes": est_minutes,
        "started_at": now.isoformat(),
        "break_at": break_at.strftime("%H:%M"),
        "status": "active",
        "files_edited": [],
        "decisions_made": 0,
    }

    _sessions[session_id] = session_data

    # Persist to temp file for hooks
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(session_data, f)
    except OSError:
        pass

    # Auto-log to ConPort (fire-and-forget)
    try:
        await auto_logger.log_session_start(session_data)
        await publish_session_event("session.started", session_data)
    except Exception:
        pass

    # Return visual banner + data
    return {
        "display": format_session_banner(session_data),
        "data": session_data,
    }


@graceful_degradation()
async def _handle_end_session(args: Dict[str, Any]) -> Dict[str, Any]:
    """End a tracked focus session."""
    session_id = args.get("session_id", "")
    outcome = args.get("outcome", "completed")
    notes = args.get("notes", "")

    session = _sessions.pop(session_id, None)
    if session is None:
        # Try loading from file
        try:
            with open(SESSION_FILE) as f:
                session = json.load(f)
        except (OSError, json.JSONDecodeError):
            session = {"session_id": session_id, "task": "Unknown"}

    # Calculate metrics
    started = session.get("started_at")
    duration_minutes = 0
    if started:
        try:
            start_dt = datetime.fromisoformat(started)
            duration_minutes = round(
                (datetime.now(timezone.utc) - start_dt).total_seconds() / 60, 1
            )
        except (ValueError, TypeError):
            pass

    metrics = {
        "duration_minutes": duration_minutes,
        "outcome": outcome,
        "files_edited": len(session.get("files_edited", [])),
        "decisions_made": session.get("decisions_made", 0),
        "notes": notes,
    }

    # Clean up session file
    try:
        os.remove(SESSION_FILE)
    except OSError:
        pass

    # Log to ConPort
    try:
        await auto_logger.log_session_end(session, metrics)
        await publish_session_event("session.ended", {"session": session, "metrics": metrics})
    except Exception:
        pass

    # Get next recommendation
    adhd_state = adhd_monitor.get_adhd_state()
    next_action = "Take a break ☕" if duration_minutes > 25 else "Continue working"

    return {
        "success": True,
        "session_id": session_id,
        "metrics": metrics,
        "next_recommendation": next_action,
        "adhd_state": adhd_state,
    }


@graceful_degradation()
async def _handle_decompose_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """Decompose a complex task into ADHD-friendly subtasks."""
    title = args.get("task_title", "Task")
    description = args.get("task_description", "")
    complexity = args.get("complexity", "medium")

    # Estimate based on complexity
    base_minutes = {"low": 10, "medium": 20, "high": 35}.get(complexity, 20)
    subtask_count = {"low": 2, "medium": 3, "high": 5}.get(complexity, 3)

    # Generate subtasks with ADHD metadata
    subtasks: List[Dict[str, Any]] = []
    for i in range(subtask_count):
        is_first = i == 0
        is_last = i == subtask_count - 1
        est = base_minutes if is_first else max(10, base_minutes - 5)
        energy_req = "high" if is_first else ("low" if is_last else "medium")
        cognitive = 0.3 + (0.2 * i) if i < 3 else 0.5

        subtasks.append(
            {
                "title": f"Step {i + 1}: {'Setup' if is_first else 'Implement' if not is_last else 'Verify'} - {title[:30]}",
                "estimated_minutes": est,
                "energy": energy_req,
                "cognitive_load": round(cognitive, 1),
                "break_after": i == subtask_count // 2,  # Break at midpoint
                "order": i + 1,
            }
        )

    total_minutes = sum(s["estimated_minutes"] for s in subtasks)

    decomposition = {
        "parent_task": title,
        "subtasks": subtasks,
        "total_estimated_minutes": total_minutes,
        "complexity": complexity,
    }

    # Log decomposition to ConPort
    try:
        await auto_logger.log_decomposition(title, len(subtasks), total_minutes)
        await publish_task_event("task.decomposed", decomposition)
    except Exception:
        pass

    return {
        "display": format_task_decomposition(decomposition),
        "data": decomposition,
    }


@graceful_degradation()
async def _handle_log_decision(args: Dict[str, Any]) -> Dict[str, Any]:
    """Log a decision to ConPort."""
    summary = args.get("summary", "")
    rationale = args.get("rationale", "")
    tags = args.get("tags", [])

    decision_id = str(uuid.uuid4())[:8]
    decision = {
        "decision_id": decision_id,
        "summary": summary,
        "rationale": rationale,
        "tags": tags,
        "timestamp": _now_iso(),
    }

    # Try ConPort
    try:
        await auto_logger.log_decision_to_conport(summary, rationale, tags)
    except Exception:
        pass

    # Track in active session
    for s in _sessions.values():
        s["decisions_made"] = s.get("decisions_made", 0) + 1

    return {"success": True, "decision": decision}


@graceful_degradation()
async def _handle_get_workflow_status(_args: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate workflow status for dashboard display."""
    adhd_state = adhd_monitor.get_adhd_state()

    # Find active session
    active_session: Dict[str, Any] = {}
    for sid, s in _sessions.items():
        if s.get("status") == "active":
            started = s.get("started_at")
            elapsed = 0
            if started:
                try:
                    start_dt = datetime.fromisoformat(started)
                    elapsed = round(
                        (datetime.now(timezone.utc) - start_dt).total_seconds() / 60, 1
                    )
                except (ValueError, TypeError):
                    pass
            active_session = {
                "session_id": sid,
                "task": s.get("task", ""),
                "elapsed_minutes": elapsed,
                "estimated_minutes": s.get("estimated_minutes", 25),
                "energy_level": s.get("energy_level", "medium"),
            }
            break

    status_data = {
        "session": active_session,
        "adhd_state": adhd_state,
        "active_tasks": [],  # Would come from task store
        "recent_decisions": [],  # Would come from ConPort
        "context_switches": len(_context_switches),
        "files_edited": len(_file_edits),
    }

    return {
        "display": format_workflow_status(status_data),
        "data": status_data,
    }


@graceful_degradation()
async def _handle_record_context_switch(args: Dict[str, Any]) -> Dict[str, Any]:
    """Record a context switch for ADHD tracking."""
    from_task = args.get("from_task", "")
    to_task = args.get("to_task", "")
    reason = args.get("reason", "")

    adhd_monitor.record_context_switch()

    switch_record = {
        "from_task": from_task,
        "to_task": to_task,
        "reason": reason,
        "timestamp": _now_iso(),
    }
    _context_switches.append(switch_record)

    # Estimate reorientation cost
    reorientation_min = 3 if len(_context_switches) < 3 else 5

    # Log to ConPort
    try:
        await auto_logger.log_context_switch(from_task, to_task)
    except Exception:
        pass

    return {
        "display": format_context_switch(from_task, to_task, reorientation_min),
        "data": {
            "switch": switch_record,
            "total_switches": len(_context_switches),
            "estimated_reorientation_minutes": reorientation_min,
        },
    }


@graceful_degradation()
async def _handle_assess_risk(args: Dict[str, Any]) -> Dict[str, Any]:
    """Assess risk of a proposed change."""
    description = args.get("description", "")
    files_affected = args.get("files_affected", [])
    change_type = args.get("change_type", "feature")

    # Simple heuristic risk assessment (ML module can enhance later)
    risk_score = 0.2  # Base risk
    risk_factors: List[str] = []

    # File count risk
    if len(files_affected) > 10:
        risk_score += 0.3
        risk_factors.append(f"High blast radius: {len(files_affected)} files")
    elif len(files_affected) > 5:
        risk_score += 0.15
        risk_factors.append(f"Moderate blast radius: {len(files_affected)} files")

    # Change type risk
    type_risk = {
        "infrastructure": 0.3,
        "refactor": 0.2,
        "feature": 0.1,
        "bugfix": 0.05,
        "config": 0.15,
    }
    risk_score += type_risk.get(change_type, 0.1)
    if change_type == "infrastructure":
        risk_factors.append("Infrastructure change - affects system stability")

    # Keyword risk signals
    high_risk_keywords = ["database", "migration", "auth", "payment", "deploy", "delete"]
    for kw in high_risk_keywords:
        if kw in description.lower():
            risk_score += 0.1
            risk_factors.append(f"Sensitive area: {kw}")
            break

    risk_score = min(1.0, risk_score)
    risk_level = (
        "low"
        if risk_score < 0.3
        else "medium"
        if risk_score < 0.6
        else "high"
        if risk_score < 0.8
        else "critical"
    )

    assessment = {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "change_type": change_type,
        "files_affected": len(files_affected),
        "recommendation": "Proceed with caution"
        if risk_level in ("medium", "high")
        else "Safe to proceed"
        if risk_level == "low"
        else "Review with team before proceeding",
    }

    return {
        "display": format_risk_assessment(assessment),
        "data": assessment,
    }


# ── Internal tools (hook-facing) ─────────────────────────────


@graceful_degradation()
async def _handle_record_intent(args: Dict[str, Any]) -> Dict[str, Any]:
    """Record user intent from prompt_analyzer hook."""
    # Store for analytics, minimal processing
    logger.debug(f"Intent recorded: {args.get('prompt_summary', '')[:50]}")
    return {"success": True}


@graceful_degradation()
async def _handle_track_edit(args: Dict[str, Any]) -> Dict[str, Any]:
    """Track file edit from PreToolUse hook."""
    file_path = args.get("file_path", "")
    if file_path:
        _file_edits.append(
            {"file_path": file_path, "timestamp": args.get("timestamp", _now_iso())}
        )
        # Also track in active session
        for s in _sessions.values():
            if s.get("status") == "active":
                files = s.setdefault("files_edited", [])
                if file_path not in files:
                    files.append(file_path)
    return {"success": True}


async def _handle_get_visual_status(_args: Dict[str, Any]) -> Dict[str, Any]:
    """Return visual status dashboard."""
    return await _handle_get_workflow_status(_args)


# ──────────────────────────────────────────────────────────────
# Tool handler registry
# ──────────────────────────────────────────────────────────────

_TOOL_HANDLERS: Dict[str, Any] = {
    "analyze_dependencies": _handle_analyze_dependencies,
    "batch_tasks": _handle_batch_tasks,
    "get_adhd_state": _handle_get_adhd_state,
    "get_task_recommendations": _handle_get_task_recommendations,
    "record_break": _handle_record_break,
    "get_agent_status": _handle_get_agent_status,
    "start_session": _handle_start_session,
    "end_session": _handle_end_session,
    "decompose_task": _handle_decompose_task,
    "log_decision": _handle_log_decision,
    "get_workflow_status": _handle_get_workflow_status,
    "record_context_switch": _handle_record_context_switch,
    "assess_risk": _handle_assess_risk,
    "record_intent": _handle_record_intent,
    "track_edit": _handle_track_edit,
    "get_visual_status": _handle_get_visual_status,
}
