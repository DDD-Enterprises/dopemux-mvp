from __future__ import annotations

import asyncio
import copy
import json
import os
import concurrent.futures
import functools
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class CognitiveState(BaseModel):
    energy: float = Field(ge=0.0, le=1.0)
    attention: float = Field(ge=0.0, le=1.0)
    load: float = Field(ge=0.0, le=1.0)
    status: Literal["low", "optimal", "high", "critical"]
    recommendation: str
    prediction: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class DashboardData(BaseModel):
    cognitive_state: CognitiveState
    team_members: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    sources: Dict[str, str]
    sampled_at: str


DashboardData.model_rebuild()


FALLBACK_COGNITIVE_STATE = CognitiveState(
    energy=0.65,
    attention=0.62,
    load=0.48,
    status="optimal",
    recommendation="Continue current work patterns with a 5-minute break in ~25 minutes.",
)

FALLBACK_TEAM_MEMBERS: List[Dict[str, Any]] = [
    {
        "id": "1",
        "name": "Alice Johnson",
        "role": "Lead Developer",
        "energy": 0.82,
        "attention": 0.76,
        "load": 0.42,
        "status": "optimal",
        "currentTask": "ML prediction pipeline hardening",
    },
    {
        "id": "2",
        "name": "Bob Smith",
        "role": "Frontend Engineer",
        "energy": 0.58,
        "attention": 0.61,
        "load": 0.67,
        "status": "high",
        "currentTask": "Dashboard interaction flows",
    },
    {
        "id": "3",
        "name": "Carol Davis",
        "role": "DevOps Engineer",
        "energy": 0.75,
        "attention": 0.74,
        "load": 0.36,
        "status": "low",
        "currentTask": "Compose contract verification",
    },
    {
        "id": "4",
        "name": "David Wilson",
        "role": "Data Engineer",
        "energy": 0.41,
        "attention": 0.47,
        "load": 0.83,
        "status": "critical",
        "currentTask": "ETL retry tuning",
    },
]

FALLBACK_TASKS: List[Dict[str, Any]] = [
    {
        "id": "task-1",
        "title": "Implement LSTM cognitive predictor",
        "complexity": 0.8,
        "estimatedMinutes": 120,
        "status": "in_progress",
        "energyRequired": "high",
    },
    {
        "id": "task-2",
        "title": "Create UI dashboard components",
        "complexity": 0.6,
        "estimatedMinutes": 90,
        "status": "pending",
        "energyRequired": "medium",
    },
    {
        "id": "task-3",
        "title": "Write contract tests",
        "complexity": 0.4,
        "estimatedMinutes": 45,
        "status": "pending",
        "energyRequired": "low",
    },
    {
        "id": "task-4",
        "title": "Deploy to staging",
        "complexity": 0.5,
        "estimatedMinutes": 60,
        "status": "pending",
        "energyRequired": "medium",
    },
]


app = FastAPI(title="Ultra UI Dashboard Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dedicated thread pool for blocking HTTP operations to avoid
# exhausting the default asyncio executor.
_http_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=50,
    thread_name_prefix="http_worker",
)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _status_from_load(load: float) -> Literal["low", "optimal", "high", "critical"]:
    if load < 0.3:
        return "low"
    if load < 0.6:
        return "optimal"
    if load < 0.8:
        return "high"
    return "critical"


def _recommendation_for_status(status: str) -> str:
    if status == "critical":
        return (
            "Mandatory break now; switch to a low-complexity recovery task afterward."
        )
    if status == "high":
        return (
            "Reduce scope, batch interruptions, and finish one task before switching."
        )
    if status == "low":
        return (
            "Good window for deep, complex work. Protect focus for the next 45 minutes."
        )
    return "Continue current work patterns with short, planned breaks."


def _energy_level_to_score(level: str) -> float:
    mapping = {
        "very_low": 0.15,
        "low": 0.3,
        "medium": 0.55,
        "high": 0.8,
        "hyperfocus": 0.92,
    }
    return mapping.get(level.lower(), 0.55)


def _attention_state_to_score(state: str) -> float:
    mapping = {
        "scattered": 0.25,
        "transitioning": 0.45,
        "focused": 0.75,
        "hyperfocused": 0.92,
        "overwhelmed": 0.15,
    }
    return mapping.get(state.lower(), 0.6)


def _fetch_json_sync(
    url: str, headers: Optional[Dict[str, str]] = None, timeout_seconds: float = 2.0
) -> Dict[str, Any]:
    request = Request(url=url, headers=headers or {}, method="GET")
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        payload = response.read().decode("utf-8")
    return json.loads(payload)


async def _fetch_json(
    url: str, headers: Optional[Dict[str, str]] = None, timeout_seconds: float = 2.0
) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _http_executor,
        functools.partial(
            _fetch_json_sync,
            url=url,
            headers=headers,
            timeout_seconds=timeout_seconds,
        ),
    )


