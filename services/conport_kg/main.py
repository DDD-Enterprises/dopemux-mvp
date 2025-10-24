#!/usr/bin/env python3
"""
ConPort-KG 2.0 API Server
Phase 1 Week 1 Day 4

FastAPI application with authentication and knowledge graph APIs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.auth_routes import router as auth_router
from auth.database import check_database_connection, init_database

# ============================================================================
# Application Initialization
# ============================================================================

app = FastAPI(
    title="ConPort-KG 2.0 API",
    description="Multi-tenant knowledge graph with multi-agent memory hub",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# CORS Configuration
# ============================================================================

# Allow all origins in development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Include Routers
# ============================================================================

app.include_router(auth_router)

# ============================================================================
# Startup/Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize database schema on startup"""
    print("🚀 Starting ConPort-KG 2.0 API Server...")

    # Check database connection
    if check_database_connection():
        print("✓ Database connected")
    else:
        print("⚠️  Database connection failed")

    # Initialize schema (idempotent)
    try:
        init_database()
        print("✓ Database schema initialized")
    except Exception as e:
        print(f"⚠️  Schema initialization failed: {e}")

    print("✓ ConPort-KG 2.0 API Server ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down ConPort-KG 2.0 API Server...")


# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "ConPort-KG 2.0",
        "description": "Multi-tenant knowledge graph with multi-agent memory hub",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "authentication": "/auth",
    }


@app.get("/health")
async def health():
    """Overall health check"""
    db_healthy = check_database_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "components": {
            "api": "operational",
            "database": "connected" if db_healthy else "disconnected",
            "authentication": "operational",
        },
        "version": "2.0.0",
    }


# ============================================================================
# Run Server (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info",
    )
