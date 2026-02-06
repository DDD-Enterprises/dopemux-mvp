from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import random
from datetime import datetime

app = FastAPI(title="Ultra UI Dashboard Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CognitiveState(BaseModel):
    energy: float
    attention: float
    load: float
    status: str
    recommendation: str
    prediction: Optional[float] = None

class DashboardData(BaseModel):
    cognitive_state: CognitiveState
    team_members: List[dict]
    tasks: List[dict]

# Simulated data (replace with real MCP calls)
@app.get("/api/cognitive-state")
async def get_cognitive_state():
    # Simulate real-time cognitive data from ADHD Engine
    import random
    energy = round(random.uniform(0.4, 0.9), 2)
    attention = round(random.uniform(0.5, 0.8), 2)
    load = round(random.uniform(0.3, 0.7), 2)

    status = "optimal" if load < 0.6 else "high" if load < 0.8 else "critical"
    recommendation = "Continue current work patterns" if status == "optimal" else "Consider task simplification"

    return {
        "cognitive_state": {
            "energy": energy,
            "attention": attention,
            "load": load,
            "status": status,
            "recommendation": recommendation
        }
    }

@app.get("/api/team-members")
async def get_team_members():
    return [
        {
            "id": "1",
            "name": "Alice Johnson",
            "role": "Lead Developer",
            "energy": round(random.uniform(0.5, 0.9), 2),
            "attention": round(random.uniform(0.6, 0.8), 2),
            "load": round(random.uniform(0.3, 0.7), 2),
            "status": "optimal" if random.random() < 0.7 else "high",
            "currentTask": "ML prediction pipeline"
        },
        {
            "id": "2",
            "name": "Bob Smith",
            "role": "Frontend Engineer",
            "energy": round(random.uniform(0.4, 0.8), 2),
            "attention": round(random.uniform(0.5, 0.7), 2),
            "load": round(random.uniform(0.4, 0.8), 2),
            "status": "high" if random.random() < 0.5 else "optimal",
            "currentTask": "UI dashboard components"
        },
        {
            "id": "3",
            "name": "Carol Davis",
            "role": "DevOps Engineer",
            "energy": round(random.uniform(0.6, 0.9), 2),
            "attention": round(random.uniform(0.7, 0.9), 2),
            "load": round(random.uniform(0.2, 0.5), 2),
            "status": "low" if random.random() < 0.6 else "optimal",
            "currentTask": "Kubernetes manifests"
        },
        {
            "id": "4",
            "name": "David Wilson",
            "role": "Data Engineer",
            "energy": round(random.uniform(0.3, 0.6), 2),
            "attention": round(random.uniform(0.4, 0.6), 2),
            "load": round(random.uniform(0.6, 0.9), 2),
            "status": "critical" if random.random() < 0.4 else "high",
            "currentTask": "ETL pipeline setup"
        }
    ]

@app.get("/api/tasks")
async def get_tasks():
    return [
        {
            "id": "1",
            "title": "Implement LSTM cognitive predictor",
            "complexity": 0.8,
            "estimatedMinutes": 120,
            "status": "in_progress",
            "energyRequired": "high"
        },
        {
            "id": "2",
            "title": "Create UI dashboard components",
            "complexity": 0.6,
            "estimatedMinutes": 90,
            "status": "pending",
            "energyRequired": "medium"
        },
        {
            "id": "3",
            "title": "Write unit tests",
            "complexity": 0.4,
            "estimatedMinutes": 45,
            "status": "pending",
            "energyRequired": "low"
        },
        {
            "id": "4",
            "title": "Deploy to staging",
            "complexity": 0.5,
            "estimatedMinutes": 60,
            "status": "pending",
            "energyRequired": "medium"
        }
    ]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Ultra UI Dashboard Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