def _normalize_task(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    task_id = str(task.get("id") or task.get("task_id") or "").strip()
    title = str(task.get("title") or task.get("name") or "").strip()
    if not task_id or not title:
        return None

    raw_complexity = task.get("complexity")
    if raw_complexity is None:
        raw_complexity = task.get("complexity_score")
    if raw_complexity is None:
        raw_complexity = 0.5
    complexity = _clamp(float(raw_complexity))

    estimated_minutes = task.get("estimatedMinutes")
    if estimated_minutes is None:
        estimated_minutes = task.get("estimated_minutes")
    if estimated_minutes is None:
        estimated_hours = task.get("estimated_hours")
        estimated_minutes = (
            int(float(estimated_hours) * 60)
            if estimated_hours is not None
            else int(30 + (complexity * 90))
        )

    status = str(task.get("status", "pending")).lower()
    status_map = {
        "todo": "pending",
        "pending": "pending",
        "in_progress": "in_progress",
        "in-progress": "in_progress",
        "active": "in_progress",
        "done": "completed",
        "complete": "completed",
        "completed": "completed",
    }
    normalized_status = status_map.get(status, "pending")

    energy_required = task.get("energyRequired") or task.get("energy_required")
    if not energy_required:
        energy_required = (
            "high" if complexity >= 0.7 else "medium" if complexity >= 0.45 else "low"
        )

    return {
        "id": task_id,
        "title": title,
        "complexity": round(complexity, 2),
        "estimatedMinutes": int(estimated_minutes),
        "status": normalized_status,
        "energyRequired": str(energy_required),
    }


async def _load_live_cognitive_state(user_id: str) -> Optional[CognitiveState]:
    base_url = os.getenv("ADHD_ENGINE_URL", "http://localhost:8095").rstrip("/")
    api_key = os.getenv("ADHD_ENGINE_API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}

    energy_url = f"{base_url}/api/v1/energy-level/{user_id}"
    attention_url = f"{base_url}/api/v1/attention-state/{user_id}"

    try:
        energy_payload, attention_payload = await asyncio.gather(
            _fetch_json(energy_url, headers=headers, timeout_seconds=1.5),
            _fetch_json(attention_url, headers=headers, timeout_seconds=1.5),
        )
    except (URLError, HTTPError, TimeoutError, ValueError, OSError):
        return None

    energy_score = _energy_level_to_score(
        str(energy_payload.get("energy_level", "medium"))
    )
    attention_state = str(attention_payload.get("attention_state", "focused"))
    attention_score = _attention_state_to_score(attention_state)

    load = 1.0 - ((energy_score + attention_score) / 2.0)
    if attention_state.lower() in {"scattered", "overwhelmed"}:
        load += 0.15
    load = _clamp(load)

    status = _status_from_load(load)

    return CognitiveState(
        energy=round(energy_score, 2),
        attention=round(attention_score, 2),
        load=round(load, 2),
        status=status,
        recommendation=_recommendation_for_status(status),
    )


async def _load_live_tasks(limit: int) -> Optional[List[Dict[str, Any]]]:
    base_url = os.getenv("TASK_ORCHESTRATOR_URL", "http://localhost:3017").rstrip("/")
    tasks_url = f"{base_url}/tasks?limit={limit}"

    try:
        payload = await _fetch_json(tasks_url, timeout_seconds=1.5)
    except (URLError, HTTPError, TimeoutError, ValueError, OSError):
        return None

    if not isinstance(payload, list):
        return None

    normalized: List[Dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        parsed = _normalize_task(item)
        if parsed is not None:
            normalized.append(parsed)

    return normalized if normalized else None


def _fallback_team_members() -> List[Dict[str, Any]]:
    return copy.deepcopy(FALLBACK_TEAM_MEMBERS)


def _fallback_tasks(limit: int) -> List[Dict[str, Any]]:
    return copy.deepcopy(FALLBACK_TASKS[:limit])


@app.get("/")
async def service_info() -> Dict[str, Any]:
    return {
        "service": "Ultra UI Dashboard Backend",
        "version": "1.1.0",
        "status": "ready",
        "endpoints": [
            "/health",
            "/api/cognitive-state",
            "/api/team-members",
            "/api/tasks",
            "/api/dashboard",
        ],
    }


@app.get("/api/cognitive-state")
async def get_cognitive_state(
    user_id: str = Query(default="default", min_length=1),
) -> Dict[str, Any]:
    live_state = await _load_live_cognitive_state(user_id=user_id)
    if live_state is None:
        state = FALLBACK_COGNITIVE_STATE
        source = "fallback"
    else:
        state = live_state
        source = "adhd-engine"

    return {
        "cognitive_state": state.model_dump(),
        "source": source,
        "sampled_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/team-members")
async def get_team_members() -> List[Dict[str, Any]]:
    # Team data remains deterministic fallback until dedicated people-state service is wired.
    return _fallback_team_members()


@app.get("/api/tasks")
async def get_tasks(
    limit: int = Query(default=4, ge=1, le=20),
) -> List[Dict[str, Any]]:
    live_tasks = await _load_live_tasks(limit=limit)
    if live_tasks is not None:
        return live_tasks[:limit]
    return _fallback_tasks(limit=limit)


@app.get("/api/dashboard")
async def get_dashboard_snapshot(
    user_id: str = Query(default="default", min_length=1),
    limit: int = Query(default=4, ge=1, le=20),
) -> DashboardData:
    cognitive_payload = await get_cognitive_state(user_id=user_id)
    tasks = await get_tasks(limit=limit)
    team_members = await get_team_members()

    return DashboardData(
        cognitive_state=CognitiveState(**cognitive_payload["cognitive_state"]),
        team_members=team_members,
        tasks=tasks,
        sources={
            "cognitive_state": str(cognitive_payload["source"]),
            "tasks": (
                "task-orchestrator"
                if tasks
                and tasks[0]["id"] not in {"task-1", "task-2", "task-3", "task-4"}
                else "fallback"
            ),
            "team_members": "fallback",
        },
        sampled_at=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Ultra UI Dashboard Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrations": {
            "adhd_engine_url": os.getenv("ADHD_ENGINE_URL", "http://localhost:8095"),
            "task_orchestrator_url": os.getenv(
                "TASK_ORCHESTRATOR_URL", "http://localhost:3017"
            ),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("DASHBOARD_BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("DASHBOARD_BACKEND_PORT", "3001")),
        reload=False,
    )
