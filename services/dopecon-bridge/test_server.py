#!/usr/bin/env python3
"""
Minimal test server for Component 5 orchestrator endpoints
Runs standalone without database/Redis dependencies for quick testing
"""

from fastapi import FastAPI
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(
    title="MCP DopeconBridge - Test Server (Component 5)",
    version="1.0.0-test",
    description="Standalone test server for orchestrator query endpoints"
)

# Import and register orchestrator endpoints
try:
    from orchestrator_endpoints import router as orchestrator_router
    app.include_router(orchestrator_router)
    logger.info("✅ Task-Orchestrator query endpoints registered at /orchestrator/*")
except ImportError as e:
    logger.error(f"❌ Failed to import orchestrator endpoints: {e}")
    raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "test",
        "endpoints": "orchestrator query endpoints only"
    }

if __name__ == "__main__":
    logger.info("🧪 Starting Component 5 test server on port 3016...")
    logger.info("📋 Available endpoints: /orchestrator/tasks, /orchestrator/adhd-state, etc.")
    logger.info("🔍 Health check: http://localhost:3016/health")
    logger.info("📖 API docs: http://localhost:3016/docs")

    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=3016,
        reload=False,
        log_level="info"
    )
