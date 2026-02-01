"""Main application entry point for the Genetic Coding Agent system."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import AgentConfig
from .vanilla.vanilla_agent import VanillaAgent
from .genetic.genetic_agent import GeneticAgent

# Create FastAPI app
app = FastAPI(
    title="Genetic Coding Agent",
    description="Dual-agent system for automated code repair with GP enhancements",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances
vanilla_agent = None
genetic_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    global vanilla_agent, genetic_agent

    config = AgentConfig()
    vanilla_agent = VanillaAgent(config)
    genetic_agent = GeneticAgent(config)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Genetic Coding Agent API", "version": "0.2.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.2.0",
        "agents": {
            "vanilla": vanilla_agent is not None,
            "genetic": genetic_agent is not None
        }
    }


@app.post("/repair/vanilla")
async def repair_with_vanilla(task: dict):
    """Repair code using the vanilla agent."""
    if not vanilla_agent:
        return {"error": "Vanilla agent not initialized"}

    result = await vanilla_agent.process_task(task)
    return result


@app.post("/repair/genetic")
async def repair_with_genetic(task: dict):
    """Repair code using the genetic agent with GP enhancements."""
    if not genetic_agent:
        return {"error": "Genetic agent not initialized"}

    result = await genetic_agent.process_task(task)
    return result


@app.post("/repair/auto")
async def repair_auto(task: dict):
    """Automatically select the best agent for repair (genetic preferred)."""
    if genetic_agent:
        result = await genetic_agent.process_task(task)
        result["agent_used"] = "genetic"
        return result
    elif vanilla_agent:
        result = await vanilla_agent.process_task(task)
        result["agent_used"] = "vanilla"
        return result
    else:
        return {"error": "No agents available"}


@app.get("/status")
async def get_status():
    """Get system status."""
    status_data = {
        "system": "healthy",
        "version": "0.2.0"
    }

    if vanilla_agent:
        status_data["vanilla_agent"] = vanilla_agent.get_status()
    else:
        status_data["vanilla_agent"] = {"error": "Agent not initialized"}

    if genetic_agent:
        status_data["genetic_agent"] = genetic_agent.get_status()
    else:
        status_data["genetic_agent"] = {"error": "Agent not initialized"}

    return status_data


@app.get("/dashboard")
async def get_dashboard():
    """Get performance dashboard data."""
    dashboard = {
        "version": "0.2.0",
        "timestamp": "2025-11-07T22:40:00Z",
        "summary": {
            "total_repairs_attempted": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0
        },
        "operator_performance": {},
        "recent_activity": []
    }

    try:
        if genetic_agent and hasattr(genetic_agent, 'memory_adapter'):
            # Get operator performance
            operator_patterns = await genetic_agent.memory_adapter.get_operator_success_patterns(limit=10)
            dashboard["operator_performance"] = operator_patterns

            # Get recent activity
            failure_patterns = await genetic_agent.memory_adapter.get_failure_patterns(limit=5)
            dashboard["recent_activity"] = [
                {
                    "type": "failure_pattern",
                    "signals": pattern.get("signals", []),
                    "timestamp": pattern.get("timestamp", "")
                }
                for pattern in failure_patterns
            ]

    except Exception as e:
        dashboard["error"] = f"Could not load dashboard data: {e}"

    return dashboard


@app.get("/dashboard/operators")
async def get_operator_performance():
    """Get detailed operator performance statistics."""
    if not genetic_agent or not hasattr(genetic_agent, 'memory_adapter'):
        return {"error": "Genetic agent or memory adapter not available"}

    try:
        patterns = await genetic_agent.memory_adapter.get_operator_success_patterns(limit=20)
        return {
            "operators": patterns,
            "total_operators": len(patterns),
            "top_performer": max(patterns.keys(), key=lambda k: patterns[k].get("avg_fitness", 0)) if patterns else None
        }
    except Exception as e:
        return {"error": f"Could not retrieve operator performance: {e}"}


@app.post("/reset/{agent_type}")
async def reset_agent(agent_type: str):
    """Reset an agent (for testing/admin purposes)."""
    global vanilla_agent, genetic_agent

    if agent_type == "vanilla" and vanilla_agent:
        vanilla_agent.reset_circuit_breaker()
        return {"message": "Vanilla agent reset successfully"}
    elif agent_type == "genetic" and genetic_agent:
        genetic_agent.reset_circuit_breaker()
        return {"message": "Genetic agent reset successfully"}
    else:
        return {"error": f"Unknown or unavailable agent: {agent_type}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)