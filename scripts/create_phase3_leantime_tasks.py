#!/usr/bin/env python3
"""
Create Phase 3 tasks in Leantime project "dopemux dev"

Requires:
- LEANTIME_URL=http://localhost:8080
- LEANTIME_API_KEY=lt_S0wuTCITdeHneelmbiprocJAxzaJdirs_dGON1EuvZTXb8mS8Cp3L30P8hc9ykbwe
- PROJECT_ID=1 (assumed for "dopemux dev")

Creates all Phase 3 tasks from ConPort decisions 372-376 and tasks 323-332
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import aiohttp
import json
import os
from datetime import datetime

LEANTIME_URL = os.getenv("LEANTIME_URL", "http://localhost:8080")
API_KEY = os.getenv("LEANTIME_API_KEY", "lt_S0wuTCITdeHneelmbiprocJAxzaJdirs_dGON1EuvZTXb8mS8Cp3L30P8hc9ykbwe")
PROJECT_ID = os.getenv("PROJECT_ID", "1")  # Assumed ID for "dopemux dev"

# Phase 3 Tasks to create
PHASE3_TASKS = [
    {
        "headline": "Phase 3.1: ML-Powered Predictions - Implement cognitive data collection pipeline",
        "description": "Build data pipeline to collect cognitive metrics from ConPort for ML model training",
        "priority": "3",  # Medium
        "status": "3"  # Open
    },
    {
        "headline": "Phase 3.2: ML Model Development - LSTM neural networks for cognitive load forecasting",
        "description": "Implement LSTM models to predict cognitive load 15-30 minutes in advance",
        "priority": "1",  # High
        "status": "3"
    },
    {
        "headline": "Phase 3.3: ML Production Integration - Deploy real-time prediction API endpoints",
        "description": "Deploy ML prediction endpoints for proactive ADHD accommodations",
        "priority": "1",
        "status": "3"
    },
    {
        "headline": "Phase 3.1: Team Data Architecture - Multi-user cognitive state aggregation",
        "description": "Implement team cognitive dashboards and load balancing algorithms",
        "priority": "2",
        "status": "3"
    },
    {
        "headline": "Phase 3.2: Collaborative Features - Team dashboard with real-time visualization",
        "description": "Build synchronous work sessions and team cognitive state awareness",
        "priority": "2",
        "status": "3"
    },
    {
        "headline": "Phase 3.1: Infrastructure Foundation - Kubernetes manifests for all services",
        "description": "Create K8s manifests and Helm charts for production deployment",
        "priority": "3",
        "status": "3"
    },
    {
        "headline": "Phase 3.2: Monitoring & Observability - Prometheus + Grafana for cognitive metrics",
        "description": "Implement comprehensive monitoring stack for all services",
        "priority": "2",
        "status": "3"
    },
    {
        "headline": "Phase 3.1: Core Dashboard - React/TypeScript frontend architecture",
        "description": "Implement real-time cognitive state visualization interface",
        "priority": "1",
        "status": "3"
    },
    {
        "headline": "Phase 3.2: Advanced UI Features - Team collaboration interface",
        "description": "Add customizable dashboards and team coordination features",
        "priority": "2",
        "status": "3"
    }
]

async def create_task(session, task_data):
    """Create a single task in Leantime."""
    payload = {
        "jsonrpc": "2.0",
        "method": "addTicket",
        "params": {
            "headline": task_data["headline"],
            "description": task_data["description"],
            "projectId": PROJECT_ID,
            "status": task_data["status"],
            "priority": task_data["priority"]
        },
        "id": len(task_data)
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    try:
        async with session.post(f"{LEANTIME_URL}/api/jsonrpc",
                              json=payload,
                              headers=headers) as response:
            result = await response.json()

            if "result" in result:
                logger.info(f"✅ Created task '{task_data['headline']}' (ID: {result['result'].get('id')})")
                return result['result'].get('id')
            else:
                logger.error(f"❌ Failed to create task '{task_data['headline']}': {result.get('error', 'Unknown error')}")
                return None
    except Exception as e:
        logger.error(f"❌ Error creating task '{task_data['headline']}': {e}")
        return None

async def main():
    """Create all Phase 3 tasks in Leantime."""
    logger.info(f"Creating {len(PHASE3_TASKS)} Phase 3 tasks in Leantime project ID {PROJECT_ID}")
    logger.info(f"Using URL: {LEANTIME_URL}")

    async with aiohttp.ClientSession() as session:
        created_count = 0
        for task_data in PHASE3_TASKS:
            task_id = await create_task(session, task_data)
            if task_id:
                created_count += 1
            await asyncio.sleep(0.5)  # Rate limiting

        logger.info(f"\n🎉 Phase 3 setup complete! Created {created_count}/{len(PHASE3_TASKS)} tasks")
        logger.info("Tasks now available in Leantime 'dopemux dev' project for execution")

if __name__ == "__main__":
    asyncio.run(main())
