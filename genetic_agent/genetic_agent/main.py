"""Main application entry point for the Genetic Coding Agent system."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import AgentConfig
from .vanilla.vanilla_agent import VanillaAgent

# Create FastAPI app
app = FastAPI(
    title="Genetic Coding Agent",
    description="Dual-agent system for automated code repair",
    version="0.1.0"
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


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    global vanilla_agent

    config = AgentConfig()
    vanilla_agent = VanillaAgent(config)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Genetic Coding Agent API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": {
            "vanilla": vanilla_agent is not None,
            "genetic": False  # TODO: Add genetic agent
        }
    }


@app.post("/repair/vanilla")
async def repair_with_vanilla(task: dict):
    """Repair code using the vanilla agent."""
    if not vanilla_agent:
        return {"error": "Vanilla agent not initialized"}

    result = await vanilla_agent.process_task(task)
    return result


@app.get("/status")
async def get_status():
    """Get system status."""
    if vanilla_agent:
        agent_status = vanilla_agent.get_status()
    else:
        agent_status = {"error": "Agent not initialized"}

    return {
        "system": "healthy",
        "vanilla_agent": agent_status
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)