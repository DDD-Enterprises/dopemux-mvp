#!/usr/bin/env python3
"""Simple Leantime + ADHD Engine integration smoke script."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from config import ADHD_API_KEY, ADHD_ENGINE_URL, LEANTIME_API_KEY, LEANTIME_URL, USER_ID


LEANTIME_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LEANTIME_API_KEY}",
}

ADHD_HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": ADHD_API_KEY,
}


def create_leantime_task(title: str, description: str) -> Optional[str]:
    """Create a task in Leantime and return the created task id."""
    payload = {
        "title": title,
        "description": description,
        "status": "open",
        "priority": 1,
        "due_date": (datetime.utcnow() + timedelta(days=1)).date().isoformat(),
    }

    response = requests.post(
        f"{LEANTIME_URL}/api/tasks",
        headers=LEANTIME_HEADERS,
        data=json.dumps(payload),
        timeout=20,
    )

    if response.status_code in (200, 201):
        data = response.json()
        task_id = data.get("id")
        print(f"Created task in Leantime: {task_id}")
        return task_id

    print(f"Leantime task creation failed: {response.status_code} - {response.text}")
    return None


def assess_task_with_adhd_engine(
    task_description: str,
    estimated_hours: float = 2.0,
    technologies: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Request ADHD assessment for a task."""
    payload = {
        "task_description": task_description,
        "estimated_hours": estimated_hours,
        "technologies": technologies or ["python", "docker"],
        "dependencies": ["integration"],
    }

    response = requests.post(
        f"{ADHD_ENGINE_URL}/api/v1/assess-task",
        headers=ADHD_HEADERS,
        data=json.dumps(payload),
        timeout=20,
    )

    if response.status_code == 200:
        data = response.json()
        print("ADHD assessment received")
        return data

    print(f"ADHD Engine assessment failed: {response.status_code} - {response.text}")
    return None


def log_activity_to_engine(event_type: str, event_data: Dict[str, Any]) -> None:
    """Log activity to ADHD Engine."""
    payload = {"event_type": event_type, "event_data": event_data}

    response = requests.put(
        f"{ADHD_ENGINE_URL}/api/v1/activity/{USER_ID}",
        headers=ADHD_HEADERS,
        data=json.dumps(payload),
        timeout=20,
    )

    if response.status_code == 200:
        print("Activity logged to ADHD Engine")
        return

    print(f"Activity logging failed: {response.status_code}")


if __name__ == "__main__":
    print("Dopemux ADHD integration smoke run")
    print("=" * 40)

    title = "Integration Smoke Task"
    description = "Verify Leantime and ADHD Engine integration path."
    task_id = create_leantime_task(title, description)

    if not task_id:
        raise SystemExit(1)

    assessment = assess_task_with_adhd_engine(
        description,
        estimated_hours=1.5,
        technologies=["python", "api", "integration"],
    )

    if not assessment:
        raise SystemExit(1)

    log_activity_to_engine(
        "task_complete",
        {
            "task_id": task_id,
            "duration_minutes": 90,
            "cognitive_load": assessment.get("cognitive_load"),
        },
    )
    print("Integration smoke run complete.")
