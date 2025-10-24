"""
ConPort-KG API Routes
Phase 1 Week 1 Day 4

FastAPI routes for authentication, authorization, and knowledge graph queries.
"""

from .auth_routes import router as auth_router

__all__ = ["auth_router"]
