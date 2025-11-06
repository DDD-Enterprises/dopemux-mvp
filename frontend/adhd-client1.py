#!/usr/bin/env python3
"""
Simple Python client for Dopemux ADHD Engine integration.

Demonstrates:
- Creating a task in Leantime
- Assessing the task with ADHD Engine
- Logging activity back to the Engine
- Displaying ADHD recommendations
"""

import requests
import json
from datetime import datetime
from config import LEANTIME_URL, LEANTIME_API_KEY, ADHD_ENGINE_URL, ADHD_API_KEY, USER_ID

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LEANTIME_API_KEY}",
    "X-API-Key": ADHD_API_KEY
}

def create_leantime_task(title, description):
    """Create a task in Leantime."""
    payload = {
        "title": title,
        "description": description,
        "status": "open",
        "priority": 1,
        "due_date": "2025-11-06"
    }
    response = requests.post(
        f"{LEANTIME_URL}/api/v1/tasks",
        headers=headers,
        data=json.dumps(payload)
    )
    if response.status_code == 201 or response.status_code == 200:
        data = response.json()
        print(f"✅ Task created in Leantime: ID {data.get('id', 'unknown')}")
        return data.get('id')
    else:
        print(f"❌ Leantime task creation failed: {response.status_code} - {response.text}")
        return None

def assess_task_with_adhd_engine(task_description, estimated_hours=2.0, technologies=["python", "docker"]):
    """Assess task with ADHD Engine."""
    payload = {
        "task_description": task_description,
        "estimated_hours": estimated_hours,
        "technologies": technologies,
        "dependencies": ["integration"]
    }
    response = requests.post(
        f"{ADHD_ENGINE_URL}/api/v1/assess-task",
        headers={"X-API-Key": ADHD_API_KEY, "Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ ADHD Assessment:")
        print(f"   • Complexity Score: {data['complexity_score']:.2f}")
        print(f"   • Cognitive Load: {data['cognitive_load']}")
        print(f"   • Recommended Chunks: {data['recommended_chunks']}")
        print(f"   • Break Frequency: {data['break_frequency']}")
        print(f"   • Energy Requirement: {data['energy_requirement']}")
        print(f"   • Accommodations: {', '.join([rec['accommodation_type'] for rec in data['accommodations']])}")
        return data
    else:
        print(f"❌ ADHD Engine assessment failed: {response.status_code} - {response.text}")
        return None

def log_activity_to_engine(event_type, event_data):
    """Log activity back to ADHD Engine."""
    payload = {
        "event_type": event_type,
        "event_data": event_data
    }
    response = requests.put(
        f"{ADHD_ENGINE_URL}/api/v1/activity/{USER_ID}",
        headers={"X-API-Key": ADHD_API_KEY, "Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    if response.status_code == 200:
        print(f"✅ Activity logged: {response.json().get('analysis', {}).get('pattern_matched', 'unknown')}")
    else:
        print(f"⚠️ Activity logging failed: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Dopemux ADHD Integration Test")
    print("=" * 40)

    # Step 1: Create task in Leantime
    task_title = "Frontend Integration Test Task"
    task_desc = "Create a frontend client for the ADHD Engine integration, demonstrating task creation in Leantime and assessment with ADHD recommendations."
    task_id = create_leantime_task(task_title, task_desc)

    if task_id:
        # Step 2: Assess with ADHD Engine
        assessment = assess_task_with_adhd_engine(task_desc, estimated_hours=1.5, technologies=["python", "api", "integration"])

        if assessment:
            # Step 3: Log activity
            log_activity_to_engine("task_complete", {
                "task_id": task_id,
                "duration_minutes": 90,
                "cognitive_load": assessment['cognitive_load']
            })

    print("\n✅ Integration test complete! Check the outputs above.")
